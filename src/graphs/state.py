"""
英文童书工作流状态定义
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from utils.file.file import File


# ==========================================
# 全局状态定义
# ==========================================

class GlobalState(BaseModel):
    """全局状态 - 工作流的完整状态"""
    # 输入参数
    theme: str = Field(..., description="故事主题")
    age_group: str = Field(..., description="目标年龄段 (5-6/7-9/10-12)")
    style: str = Field(..., description="画风选择 (watercolor/cartoon/3d)")
    education_tags: List[str] = Field(default=[], description="教育标签列表")
    interactions: List[str] = Field(default=[], description="互动类型列表")
    page_count: int = Field(default=8, description="页数，默认8页")
    
    # 中间状态
    analysis_result: Dict = Field(default={}, description="主题分析结果")
    story_outline: Dict = Field(default={}, description="故事大纲")
    character_image_url: str = Field(default="", description="角色参考图URL")
    pages: List[Dict] = Field(default=[], description="页面内容列表")
    illustrations: List[str] = Field(default=[], description="插画URL列表")
    
    # 输出
    html_content: str = Field(default="", description="HTML电子书内容")
    pdf_file: Optional[File] = Field(default=None, description="PDF文件")
    ebook_result: Dict = Field(default={}, description="最终电子书结果")


# ==========================================
# 图输入输出定义
# ==========================================

class GraphInput(BaseModel):
    """工作流输入参数"""
    theme: str = Field(..., description="故事主题，如'A shy turtle learns to make friends'")
    age_group: str = Field(..., description="目标年龄段 (5-6/7-9/10-12)")
    style: str = Field(..., description="画风选择 (watercolor/cartoon/3d)")
    education_tags: List[str] = Field(default=[], description="教育标签列表，如['friendship', 'courage']")
    interactions: List[str] = Field(default=[], description="互动类型列表，如['click', 'drag', 'quiz']")
    page_count: int = Field(default=8, description="页数，默认8页")


class GraphOutput(BaseModel):
    """工作流输出结果"""
    ebook_result: Dict = Field(..., description="最终电子书结果，包含HTML和PDF")
    pages: List[Dict] = Field(..., description="所有页面内容列表")


# ==========================================
# 节点输入输出定义
# ==========================================

# ----- 主题分析节点 -----
class ThemeAnalysisInput(BaseModel):
    """主题分析节点输入"""
    theme: str = Field(..., description="故事主题")
    age_group: str = Field(..., description="目标年龄段")
    education_tags: List[str] = Field(default=[], description="教育标签列表")


class ThemeAnalysisOutput(BaseModel):
    """主题分析节点输出"""
    analysis_result: Dict = Field(..., description="主题分析结果，包含教育目标、词汇、故事结构等")
    character_name: str = Field(..., description="主角名称")
    character_traits: List[str] = Field(default=[], description="主角性格特征")


# ----- 故事大纲节点 -----
class StoryOutlineInput(BaseModel):
    """故事大纲节点输入"""
    theme: str = Field(..., description="故事主题")
    page_count: int = Field(..., description="页数")
    analysis_result: Dict = Field(..., description="主题分析结果")


class StoryOutlineOutput(BaseModel):
    """故事大纲节点输出"""
    story_outline: Dict = Field(..., description="故事大纲，包含每页情节")


# ----- 页面内容生成节点 (循环节点) -----
class PageContentInput(BaseModel):
    """页面内容生成节点输入"""
    theme: str = Field(..., description="故事主题")
    age_group: str = Field(..., description="目标年龄段")
    style: str = Field(..., description="画风")
    page_count: int = Field(..., description="总页数")
    analysis_result: Dict = Field(..., description="主题分析结果")
    story_outline: Dict = Field(..., description="故事大纲")


class PageContentOutput(BaseModel):
    """页面内容生成节点输出"""
    pages: List[Dict] = Field(..., description="所有页面内容列表")


# 子图 - 单页内容生成
class SinglePageInput(BaseModel):
    """单页内容生成输入"""
    theme: str = Field(..., description="故事主题")
    age_group: str = Field(..., description="目标年龄段")
    style: str = Field(..., description="画风")
    character_name: str = Field(..., description="主角名称")
    character_traits: List[str] = Field(default=[], description="主角性格特征")
    page_number: int = Field(..., description="当前页码")
    page_plot: str = Field(..., description="本页情节")
    education_goal: str = Field(..., description="本页教育目标")


class SinglePageOutput(BaseModel):
    """单页内容生成输出"""
    page_content: Dict = Field(..., description="单页内容，包含text/visual_prompt/interaction等")


# ----- 角色参考图生成节点 -----
class CharacterImageInput(BaseModel):
    """角色参考图生成节点输入"""
    character_name: str = Field(..., description="主角名称，从主题分析结果中提取")
    character_traits: List[str] = Field(default=[], description="主角性格特征，从主题分析结果中提取")
    style: str = Field(..., description="画风")
    age_group: str = Field(..., description="目标年龄段")


class CharacterImageOutput(BaseModel):
    """角色参考图生成节点输出"""
    character_image_url: str = Field(..., description="角色参考图URL")


# ----- 页面插画生成节点 (循环节点) -----
class IllustrationInput(BaseModel):
    """页面插画生成节点输入"""
    pages: List[Dict] = Field(..., description="页面内容列表")
    character_image_url: str = Field(..., description="角色参考图URL")
    style: str = Field(..., description="画风")


class IllustrationOutput(BaseModel):
    """页面插画生成节点输出"""
    illustrations: List[str] = Field(..., description="插画URL列表")


# 子图 - 单页插画生成
class SingleIllustrationInput(BaseModel):
    """单页插画生成输入"""
    visual_prompt: str = Field(..., description="画面描述")
    character_image_url: str = Field(..., description="角色参考图URL")
    style: str = Field(..., description="画风")
    page_number: int = Field(..., description="页码")


class SingleIllustrationOutput(BaseModel):
    """单页插画生成输出"""
    illustration_url: str = Field(..., description="插画URL")


# ----- HTML生成节点 -----
class HTMLGenerationInput(BaseModel):
    """HTML生成节点输入"""
    theme: str = Field(..., description="故事主题")
    age_group: str = Field(..., description="目标年龄段")
    pages: List[Dict] = Field(..., description="页面内容列表")
    illustrations: List[str] = Field(..., description="插画URL列表")
    character_name: str = Field(..., description="主角名称")


class HTMLGenerationOutput(BaseModel):
    """HTML生成节点输出"""
    html_content: str = Field(..., description="HTML电子书内容")


# ----- PDF生成节点 -----
class PDFGenerationInput(BaseModel):
    """PDF生成节点输入"""
    theme: str = Field(..., description="故事主题")
    pages: List[Dict] = Field(..., description="页面内容列表")
    illustrations: List[str] = Field(..., description="插画URL列表")
    character_name: str = Field(..., description="主角名称")


class PDFGenerationOutput(BaseModel):
    """PDF生成节点输出"""
    pdf_file: File = Field(..., description="PDF文件对象")


# ----- 输出整合节点 -----
class OutputIntegrationInput(BaseModel):
    """输出整合节点输入"""
    html_content: str = Field(..., description="HTML电子书内容")
    pdf_file: Optional[File] = Field(default=None, description="PDF文件对象")
    pages: List[Dict] = Field(..., description="页面内容列表")
    theme: str = Field(..., description="故事主题")
    style: str = Field(..., description="画风")
    illustrations: List[str] = Field(default=[], description="插画URL列表")


class FileAsset(BaseModel):
    """文件资产信息"""
    file_name: str = Field(..., description="文件名")
    local_path: str = Field(..., description="本地文件路径")
    storage_key: str = Field(..., description="对象存储key")
    url: str = Field(..., description="可访问URL")
    file_type: str = Field(..., description="文件类型 (html/pdf/thumbnail)")
    size_bytes: int = Field(..., description="文件大小(字节)")
    created_at: str = Field(..., description="创建时间")


class OutputIntegrationOutput(BaseModel):
    """输出整合节点输出"""
    ebook_result: Dict = Field(..., description="最终电子书结果")
    assets: List[FileAsset] = Field(default=[], description="生成的文件资产列表")
    thumbnail_url: str = Field(default="", description="缩略图URL")
