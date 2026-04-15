"""
输出整合节点
整合HTML、PDF和页面内容，输出最终结果
提供完整的文件管理和可视化展示功能
"""
import os
import shutil
import logging
import re
from datetime import datetime
from typing import List, Dict
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk.s3 import S3SyncStorage

from graphs.state import OutputIntegrationInput, OutputIntegrationOutput, FileAsset


def generate_safe_filename(theme: str, timestamp: str, ext: str) -> str:
    """生成安全的文件名，包含主题摘要和时间戳"""
    # 提取主题的前20个字符作为摘要
    theme_summary = re.sub(r'[^\w\s-]', '', theme)[:20].strip().replace(' ', '_')
    if not theme_summary:
        theme_summary = "storybook"
    return f"{theme_summary}_{timestamp}.{ext}"


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小显示"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def output_integration_node(
    state: OutputIntegrationInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> OutputIntegrationOutput:
    """
    title: 输出整合与文件管理
    desc: 整合所有输出内容，保存文件到assets目录，上传到对象存储生成可访问URL，并提供缩略图
    integrations: 对象存储
    """
    ctx = runtime.context
    logger = logging.getLogger(__name__)
    
    # 初始化对象存储
    storage = S3SyncStorage(
        endpoint_url=os.getenv("COZE_BUCKET_ENDPOINT_URL"),
        access_key="",
        secret_key="",
        bucket_name=os.getenv("COZE_BUCKET_NAME"),
        region="cn-beijing",
    )
    
    # 生成时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # ===== 1. 保存文件到本地 assets 目录 =====
    assets_dir = os.path.join(os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects"), "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    assets: List[FileAsset] = []
    
    # 1.1 保存 HTML 文件
    html_filename = generate_safe_filename(state.theme, timestamp, "html")
    html_local_path = os.path.join(assets_dir, html_filename)
    
    with open(html_local_path, 'w', encoding='utf-8') as f:
        f.write(state.html_content)
    
    html_size = os.path.getsize(html_local_path)
    logger.info(f"✅ HTML 已保存到本地: {html_local_path} ({format_file_size(html_size)})")
    
    # 1.2 复制 PDF 文件（如果存在）
    pdf_local_path = ""
    pdf_filename = ""
    pdf_size = 0
    
    if state.pdf_file and os.path.exists(state.pdf_file.url):
        pdf_filename = generate_safe_filename(state.theme, timestamp, "pdf")
        pdf_local_path = os.path.join(assets_dir, pdf_filename)
        shutil.copy(state.pdf_file.url, pdf_local_path)
        pdf_size = os.path.getsize(pdf_local_path)
        logger.info(f"✅ PDF 已保存到本地: {pdf_local_path} ({format_file_size(pdf_size)})")
    
    # ===== 2. 上传到对象存储并生成可访问 URL =====
    
    # 2.1 上传 HTML
    try:
        with open(html_local_path, 'rb') as f:
            html_key = storage.stream_upload_file(
                fileobj=f,
                file_name=f"storybooks/html/{html_filename}",
                content_type="text/html",
            )
        html_url = storage.generate_presigned_url(key=html_key, expire_time=2592000)  # 30天有效期
        
        assets.append(FileAsset(
            file_name=html_filename,
            local_path=html_local_path,
            storage_key=html_key,
            url=html_url,
            file_type="html",
            size_bytes=html_size,
            created_at=timestamp
        ))
        logger.info(f"✅ HTML 已上传到对象存储: {html_key}")
    except Exception as e:
        logger.error(f"❌ HTML 上传失败: {e}")
        html_url = ""
        html_key = ""
    
    # 2.2 上传 PDF（如果存在）
    pdf_url = ""
    pdf_key = ""
    if pdf_local_path:
        try:
            with open(pdf_local_path, 'rb') as f:
                pdf_key = storage.stream_upload_file(
                    fileobj=f,
                    file_name=f"storybooks/pdf/{pdf_filename}",
                    content_type="application/pdf",
                )
            pdf_url = storage.generate_presigned_url(key=pdf_key, expire_time=2592000)
            
            assets.append(FileAsset(
                file_name=pdf_filename,
                local_path=pdf_local_path,
                storage_key=pdf_key,
                url=pdf_url,
                file_type="pdf",
                size_bytes=pdf_size,
                created_at=timestamp
            ))
            logger.info(f"✅ PDF 已上传到对象存储: {pdf_key}")
        except Exception as e:
            logger.error(f"❌ PDF 上传失败: {e}")
    
    # ===== 3. 生成缩略图（使用第一页插画）=====
    thumbnail_url = ""
    if state.illustrations and len(state.illustrations) > 0:
        # 使用第一页插画作为缩略图
        thumbnail_url = state.illustrations[0]
        logger.info(f"✅ 缩略图已设置: {thumbnail_url}")
    
    # ===== 4. 输出日志摘要 =====
    logger.info("=" * 70)
    logger.info("📚 电子书生成完成")
    logger.info(f"   标题: {state.theme}")
    logger.info(f"   画风: {state.style}")
    logger.info(f"   总页数: {len(state.pages)}")
    logger.info("-" * 70)
    logger.info("📁 生成的文件:")
    for asset in assets:
        logger.info(f"   • {asset.file_name} ({format_file_size(asset.size_bytes)})")
        logger.info(f"     本地路径: {asset.local_path}")
        logger.info(f"     访问链接: {asset.url[:80]}...")
    logger.info("=" * 70)
    
    # ===== 5. 构建最终结果 =====
    ebook_result = {
        "title": state.theme,
        "total_pages": len(state.pages),
        "style": state.style,
        "html_content": state.html_content,
        "html_url": html_url,
        "pdf_url": pdf_url,
        "thumbnail_url": thumbnail_url,
        "pages_summary": [
            {
                "page_number": i + 1,
                "text": page.get("text", ""),
                "key_words": page.get("key_words", []),
                "interaction_type": page.get("interaction", {}).get("type", "")
            }
            for i, page in enumerate(state.pages)
        ],
        "generated_at": timestamp,
        "file_assets": [
            {
                "file_name": asset.file_name,
                "file_type": asset.file_type,
                "size": format_file_size(asset.size_bytes),
                "url": asset.url
            }
            for asset in assets
        ]
    }
    
    return OutputIntegrationOutput(
        ebook_result=ebook_result,
        assets=assets,
        thumbnail_url=thumbnail_url
    )
