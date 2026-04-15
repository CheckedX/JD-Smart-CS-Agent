"""
角色参考图生成节点
生成主角的参考图，确保整本书角色一致性
"""
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import ImageGenerationClient

from graphs.state import CharacterImageInput, CharacterImageOutput


def character_image_node(
    state: CharacterImageInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> CharacterImageOutput:
    """
    title: 角色参考图生成
    desc: 生成主角的角色参考图，用于保持整本书中角色形象的一致性
    integrations: 图像生成
    """
    ctx = runtime.context
    
    # 根据画风选择描述词
    style_descriptions = {
        "watercolor": "watercolor painting style, soft colors, gentle brushstrokes",
        "cartoon": "cartoon style, bold outlines, vibrant colors, Pixar-like",
        "3d": "3D rendered style, cute and rounded, soft lighting"
    }
    
    style_desc = style_descriptions.get(state.style, "cartoon style")
    
    # 构建提示词
    character_traits_str = ", ".join(state.character_traits) if state.character_traits else "friendly and cute"
    
    prompt = (
        f"Character design sheet for a children's book. "
        f"{state.character_name}, a cute {character_traits_str} character, "
        f"multiple poses and expressions (happy, sad, surprised, thinking), "
        f"front view, side view, 3/4 view, "
        f"{style_desc}, "
        f"simple background, white background, "
        f"children's book illustration style, "
        f"age-appropriate for {state.age_group} years old"
    )
    
    # 初始化图像生成客户端
    client = ImageGenerationClient(ctx=ctx)
    
    # 生成图像
    response = client.generate(
        prompt=prompt,
        size="2K",
        watermark=False
    )
    
    # 获取生成的图像URL
    character_image_url = ""
    if response.success and response.image_urls:
        character_image_url = response.image_urls[0]
    
    return CharacterImageOutput(character_image_url=character_image_url)
