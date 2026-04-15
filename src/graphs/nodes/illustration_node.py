"""
页面插画生成节点
调用循环子图为每页生成插画
"""
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import IllustrationInput, IllustrationOutput
from graphs.loop_graph import illustration_loop_graph


def illustration_node(
    state: IllustrationInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> IllustrationOutput:
    """
    title: 页面插画生成
    desc: 循环调用子图为每页生成插画，使用角色参考图保持一致性
    integrations: 图像生成
    """
    ctx = runtime.context
    
    # 构建子图输入
    loop_input = {
        "pages": state.pages,
        "character_image_url": state.character_image_url,
        "style": state.style,
        "illustrations": [],
        "current_index": 0
    }
    
    # 调用循环子图
    result = illustration_loop_graph.invoke(loop_input)
    
    return IllustrationOutput(illustrations=result.get("illustrations", []))
