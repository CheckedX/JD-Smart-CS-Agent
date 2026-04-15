"""
循环子图定义
包含页面内容生成循环和插画生成循环
"""
import os
import json
from typing import Dict, Any, List
from jinja2 import Template
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context, new_context
from coze_coding_dev_sdk import LLMClient, ImageGenerationClient


# ==========================================
# 循环子图状态定义
# ==========================================

class PageContentLoopState(BaseModel):
    """页面内容生成循环状态"""
    theme: str = Field(..., description="故事主题")
    age_group: str = Field(..., description="目标年龄段")
    style: str = Field(..., description="画风")
    page_count: int = Field(..., description="总页数")
    character_name: str = Field(..., description="主角名称")
    character_traits: List[str] = Field(default=[], description="主角性格特征")
    pages_outline: List[Dict] = Field(default=[], description="页面大纲列表")
    pages: List[Dict] = Field(default=[], description="生成的页面内容")
    current_index: int = Field(default=0, description="当前处理索引")


class IllustrationLoopState(BaseModel):
    """插画生成循环状态"""
    pages: List[Dict] = Field(..., description="页面内容列表")
    character_image_url: str = Field(..., description="角色参考图URL")
    style: str = Field(..., description="画风")
    illustrations: List[str] = Field(default=[], description="生成的插画URL列表")
    current_index: int = Field(default=0, description="当前处理索引")


# ==========================================
# 页面内容生成子图
# ==========================================

def generate_single_page(state: PageContentLoopState) -> PageContentLoopState:
    """生成单页内容"""
    # 读取LLM配置
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH", ""), 
                           "config/page_content_llm_cfg.json")
    with open(cfg_file, 'r', encoding='utf-8') as fd:
        _cfg = json.load(fd)
    
    llm_config = _cfg.get("config", {})
    sp = _cfg.get("sp", "")
    up = _cfg.get("up", "")
    
    # 获取当前页面大纲（如果没有则使用默认值）
    if state.current_index < len(state.pages_outline):
        page_outline = state.pages_outline[state.current_index]
    else:
        # 生成默认页面大纲
        page_outline = {
            "page_number": state.current_index + 1,
            "plot": f"Continue the story of {state.character_name} with a new adventure or discovery.",
            "education_goal": "learning and growth"
        }
    
    # 使用jinja2渲染用户提示词
    up_tpl = Template(up)
    user_prompt = up_tpl.render({
        "theme": state.theme,
        "character_name": state.character_name,
        "character_traits": state.character_traits,
        "age_group": state.age_group,
        "page_number": page_outline.get("page_number", state.current_index + 1),
        "page_plot": page_outline.get("plot", ""),
        "education_goal": page_outline.get("education_goal", ""),
        "style": state.style
    })
    
    # 初始化LLM客户端
    ctx = new_context(method="invoke")
    client = LLMClient(ctx=ctx)
    
    # 组装消息
    messages = [
        SystemMessage(content=sp),
        HumanMessage(content=user_prompt)
    ]
    
    # 调用大模型
    response = client.invoke(
        messages=messages,
        model=llm_config.get("model", "doubao-seed-2-0-pro-260215"),
        temperature=llm_config.get("temperature", 0.9),
        top_p=llm_config.get("top_p", 0.95),
        max_completion_tokens=llm_config.get("max_completion_tokens", 2048)
    )
    
    # 解析响应
    content = response.content
    if isinstance(content, list):
        if content and isinstance(content[0], str):
            content = " ".join(content)
        else:
            text_parts = [item.get("text", "") for item in content
                         if isinstance(item, dict) and item.get("type") == "text"]
            content = " ".join(text_parts)
    
    # 清理markdown代码块标记
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    
    # 解析JSON
    try:
        page_content = json.loads(content)
    except json.JSONDecodeError as e:
        # 如果解析失败，使用默认内容
        page_content = {
            "text": f"Page {state.current_index + 1} of the story about {state.character_name}.",
            "visual_prompt": f"Children's book illustration in {state.style} style, featuring {state.character_name}",
            "key_words": ["story", "fun"],
            "interaction": {
                "type": "click",
                "action": "alert('Great job!')",
                "hint": "Click to see what happens next!"
            }
        }
    
    # 添加页码信息
    page_content["page_number"] = state.current_index + 1
    
    # 添加到页面列表
    new_pages = list(state.pages)
    new_pages.append(page_content)
    
    return PageContentLoopState(
        theme=state.theme,
        age_group=state.age_group,
        style=state.style,
        page_count=state.page_count,
        character_name=state.character_name,
        character_traits=state.character_traits,
        pages_outline=state.pages_outline,
        pages=new_pages,
        current_index=state.current_index
    )


def should_continue_page_loop(state: PageContentLoopState) -> str:
    """判断是否继续页面生成循环"""
    # 使用 page_count 作为主要判断条件
    if state.current_index < state.page_count - 1:
        return "continue"
    return "end"


def increment_page_index(state: PageContentLoopState) -> PageContentLoopState:
    """递增页面索引"""
    return PageContentLoopState(
        theme=state.theme,
        age_group=state.age_group,
        style=state.style,
        page_count=state.page_count,
        character_name=state.character_name,
        character_traits=state.character_traits,
        pages_outline=state.pages_outline,
        pages=state.pages,
        current_index=state.current_index + 1
    )


# 构建页面内容生成子图
page_content_builder = StateGraph(PageContentLoopState, input_schema=PageContentLoopState, output_schema=PageContentLoopState)
page_content_builder.add_node("generate_single_page", generate_single_page)
page_content_builder.add_node("increment_index", increment_page_index)

page_content_builder.set_entry_point("generate_single_page")
page_content_builder.add_edge("generate_single_page", "increment_index")
page_content_builder.add_conditional_edges(
    "increment_index",
    should_continue_page_loop,
    {
        "continue": "generate_single_page",
        "end": END
    }
)

page_content_loop_graph = page_content_builder.compile()


# ==========================================
# 插画生成子图
# ==========================================

def generate_single_illustration(state: IllustrationLoopState) -> IllustrationLoopState:
    """生成单页插画"""
    if state.current_index >= len(state.pages):
        return state
    
    page = state.pages[state.current_index]
    visual_prompt = page.get("visual_prompt", "")
    
    # 根据画风选择描述词
    style_descriptions = {
        "watercolor": "watercolor painting style, soft colors, gentle brushstrokes",
        "cartoon": "cartoon style, bold outlines, vibrant colors, Pixar-like",
        "3d": "3D rendered style, cute and rounded, soft lighting"
    }
    
    style_desc = style_descriptions.get(state.style, "cartoon style")
    
    # 构建提示词
    prompt = (
        f"{visual_prompt}, "
        f"{style_desc}, "
        f"children's book illustration, "
        f"bright and cheerful colors, "
        f"simple composition, "
        f"high quality, detailed"
    )
    
    # 初始化图像生成客户端
    ctx = new_context(method="invoke")
    client = ImageGenerationClient(ctx=ctx)
    
    # 生成图像
    try:
        response = client.generate(
            prompt=prompt,
            size="2K",
            watermark=False
        )
        
        illustration_url = ""
        if response.success and response.image_urls:
            illustration_url = response.image_urls[0]
        else:
            # 如果生成失败，使用占位符
            illustration_url = ""
    except Exception as e:
        illustration_url = ""
    
    # 添加到插画列表
    new_illustrations = list(state.illustrations)
    new_illustrations.append(illustration_url)
    
    return IllustrationLoopState(
        pages=state.pages,
        character_image_url=state.character_image_url,
        style=state.style,
        illustrations=new_illustrations,
        current_index=state.current_index
    )


def should_continue_illustration_loop(state: IllustrationLoopState) -> str:
    """判断是否继续插画生成循环"""
    if state.current_index < len(state.pages) - 1:
        return "continue"
    return "end"


def increment_illustration_index(state: IllustrationLoopState) -> IllustrationLoopState:
    """递增插画索引"""
    return IllustrationLoopState(
        pages=state.pages,
        character_image_url=state.character_image_url,
        style=state.style,
        illustrations=state.illustrations,
        current_index=state.current_index + 1
    )


# 构建插画生成子图
illustration_builder = StateGraph(IllustrationLoopState, input_schema=IllustrationLoopState, output_schema=IllustrationLoopState)
illustration_builder.add_node("generate_single_illustration", generate_single_illustration)
illustration_builder.add_node("increment_index", increment_illustration_index)

illustration_builder.set_entry_point("generate_single_illustration")
illustration_builder.add_edge("generate_single_illustration", "increment_index")
illustration_builder.add_conditional_edges(
    "increment_index",
    should_continue_illustration_loop,
    {
        "continue": "generate_single_illustration",
        "end": END
    }
)

illustration_loop_graph = illustration_builder.compile()
