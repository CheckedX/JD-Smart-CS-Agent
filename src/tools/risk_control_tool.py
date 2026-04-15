"""
风控检查工具
用于识别异常查询和恶意请求，保护系统安全
"""

from langchain.tools import tool
from typing import List
import re
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context

# 定义风控规则关键词
RISK_KEYWORDS = [
    "破解", "刷单", "薅羊毛", "漏洞", "漏洞利用", "绕过", "欺诈",
    "诈骗", "盗取", "攻击", "注入", "SQL注入", "XSS", "CSRF",
    "恶意", "病毒", "木马", "钓鱼", "非法", "违法", "灰色",
    "黄赌毒", "赌博", "色情", "违禁品", "管制物品", "枪支", "弹药",
    "炸药", "毒品", "违禁药物", "处方药", "走私", "洗钱", "套现",
    "黑客", "黑客工具", "DDoS", "分布式攻击", "木马病毒", "勒索软件",
    "爬虫", "批量注册", "虚假订单", "恶意退款", "拒付", "恶意投诉"
]

# 敏感信息正则模式
SENSITIVE_PATTERNS = {
    'phone': r'1[3-9]\d{9}',
    'id_card': r'\d{17}[\dXx]',
    'bank_card': r'\d{16,19}',
    'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    'sql_injection': r"(union\s+select|drop\s+table|delete\s+from|update\s+.+set|'or\s+1=1|'or\s+1=1--)",
    'xss': r'<script|javascript:|onerror=|onload=|onclick=|eval\(|alert\(',
}

def _extract_sensitive_info(text: str) -> List[str]:
    """提取文本中的敏感信息（排除订单号模式）"""
    found = []
    for pattern_type, pattern in SENSITIVE_PATTERNS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # 排除订单号：16位数字且明显非银行卡号的输入（如仅包含该数字，无上下文）
            if pattern_type == 'bank_card' and len(matches) == 1:
                candidate = matches[0]
                # 简单判定：仅长度16且不含其他上下文，视为疑似订单号，不标记为敏感信息
                if re.fullmatch(r'\d{16}', candidate) and len(text.strip()) <= 50 and '订单' in text:
                    continue
            found.append(f"{pattern_type}: {len(matches)}处")
    return found

def _check_risk_keywords(text: str) -> tuple[bool, List[str]]:
    """检查是否包含风控关键词"""
    text_lower = text.lower()
    found_keywords = []

    for keyword in RISK_KEYWORDS:
        if keyword.lower() in text_lower:
            found_keywords.append(keyword)

    return len(found_keywords) > 0, found_keywords

@tool
def risk_control_check(query: str) -> str:
    """
    风控检查工具，识别用户查询中可能存在的风险

    该工具会检查用户输入是否包含：
    1. 违规关键词（如破解、刷单、诈骗等）
    2. 敏感信息（手机号、身份证、银行卡等）
    3. SQL注入、XSS攻击等恶意代码

    Args:
        query (str): 用户的查询文本

    Returns:
        str: 风控检查结果，包含风险等级和具体风险点

    Example:
        >>> risk_control_check("如何破解订单系统")
        "【风控告警】高风险 - 检测到违规关键词：破解"
    """
    ctx = request_context.get() or new_context(method="risk_control_check")

    risk_points = []
    risk_level = "安全"  # 默认安全

    try:
        # 1. 检查违规关键词
        has_keywords, keywords = _check_risk_keywords(query)
        if has_keywords:
            risk_points.append(f"检测到违规关键词: {', '.join(keywords)}")
            risk_level = "高风险"

        # 2. 检查敏感信息
        sensitive_info = _extract_sensitive_info(query)
        if sensitive_info:
            risk_points.append(f"检测到敏感信息: {', '.join(sensitive_info)}")
            risk_level = "中风险" if risk_level != "高风险" else "高风险"

        # 3. 检查输入长度（防范超长攻击）
        if len(query) > 500:
            risk_points.append(f"输入长度异常: {len(query)}字符")
            risk_level = "中风险" if risk_level != "高风险" else "高风险"

        # 4. 检查特殊字符频率（防范特殊字符攻击）
        special_chars = len(re.findall(r'[<>"\'\%;\(\)]', query))
        if special_chars > 20:
            risk_points.append(f"特殊字符频率异常: {special_chars}个")
            risk_level = "中风险" if risk_level != "高风险" else "高风险"

        # 返回风控结果
        if risk_points:
            risk_msg = f"【风控告警】{risk_level}\n"
            risk_msg += "\n".join(f"• {point}" for point in risk_points)
            risk_msg += "\n\n建议：请规范提问，避免使用违规词汇或提供敏感信息。"
            return risk_msg
        else:
            return "【风控通过】安全 - 未检测到风险"

    except Exception as e:
        return f"风控检查失败: {str(e)}"
