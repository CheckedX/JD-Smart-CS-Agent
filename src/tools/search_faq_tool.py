"""
知识库搜索工具
用于从FAQ知识库中检索相关信息，支持订单查询、退款、物流等场景
"""

from langchain.tools import tool
from coze_coding_dev_sdk import KnowledgeClient, Config
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context

@tool
def search_faq(query: str) -> str:
    """
    从FAQ知识库中搜索相关的客服信息

    该工具用于检索订单查询、退款流程、物流追踪、支付问题等客服相关的FAQ信息。

    Args:
        query (str): 用户的问题或关键词，如"如何退款"、"订单在哪里"、"物流进度查询"等

    Returns:
        str: 从知识库中检索到的相关FAQ内容，按相关度排序返回

    Example:
        >>> search_faq("如何申请退款")
        "关于退款流程的详细说明：1. 进入订单详情页...2. 点击退款按钮...3. 选择退款原因..."
    """
    ctx = request_context.get() or new_context(method="search_faq")

    try:
        # 初始化知识库客户端
        config = Config()
        client = KnowledgeClient(config=config, ctx=ctx)

        # 执行语义搜索
        response = client.search(
            query=query,
            top_k=5,  # 返回最相关的5条结果
            min_score=0.5  # 相似度阈值
        )

        if response.code != 0 or not response.chunks:
            return "抱歉，未在知识库中找到相关信息。"

        # 格式化搜索结果
        results = []
        for idx, chunk in enumerate(response.chunks, 1):
            results.append(f"[知识库参考 {idx}] (相关度: {chunk.score:.2f})\n{chunk.content}")

        return "\n\n".join(results)

    except Exception as e:
        return f"知识库检索失败: {str(e)}"
