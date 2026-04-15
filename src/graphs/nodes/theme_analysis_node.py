"""
主题分析节点
分析故事主题的教育价值、语言难度和结构要素
"""
import os
import json
from jinja2 import Template
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient
from langchain_core.messages import SystemMessage, HumanMessage

from graphs.state import ThemeAnalysisInput, ThemeAnalysisOutput


def theme_analysis_node(
    state: ThemeAnalysisInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> ThemeAnalysisOutput:
    """
    title: 主题分析
    desc: 分析故事主题的教育目标、词汇水平、句式复杂度和故事结构
    integrations: 豆包大语言模型
    """
    ctx = runtime.context
    
    # 读取LLM配置
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH", ""), 
                           config.get('metadata', {}).get('llm_cfg', 'config/theme_analysis_llm_cfg.json'))
    with open(cfg_file, 'r', encoding='utf-8') as fd:
        _cfg = json.load(fd)
    
    llm_config = _cfg.get("config", {})
    sp = _cfg.get("sp", "")
    up = _cfg.get("up", "")
    
    # 使用jinja2渲染用户提示词
    up_tpl = Template(up)
    user_prompt = up_tpl.render({
        "theme": state.theme,
        "age_group": state.age_group,
        "education_tags": state.education_tags
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
        temperature=llm_config.get("temperature", 0.7),
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
        analysis_result = json.loads(content)
    except json.JSONDecodeError as e:
        # 如果解析失败，返回一个默认结构
        analysis_result = {
            "education_goals": ["social skills", "emotional intelligence"],
            "key_vocabulary": ["friend", "happy", "share"],
            "vocabulary_level": "CEFR Pre-A1",
            "sentence_complexity": "Simple sentences with repetition",
            "story_structure": {
                "character_name": "Little Hero",
                "character_traits": ["brave", "kind"],
                "conflict": "A challenge to overcome",
                "resolution": "Success through friendship"
            }
        }
    
    # 提取主角信息
    story_structure = analysis_result.get("story_structure", {})
    character_name = story_structure.get("character_name", "Little Hero")
    character_traits = story_structure.get("character_traits", ["brave", "kind"])
    
    return ThemeAnalysisOutput(
        analysis_result=analysis_result,
        character_name=character_name,
        character_traits=character_traits
    )
