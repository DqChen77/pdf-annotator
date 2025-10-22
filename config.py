"""
配置文件
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def get_openai_api_key():
    """动态获取API密钥"""
    return os.getenv('OPENAI_API_KEY')

def get_openai_model():
    """动态获取模型名称"""
    return os.getenv('OPENAI_MODEL', 'gpt-4')

def get_openai_base_url():
    """动态获取API地址"""
    return os.getenv('OPENAI_BASE_URL', None)

# 向后兼容：保留原有的常量
OPENAI_API_KEY = get_openai_api_key()
OPENAI_MODEL = get_openai_model()
OPENAI_BASE_URL = get_openai_base_url()

# PDF处理配置
MAX_TOKENS_PER_CHUNK = 12000  # 每次发送给AI的最大token数（用于全文分析）
HIGHLIGHT_COLOR = (1, 1, 0)  # 黄色高亮 (RGB 0-1)
NOTE_COLOR = (0.2, 0.6, 1)   # 蓝色注释框

# AI提示词配置
SYSTEM_PROMPT = """你是一个专业的学术论文分析助手。你的任务是：
1. 识别文本中的关键观点、重要发现、核心方法
2. 为需要高亮的关键句子提供准确的文本位置（必须完整匹配原文）
3. 为每个高亮提供简洁的中文注释说明

请以结构化的方式输出结果。"""

ANALYSIS_PROMPT = """你是一个专业的学术论文分析助手。请仔细阅读以下完整论文，完成两个任务：

**任务1：识别20-30个关键观点（用于高亮标注）**
**任务2：为每个主要段落生成简洁总结**

---

### 任务1：识别高亮（20-30个）

要求尽可能多地覆盖论文内容，建议分配：
- Introduction: 4-6个（背景、问题、假设、目的）
- Literature Review: 3-4个（理论基础、研究空白）
- Methods: 4-6个（研究设计、方法、样本、分析）
- Results: 6-10个（主要发现、数据、统计结果）
- Discussion: 4-6个（结果解释、理论贡献、局限性）
- Conclusion: 2-3个（核心结论、未来方向）

每个高亮必须：
- 完整的英文原句（精确匹配原文）
- 30-50字中文注释
- 标注章节

---

### 任务2：段落总结（5-10个）

为每个主要段落（100字以上）生成20-30字的中文总结，说明这段主要讲什么。

---

论文全文：
{text}

---

请严格按照JSON格式返回：
{{
    "highlights": [
        {{
            "text": "完整英文原句",
            "note": "中文注释（30-50字）",
            "section": "章节名"
        }},
        ... (至少20个，最多30个)
    ],
    "summaries": [
        {{
            "paragraph_start": "段落开头的前20个字（用于定位）",
            "summary": "这段主要内容的中文总结（20-30字）"
        }},
        ... (5-10个主要段落)
    ]
}}

**重要：必须返回20-30个highlights和5-10个summaries！**
"""

