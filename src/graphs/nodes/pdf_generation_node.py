"""
PDF电子书生成节点
生成PDF格式的电子书
"""
import os
import tempfile
import requests
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import PDFGenerationInput, PDFGenerationOutput
from utils.file.file import File


def pdf_generation_node(
    state: PDFGenerationInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> PDFGenerationOutput:
    """
    title: PDF电子书生成
    desc: 生成PDF格式的电子书，包含所有页面和插画
    integrations: 
    """
    ctx = runtime.context
    
    # 创建临时PDF文件
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, "storybook.pdf")
    
    # 创建PDF文档
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    # 准备样式
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='#333333',
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    text_style = ParagraphStyle(
        'StoryText',
        parent=styles['BodyText'],
        fontSize=14,
        leading=20,
        spaceAfter=20,
        alignment=TA_LEFT
    )
    
    keywords_style = ParagraphStyle(
        'Keywords',
        parent=styles['BodyText'],
        fontSize=12,
        textColor='#1976d2',
        spaceAfter=15,
        alignment=TA_LEFT
    )
    
    # 构建PDF内容
    story = []
    
    # 封面
    story.append(Paragraph(state.theme, title_style))
    story.append(Paragraph(f"A story about {state.character_name}", styles['Heading2']))
    story.append(Spacer(1, 0.5*inch))
    
    for i, (page, illustration_url) in enumerate(zip(state.pages, state.illustrations)):
        # 添加页面内容
        story.append(Paragraph(f"Page {i+1}", styles['Heading3']))
        
        # 尝试添加插画
        if illustration_url:
            try:
                response = requests.get(illustration_url, timeout=30)
                if response.status_code == 200:
                    img = Image(BytesIO(response.content))
                    img.drawHeight = 3*inch
                    img.drawWidth = 4*inch
                    img.hAlign = 'CENTER'
                    story.append(img)
                    story.append(Spacer(1, 0.2*inch))
            except Exception as e:
                # 如果图片加载失败，跳过
                pass
        
        # 添加文本
        story.append(Paragraph(page.get('text', ''), text_style))
        
        # 添加关键词
        key_words = page.get('key_words', [])
        if key_words:
            story.append(Paragraph(f"<b>Key Words:</b> {', '.join(key_words)}", keywords_style))
        
        # 添加互动提示
        interaction = page.get('interaction', {})
        if interaction:
            hint = interaction.get('hint', '')
            if hint:
                story.append(Paragraph(f"<i>💡 {hint}</i>", styles['Italic']))
        
        # 添加分页（最后一页除外）
        if i < len(state.pages) - 1:
            story.append(PageBreak())
    
    # 生成PDF
    doc.build(story)
    
    # 创建File对象
    pdf_file = File(
        url=f"file://{pdf_path}",
        file_type="document"
    )
    
    return PDFGenerationOutput(pdf_file=pdf_file)
