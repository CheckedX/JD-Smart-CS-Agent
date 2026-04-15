## 项目概述
- **名称**: AI英文童书生成工作流
- **功能**: 根据主题自动生成带互动元素的英文童书，支持HTML和PDF双格式输出，并提供完整的文件管理和可视化展示功能

### 节点清单
| 节点名 | 文件位置 | 类型 | 功能描述 | 分支逻辑 | 配置文件 |
|-------|---------|------|---------|---------|---------|
| theme_analysis | `nodes/theme_analysis_node.py` | agent | 分析故事主题的教育目标、词汇水平、故事结构 | - | `config/theme_analysis_llm_cfg.json` |
| story_outline | `nodes/story_outline_node.py` | agent | 生成完整的故事大纲 | - | `config/story_outline_llm_cfg.json` |
| page_content | `nodes/page_content_node.py` | looparray | 循环生成每页的英文文本、画面描述和互动元素 | - | - |
| character_image | `nodes/character_image_node.py` | task | 生成主角的角色参考图 | - | - |
| illustration | `nodes/illustration_node.py` | looparray | 循环生成每页插画 | - | - |
| html_generation | `nodes/html_generation_node.py` | task | 生成交互式HTML电子书 | - | - |
| pdf_generation | `nodes/pdf_generation_node.py` | task | 生成PDF格式电子书 | - | - |
| output_integration | `nodes/output_integration_node.py` | task | 整合输出、文件管理、上传对象存储、生成可访问URL | - | - |

**类型说明**: task(普通任务节点) / agent(大模型) / condition(条件分支) / looparray(列表循环) / loopcond(条件循环)

## 子图清单
| 子图名 | 文件位置 | 功能描述 | 被调用节点 |
|-------|---------|------|---------|-----------|
| page_content_loop_graph | `graphs/loop_graph.py` | 循环生成每页内容 | page_content |
| illustration_loop_graph | `graphs/loop_graph.py` | 循环生成每页插画 | illustration |

## 技能使用
- **主题分析节点(theme_analysis)** 使用 **豆包大语言模型** (doubao-seed-2-0-pro-260215)
- **故事大纲节点(story_outline)** 使用 **豆包大语言模型** (doubao-seed-2-0-pro-260215)
- **角色图生成节点(character_image)** 使用 **图像生成** (ImageGenerationClient)
- **插画生成节点(illustration)** 使用 **图像生成** (ImageGenerationClient)
- **输出整合节点(output_integration)** 使用 **对象存储** (S3SyncStorage)

## 模型配置
| 配置文件 | 模型 | 用途 |
|---------|------|------|
| config/theme_analysis_llm_cfg.json | doubao-seed-2-0-pro-260215 | 主题分析 |
| config/story_outline_llm_cfg.json | doubao-seed-2-0-pro-260215 | 故事大纲生成 |
| config/page_content_llm_cfg.json | doubao-seed-2-0-pro-260215 | 页面内容生成 |

## 工作流结构

```
输入参数
   ↓
[theme_analysis] 主题分析 (Agent - 豆包LLM)
   ↓
[story_outline] 故事大纲 (Agent - 豆包LLM)
   ↓ (并行分支)
   ├─→ [page_content] 页面内容生成 (Loop)
   └─→ [character_image] 角色参考图 (Image)
   ↓ (汇聚)
[illustration] 页面插画生成 (Loop)
   ↓ (并行分支)
   ├─→ [html_generation] HTML生成
   └─→ [pdf_generation] PDF生成
   ↓ (汇聚)
[output_integration] 输出整合 (文件管理+对象存储)
   ↓
最终结果
```

## 文件管理功能

### 1. 文件保存策略
- **本地保存**: 所有文件自动保存到 `assets/` 目录
- **命名规范**: `{主题摘要}_{时间戳}.{扩展名}`
  - 示例: `A_brave_little_rabbi_20260407_195836.html`
- **文件类型**: HTML、PDF、缩略图

### 2. 对象存储上传
- **自动上传**: 文件自动生成后上传到对象存储
- **目录结构**: 
  - `storybooks/html/` - HTML电子书
  - `storybooks/pdf/` - PDF电子书
- **URL有效期**: 30天（可配置）

### 3. 可视化展示
- **HTML预览**: 通过生成的URL直接浏览器访问
- **PDF预览**: 对象存储URL支持浏览器直接打开
- **缩略图**: 使用第一页插画作为电子书缩略图

## 输入参数
| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|--------|------|------|------|--------|
| theme | String | 是 | 故事主题 | "A shy turtle learns to make friends" |
| age_group | String | 是 | 目标年龄段 | "5-6" / "7-9" / "10-12" |
| style | String | 是 | 画风选择 | "watercolor" / "cartoon" / "3d" |
| education_tags | Array | 否 | 教育标签 | ["friendship", "courage"] |
| interactions | Array | 否 | 互动类型 | ["click", "drag", "quiz"] |
| page_count | Number | 否 | 页数（默认8）| 8 |

## 输出结果
| 字段 | 类型 | 说明 |
|------|------|------|
| ebook_result.title | String | 故事标题 |
| ebook_result.total_pages | Number | 总页数 |
| ebook_result.style | String | 画风 |
| ebook_result.html_content | String | HTML源代码 |
| ebook_result.html_url | String | HTML可访问URL |
| ebook_result.pdf_url | String | PDF可访问URL |
| ebook_result.thumbnail_url | String | 缩略图URL |
| ebook_result.generated_at | String | 生成时间戳 |
| ebook_result.file_assets | Array | 文件资产列表 |
| assets | Array | 完整的文件资产信息 |
| thumbnail_url | String | 缩略图URL |

### 文件资产结构 (FileAsset)
```json
{
  "file_name": "A_brave_little_rabbi_20260407_195836.html",
  "local_path": "/workspace/projects/assets/A_brave_little_rabbi_20260407_195836.html",
  "storage_key": "storybooks/html/A_brave_little_rabbi_20260407_195836_5e62d2d0.html",
  "url": "https://...",
  "file_type": "html",
  "size_bytes": 7405,
  "created_at": "20260407_195836"
}
```

## 技术栈
- **AI模型**: 豆包大语言模型 (doubao-seed-2-0-pro-260215)
- **图像生成**: ImageGenerationClient (国内可用，无需翻墙)
- **PDF生成**: ReportLab
- **对象存储**: S3SyncStorage (Coze平台内置)
- **工作流框架**: LangGraph

## 使用示例

### 开发者查看文件
```bash
# 查看本地生成的文件
ls -la /workspace/projects/assets/

# HTML文件可以直接在浏览器打开
open /workspace/projects/assets/A_brave_little_rabbi_*.html
```

### 访问在线文件
从输出结果中获取 `html_url` 或 `pdf_url`，直接在浏览器中访问即可预览。
