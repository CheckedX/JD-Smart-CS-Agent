"""
故事大纲节点
生成完整的故事大纲，包含每页的情节描述
"""
import os
import json
from jinja2 import Template
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient
from langchain_core.messages import SystemMessage, HumanMessage

from graphs.state import StoryOutlineInput, StoryOutlineOutput


def story_outline_node(
    state: StoryOutlineInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> StoryOutlineOutput:
    """
    title: 故事大纲生成
    desc: 根据主题分析结果生成完整的故事大纲，包含每页的情节和教育目标
    integrations: 豆包大语言模型
    """
    ctx = runtime.context
    
    # 读取LLM配置
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH", ""),
                           config.get('metadata', {}).get('llm_cfg', 'config/story_outline_llm_cfg.json'))
    with open(cfg_file, 'r', encoding='utf-8') as fd:
        _cfg = json.load(fd)
    
    llm_config = _cfg.get("config", {})
    sp = _cfg.get("sp", "")
    up = _cfg.get("up", "")
    
    # 提取故事结构信息
    story_structure = state.analysis_result.get("story_structure", {})
    character_name = story_structure.get("character_name", "Little Hero")
    character_traits = story_structure.get("character_traits", ["brave", "kind"])
    conflict = story_structure.get("conflict", "A challenge to overcome")
    resolution = story_structure.get("resolution", "Success through friendship")
    
    # 使用jinja2渲染用户提示词
    up_tpl = Template(up)
    user_prompt = up_tpl.render({
        "theme": state.theme,
        "page_count": state.page_count,
        "character_name": character_name,
        "character_traits": character_traits,
        "conflict": conflict,
        "resolution": resolution
    })
    
    # 初始化LLM客户端
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
        temperature=llm_config.get("temperature", 0.8),
        top_p=llm_config.get("top_p", 0.9),
        max_completion_tokens=llm_config.get("max_completion_tokens", 4096)
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
        story_outline = json.loads(content)
    except json.JSONDecodeError as e:
        # 如果解析失败，生成一个默认的大纲
        pages = []
        for i in range(1, state.page_count + 1):
            pages.append({
                "page_number": i,
                "plot": f"Page {i} of the story about {character_name}",
                "education_goal": "learning and growth"
            })
        story_outline = {"pages": pages}
    
    return StoryOutlineOutput(story_outline=story_outline)
