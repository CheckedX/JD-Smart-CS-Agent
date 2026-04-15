"""
HTML电子书生成节点
生成交互式HTML电子书
"""
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import HTMLGenerationInput, HTMLGenerationOutput


def html_generation_node(
    state: HTMLGenerationInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> HTMLGenerationOutput:
    """
    title: HTML电子书生成
    desc: 生成交互式HTML电子书，包含翻页动画和互动元素
    integrations: 
    """
    ctx = runtime.context
    
    # 构建页面HTML
    pages_html = []
    page_dots_html = []
    
    # 确保插画数量与页面数量一致，不足的用占位符填充
    illustrations = state.illustrations[:]
    while len(illustrations) < len(state.pages):
        illustrations.append("")  # 空字符串作为占位符
    
    for i, page in enumerate(state.pages):
        illustration_url = illustrations[i] if i < len(illustrations) else ""
        interaction = page.get("interaction", {})
        interaction_type = interaction.get("type", "")
        interaction_action = interaction.get("action", "")
        interaction_hint = interaction.get("hint", "")
        
        # 构建互动元素HTML
        interaction_html = ""
        if interaction_type == "click":
            interaction_html = f'''
            <div class="interaction click-interaction" onclick="{interaction_action}">
                <span class="hint">{interaction_hint}</span>
            </div>
            '''
        elif interaction_type == "quiz":
            interaction_html = f'''
            <div class="interaction quiz-interaction">
                <p class="quiz-question">{interaction_action}</p>
                <span class="hint">{interaction_hint}</span>
            </div>
            '''
        elif interaction_type == "drag":
            interaction_html = f'''
            <div class="interaction drag-interaction">
                <span class="hint">{interaction_hint}</span>
            </div>
            '''
        
        display_style = "block" if i == 0 else "none"
        page_html = f'''
        <div class="page" id="page-{i+1}" style="display: {display_style};">
            <div class="page-content">
                <img src="{illustration_url}" alt="Page {i+1} illustration" class="illustration">
                <div class="text-content">
                    <p class="story-text">{page.get('text', '')}</p>
                    <div class="key-words">
                        <strong>Key Words:</strong> {', '.join(page.get('key_words', []))}
                    </div>
                    {interaction_html}
                </div>
            </div>
            <div class="page-number">{i+1} / {len(state.pages)}</div>
        </div>
        '''
        pages_html.append(page_html)
        
        # 构建页码点
        active_class = "active" if i == 0 else ""
        dot_html = f'<div class="dot {active_class}" onclick="goToPage({i+1})"></div>'
        page_dots_html.append(dot_html)
    
    # 构建完整HTML
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{state.theme}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Georgia', serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}
        
        .book-container {{
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 900px;
            width: 100%;
            overflow: hidden;
        }}
        
        .book-header {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .book-header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .book-header .character {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .book-content {{
            padding: 40px;
            min-height: 600px;
        }}
        
        .page {{
            animation: fadeIn 0.5s ease-in;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .illustration {{
            width: 100%;
            max-height: 400px;
            object-fit: contain;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .text-content {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 15px;
        }}
        
        .story-text {{
            font-size: 1.4em;
            line-height: 1.8;
            color: #333;
            margin-bottom: 20px;
        }}
        
        .key-words {{
            background: #e3f2fd;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            color: #1976d2;
        }}
        
        .interaction {{
            background: #fff3e0;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #ff9800;
        }}
        
        .hint {{
            color: #e65100;
            font-style: italic;
        }}
        
        .quiz-question {{
            color: #333;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .page-number {{
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 0.9em;
        }}
        
        .navigation {{
            display: flex;
            justify-content: space-between;
            padding: 20px 40px;
            background: #f5f5f5;
        }}
        
        .nav-btn {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 30px;
            font-size: 1em;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .nav-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }}
        
        .nav-btn:disabled {{
            background: #ccc;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }}
        
        .page-indicator {{
            display: flex;
            justify-content: center;
            gap: 8px;
            padding: 20px;
        }}
        
        .dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #ddd;
            cursor: pointer;
            transition: background 0.3s;
        }}
        
        .dot.active {{
            background: #667eea;
        }}
    </style>
</head>
<body>
    <div class="book-container">
        <div class="book-header">
            <h1>{state.theme}</h1>
            <div class="character">A story about {state.character_name}</div>
        </div>
        
        <div class="book-content">
            {''.join(pages_html)}
        </div>
        
        <div class="page-indicator">
            {''.join(page_dots_html)}
        </div>
        
        <div class="navigation">
            <button class="nav-btn" id="prev-btn" onclick="prevPage()" disabled>Previous</button>
            <button class="nav-btn" id="next-btn" onclick="nextPage()">Next</button>
        </div>
    </div>
    
    <script>
        let currentPage = 1;
        const totalPages = {len(state.pages)};
        
        function showPage(pageNum) {{
            // Hide all pages
            for (let i = 1; i <= totalPages; i++) {{
                document.getElementById('page-' + i).style.display = 'none';
            }}
            // Show current page
            document.getElementById('page-' + pageNum).style.display = 'block';
            
            // Update buttons
            document.getElementById('prev-btn').disabled = (pageNum === 1);
            document.getElementById('next-btn').disabled = (pageNum === totalPages);
            
            // Update dots
            const dots = document.querySelectorAll('.dot');
            dots.forEach((dot, index) => {{
                dot.classList.toggle('active', index === pageNum - 1);
            }});
            
            currentPage = pageNum;
        }}
        
        function nextPage() {{
            if (currentPage < totalPages) {{
                showPage(currentPage + 1);
            }}
        }}
        
        function prevPage() {{
            if (currentPage > 1) {{
                showPage(currentPage - 1);
            }}
        }}
        
        function goToPage(pageNum) {{
            showPage(pageNum);
        }}
    </script>
</body>
</html>'''
    
    return HTMLGenerationOutput(html_content=html_content)
