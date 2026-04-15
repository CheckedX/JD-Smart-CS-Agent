"""
智能客服Agent
支持多轮对话、FAQ知识库检索、意图识别和风控机制
"""

import os
import json
from typing import Annotated
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain_openai import ChatOpenAI
from langchain.messages import ToolMessage
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from coze_coding_utils.runtime_ctx.context import default_headers
from storage.memory.memory_saver import get_memory_saver

# 导入自定义工具
from tools.search_faq_tool import search_faq
from tools.risk_control_tool import risk_control_check

LLM_CONFIG = "config/agent_llm_config.json"

# 默认保留最近 20 轮对话 (40 条消息)
MAX_MESSAGES = 40

def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]  # type: ignore

class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]

@wrap_tool_call
def handle_tool_errors(request, handler):
    """自定义工具错误处理"""
    try:
        return handler(request)
    except Exception as e:
        return ToolMessage(
            content=f"工具执行错误: ({str(e)})",
            tool_call_id=request.tool_call["id"]
        )

def build_agent(ctx=None):
    """
    构建智能客服Agent

    该Agent具备以下能力：
    1. 多轮对话记忆：支持上下文理解，记住用户历史对话
    2. FAQ知识库检索：从知识库中获取准确的客服信息
    3. 意图识别：自动识别用户意图（订单查询、退款、物流等）
    4. 风控机制：识别异常查询和恶意请求

    Returns:
        Agent: 配置好的智能客服Agent实例
    """
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    config_path = os.path.join(workspace_path, LLM_CONFIG)

    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")

    llm = ChatOpenAI(
        model=cfg['config'].get("model"),
        api_key=api_key,
        base_url=base_url,
        temperature=cfg['config'].get('temperature', 0.7),
        streaming=True,
        timeout=cfg['config'].get('timeout', 600),
        extra_body={
            "thinking": {
                "type": cfg['config'].get('thinking', 'disabled')
            }
        },
        default_headers=default_headers(ctx) if ctx else {}
    )

    # 注册工具
    tools = [risk_control_check, search_faq]

    # 创建Agent并启用错误处理和记忆功能
    agent = create_agent(
        model=llm,
        system_prompt=cfg.get("sp"),
        tools=tools,
        middleware=[handle_tool_errors],
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )

    return agent
