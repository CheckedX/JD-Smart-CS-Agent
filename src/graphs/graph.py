"""
英文童书工作流主图
根据主题自动生成带互动元素的英文童书
"""
from langgraph.graph import StateGraph, END

from graphs.state import (
    GlobalState,
    GraphInput,
    GraphOutput
)

from graphs.nodes.theme_analysis_node import theme_analysis_node
from graphs.nodes.story_outline_node import story_outline_node
from graphs.nodes.page_content_node import page_content_node
from graphs.nodes.character_image_node import character_image_node
from graphs.nodes.illustration_node import illustration_node
from graphs.nodes.html_generation_node import html_generation_node
from graphs.nodes.pdf_generation_node import pdf_generation_node
from graphs.nodes.output_integration_node import output_integration_node


# 创建工作流图
builder = StateGraph(GlobalState, input_schema=GraphInput, output_schema=GraphOutput)

# 添加业务节点
builder.add_node(
    "theme_analysis",
    theme_analysis_node,
    metadata={"type": "agent", "llm_cfg": "config/theme_analysis_llm_cfg.json"}
)
builder.add_node(
    "story_outline",
    story_outline_node,
    metadata={"type": "agent", "llm_cfg": "config/story_outline_llm_cfg.json"}
)
builder.add_node(
    "page_content",
    page_content_node,
    metadata={"type": "looparray"}
)
builder.add_node(
    "character_image",
    character_image_node,
    metadata={"type": "task"}
)
builder.add_node(
    "illustration",
    illustration_node,
    metadata={"type": "looparray"}
)
builder.add_node(
    "html_generation",
    html_generation_node,
    metadata={"type": "task"}
)
builder.add_node(
    "pdf_generation",
    pdf_generation_node,
    metadata={"type": "task"}
)
builder.add_node(
    "output_integration",
    output_integration_node,
    metadata={"type": "task"}
)

# 设置入口点
builder.set_entry_point("theme_analysis")

# 添加边 - 主题分析 → 故事大纲
builder.add_edge("theme_analysis", "story_outline")

# 添加边 - 故事大纲后并行分支：页面内容生成 和 角色图生成
builder.add_edge("story_outline", "page_content")
builder.add_edge("story_outline", "character_image")

# 两个并行分支汇聚到插画生成
builder.add_edge(["page_content", "character_image"], "illustration")

# 插画生成后并行分支：HTML生成 和 PDF生成
builder.add_edge("illustration", "html_generation")
builder.add_edge("illustration", "pdf_generation")

# 两个并行分支汇聚到输出整合
builder.add_edge(["html_generation", "pdf_generation"], "output_integration")

# 输出整合后结束
builder.add_edge("output_integration", END)

# 编译图
main_graph = builder.compile()
