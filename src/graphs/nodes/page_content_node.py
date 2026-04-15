"""
页面内容生成节点
调用循环子图生成所有页面的内容
"""
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import PageContentInput, PageContentOutput
from graphs.loop_graph import page_content_loop_graph


def page_content_node(
    state: PageContentInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> PageContentOutput:
    """
    title: 页面内容生成
    desc: 循环调用子图生成每页的英文文本、画面描述和互动元素
    integrations: 豆包大语言模型
    """
    ctx = runtime.context
    
    # 提取必要信息
    analysis_result = state.analysis_result
    story_structure = analysis_result.get("story_structure", {})
    character_name = story_structure.get("character_name", "Little Hero")
    character_traits = story_structure.get("character_traits", ["brave", "kind"])
    
    story_outline = state.story_outline
    pages_outline = story_outline.get("pages", [])
    
    # 构建子图输入
    loop_input = {
        "theme": state.theme,
        "age_group": state.age_group,
        "style": state.style,
        "page_count": state.page_count,
        "character_name": character_name,
        "character_traits": character_traits,
        "pages_outline": pages_outline,
        "pages": [],
        "current_index": 0
    }
    
    # 调用循环子图
    result = page_content_loop_graph.invoke(loop_input)
    
    return PageContentOutput(pages=result.get("pages", []))
