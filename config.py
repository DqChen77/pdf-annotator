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

# 默认颜色配置 (RGB 0-1)
DEFAULT_HIGHLIGHT_COLOR = (1, 1, 0)      # 黄色高亮：重要观点
DEFAULT_TERM_HIGHLIGHT_COLOR = (0.5, 0.8, 1)  # 浅蓝色高亮：专业术语
DEFAULT_SUMMARY_HIGHLIGHT_COLOR = (1, 0.7, 0.7)  # 淡红色高亮：段落总结
DEFAULT_NOTE_COLOR = (0.2, 0.6, 1)       # 蓝色注释框

# 可配置的颜色（从配置文件加载或使用默认值）
HIGHLIGHT_COLOR = DEFAULT_HIGHLIGHT_COLOR
TERM_HIGHLIGHT_COLOR = DEFAULT_TERM_HIGHLIGHT_COLOR
SUMMARY_HIGHLIGHT_COLOR = DEFAULT_SUMMARY_HIGHLIGHT_COLOR
NOTE_COLOR = DEFAULT_NOTE_COLOR

# 默认数量配置
DEFAULT_HIGHLIGHT_COUNT_MIN = 20
DEFAULT_HIGHLIGHT_COUNT_MAX = 30
DEFAULT_SUMMARY_COUNT_MIN = 5
DEFAULT_SUMMARY_COUNT_MAX = 10
DEFAULT_SUMMARY_WORD_COUNT_MIN = 40
DEFAULT_SUMMARY_WORD_COUNT_MAX = 80

# 可配置的数量
HIGHLIGHT_COUNT_MIN = DEFAULT_HIGHLIGHT_COUNT_MIN
HIGHLIGHT_COUNT_MAX = DEFAULT_HIGHLIGHT_COUNT_MAX
SUMMARY_COUNT_MIN = DEFAULT_SUMMARY_COUNT_MIN
SUMMARY_COUNT_MAX = DEFAULT_SUMMARY_COUNT_MAX
SUMMARY_WORD_COUNT_MIN = DEFAULT_SUMMARY_WORD_COUNT_MIN
SUMMARY_WORD_COUNT_MAX = DEFAULT_SUMMARY_WORD_COUNT_MAX

# 术语标注积极程度
TERM_ANNOTATION_LEVEL = "moderate"  # "conservative", "moderate", "aggressive"

def get_dynamic_analysis_prompt(
    highlight_min=20, 
    highlight_max=30,
    summary_min=5,
    summary_max=10,
    summary_word_min=40,
    summary_word_max=80,
    term_level="moderate"
):
    """
    根据用户配置生成动态的分析提示词
    
    Args:
        highlight_min: 关键观点最小数量
        highlight_max: 关键观点最大数量
        summary_min: 段落总结最小数量
        summary_max: 段落总结最大数量
        summary_word_min: 段落总结最小字数
        summary_word_max: 段落总结最大字数
        term_level: 术语标注积极程度 ("conservative", "moderate", "aggressive")
    
    Returns:
        生成的提示词字符串
    """
    
    # 根据术语标注级别调整说明
    term_instructions = {
        "conservative": """**标注策略：保守标注，只标注核心专业术语**
   - **必须标注：**
     - 核心专业术语：oxytocin, amygdala, hippocampus, dopamine
     - 所有缩写：fMRI, HPA, ANOVA, SEM
   - **不要标注：**
     - 一般学术词汇
     - 常见形容词和动词""",
        "moderate": """**标注策略：适中标注，标注专业术语和较难词汇**
   - **必须标注（优先级从高到低）：**
     - 形容词化专业词：mesolimbic, dopaminergic, hypothalamic
     - 复合专业词：mesolimbic dopaminergic system
     - 专业名词：oxytocin, amygdala, hippocampus
     - 长单词（8+字母）：neuroplasticity, conceptualization
     - 学术动词/形容词：attenuate, facilitate, salient
     - 所有缩写：fMRI, HPA, ANOVA, SEM
   - **不要标注：**
     - 太常见的：study, research, important""",
        "aggressive": """**标注策略：积极标注，标注所有可能困难的词汇（宁可多标注，不要遗漏）**
   - **必须标注：**
     - 所有专业术语
     - 所有形容词化的专业词
     - 所有长单词（8+字母）且不常见
     - 所有学术性较强的词汇
     - 所有缩写
   - **只要不是高中基础词汇，就可以标注**"""
    }
    
    term_instruction = term_instructions.get(term_level, term_instructions["moderate"])
    
    prompt = f"""你是一个专业的学术论文分析助手。请仔细阅读以下完整论文，完成三个任务：

**任务1：识别{highlight_min}-{highlight_max}个关键观点（黄色高亮）**
**任务2：识别所有专业术语（蓝色高亮，无数量限制）**
**任务3：为每个主要段落生成简洁总结**

---

### 任务1：识别关键观点高亮（{highlight_min}-{highlight_max}个）

标注论文中的**重要观点、发现、结论、方法**，建议分配：
- Introduction: 4-6个（背景、问题、假设、目的）
- Literature Review: 3-4个（理论基础、研究空白）
- Methods: 4-6个（研究设计、方法、样本、分析）
- Results: 6-10个（主要发现、数据、统计结果）
- Discussion: 4-6个（结果解释、理论贡献、局限性）
- Conclusion: 2-3个（核心结论、未来方向）

每个观点高亮必须：
- 完整的英文原句（精确匹配原文）
- 30-50字中文注释
- 标注章节

---

### 任务2：识别所有专业术语（全面标注）

{term_instruction}

**⚠️ 重要：全文覆盖要求**
- 必须从头到尾阅读整篇论文
- 确保标注的术语均匀分布在全文各个部分
- 特别注意Discussion和Results后半部分的专业术语

#### 标注格式：
每个术语必须包含：
- **text**: 完整准确的英文术语（在论文中实际出现的形式）
- **translation**: 5-15字的中文翻译
- **note**: 简短解释（可选，10-25字，帮助理解）

#### 关于重复：
- 每个术语在数组中只出现一次
- 不要为了凑数重复相同的词

---

### 任务3：段落总结（{summary_min}-{summary_max}个）

为每个主要段落（100字以上）生成一份详细精炼的中文总结（{summary_word_min}-{summary_word_max}字），说明这段主要讲什么，包括关键方法、发现或结论。

---

论文全文：
{{text}}

---

请严格按照JSON格式返回：
{{{{
    "highlights": [
        {{{{
            "text": "完整英文原句",
            "note": "中文注释（30-50字）",
            "section": "章节名",
            "type": "insight"
        }}}},
        ... ({highlight_min}-{highlight_max}个关键观点)
    ],
    "terms": [
        {{{{
            "text": "professional term",
            "translation": "专业术语",
            "note": "简短解释（可选）"
        }}}},
        ... (积极标注所有可能困难的术语，每个术语只出现一次）
    ],
    "summaries": [
        {{{{
            "paragraph_start": "段落开头的前20个字（用于定位）",
            "summary": "这段主要内容的详细中文总结（{summary_word_min}-{summary_word_max}字），包括关键方法、发现或结论"
        }}}},
        ... ({summary_min}-{summary_max}个主要段落)
    ]
}}}}

**重要提示：**
1. highlights数组：{highlight_min}-{highlight_max}个观点（均匀分布全文）
2. terms数组：按照上述标注策略全面标注
3. summaries数组：{summary_min}-{summary_max}个总结
4. **严禁重复：每个词只能出现一次**
5. **全文覆盖：确保前中后各部分都有术语分布**
"""
    return prompt

# AI提示词配置
SYSTEM_PROMPT = """你是一个专业的学术论文分析助手。你的任务是：
1. 识别文本中的关键观点、重要发现、核心方法
2. 为需要高亮的关键句子提供准确的文本位置（必须完整匹配原文）
3. 为每个高亮提供简洁的中文注释说明

请以结构化的方式输出结果。"""

ANALYSIS_PROMPT = """你是一个专业的学术论文分析助手。请仔细阅读以下完整论文，完成三个任务：

**任务1：识别20-30个关键观点（黄色高亮）**
**任务2：识别所有专业术语（蓝色高亮，无数量限制）**
**任务3：为每个主要段落生成简洁总结**

---

### 任务1：识别关键观点高亮（20-30个）

标注论文中的**重要观点、发现、结论、方法**，建议分配：
- Introduction: 4-6个（背景、问题、假设、目的）
- Literature Review: 3-4个（理论基础、研究空白）
- Methods: 4-6个（研究设计、方法、样本、分析）
- Results: 6-10个（主要发现、数据、统计结果）
- Discussion: 4-6个（结果解释、理论贡献、局限性）
- Conclusion: 2-3个（核心结论、未来方向）

每个观点高亮必须：
- 完整的英文原句（精确匹配原文）
- 30-50字中文注释
- 标注章节

---

### 任务2：识别所有专业术语（全面标注，宁多勿少）

**目标读者：中文母语者，需要大量词汇帮助**

请**非常全面**地标注所有可能让中文读者感到困难的词汇。**宁可多标注，不要遗漏！**

**⚠️ 重要：全文覆盖要求**
- 必须从头到尾阅读整篇论文
- 确保标注的术语均匀分布在全文各个部分
- 不要只标注前面几页的术语，后面的内容也要充分标注
- 特别注意Discussion和Results后半部分的专业术语

#### 标注原则（非常重要！）：
- 🎯 **积极标注：标注所有可能让读者感到困难或不熟悉的词汇**
- 📖 **标注标准：词本身较难、不常见，或者是专业术语**
- ⚠️ **判断标准：只要不是高中/大学基础英语词汇，就可以标注**
- 💡 **重点关注：**
  - 专业术语（任何学科）
  - 长单词（8个字母以上且不常见）
  - 形容词化的专业词（如 mesolimbic, dopaminergic, neurobiological）
  - 拉丁/希腊词源的学术词汇
  - 领域特定的复合词
- 📌 **严禁重复：**
  - 每个术语只能在数组中出现一次
  - 不要为了凑数而重复相同的词

#### 🔴 核心原则：
**"宁可多标注，不要遗漏困难词"**

标注门槛：
- ✅ **必须标注**：专业术语、长单词、形容词化的专业词
  - mesolimbic dopaminergic（中脑边缘多巴胺能的）
  - olfactory bulb（嗅球）
  - oxytocin（催产素）
  - amygdala（杏仁核）
  - hypothalamic（下丘脑的）
  - neuroplasticity（神经可塑性）
  
- ⚠️ **可以标注**：较长的学术词汇、不常见的动词/形容词
  - facilitate, attenuate, modulate（当用于专业语境时）
  - reciprocal, concurrent, salient（学术性较强的词）
  - perinatal, neonatal, gestational（医学时期）
  
- ❌ **不要标注**：日常基础词汇
  - study, research, data, result, method
  - important, significant, show, find
  - attachment, bonding, maternal（词本身很简单）

#### 应该标注的词汇类型（积极标注）：

1. **所有专业术语**（任何学科）
   - 解剖学：amygdala, hippocampus, hypothalamus, prefrontal cortex, olfactory bulb, striatum, thalamus
   - 化学/生物：oxytocin, cortisol, dopamine, serotonin, vasopressin, neuroplasticity
   - 生理系统：cardiovascular, endocrine, neuroendocrine, hypothalamic, dopaminergic, cholinergic
   - 技术/设备：fMRI, MRI, EEG, PET scan, spectroscopy
   - **重点：形容词化的专业词**（如 mesolimbic, dopaminergic, serotonergic, hypothalamic）

2. **研究方法和统计术语**（不常见的都标注）
   - quasi-experimental, propensity score, hierarchical modeling
   - heterogeneity, multicollinearity, autocorrelation
   - longitudinal, cross-sectional（可以标注）
   - structural equation modeling, multivariate analysis
   - Cronbach's alpha, Cohen's d, chi-square

3. **长单词和复杂词汇**（8字母以上且不常见）
   - 专业形容词：mesolimbic, dopaminergic, neurobiological, neuroendocrine, cardiovascular
   - 抽象概念：mentalization, embodiment, proprioception, interoception, conceptualization
   - 理论术语：epigenetics, transgenerational, allostatic, neuroplasticity
   - 生理时期：perinatal, neonatal, gestational, postnatal, prenatal（可以标注）

4. **学术性强的动词和形容词**
   - 动词：mediate, moderate, facilitate, attenuate, potentiate, elucidate, obviate
   - 形容词：salient, reciprocal, bilateral, concurrent, distal, proximal
   - 副词：concomitantly, reciprocally, unilaterally

5. **专业关系和结构**
   - dyadic, triadic, hierarchical
   - synchronization, coordination, regulation（专业语境下）
   - interaction, interconnection（专业语境下可标注）

6. **复合专业词汇**
   - mesolimbic dopaminergic system
   - hypothalamic-pituitary-adrenal axis
   - prefrontal cortex
   - nucleus accumbens
   - ventral tegmental area

7. **所有缩写**
   - ANOVA, SEM, HPA, fMRI, MRI, EEG, PET, DSM, ICD, WHO
   - 任何大写缩写都要标注

8. **拉丁/希腊词源**
   - per se, vis-à-vis, prima facie, in vivo, in vitro
   - albeit, albeit, notwithstanding

#### ❌ 不要标注这些基础词汇：
- 基础词汇：the, a, is, are, and, or, but, in, on, at
- 非常常见的词：study, research, data, result, method
- 太简单的动词：show, find, use, make, get
- 太简单的形容词：good, bad, big, small, high, low

#### 💡 简单判断标准：
1. **专业术语？** → 标注 ✅
2. **长单词（8+字母）且不常见？** → 标注 ✅  
3. **形容词化的专业词（如 -ic, -al, -ous 结尾）？** → 标注 ✅
4. **缩写？** → 标注 ✅
5. **拉丁/希腊词源？** → 标注 ✅
6. **高中基础词汇？** → 不标注 ❌

**标注示例（重要！）：**
- ✅ mesolimbic（中脑边缘的）- 8字母，专业形容词
- ✅ dopaminergic（多巴胺能的）- 12字母，专业形容词
- ✅ mesolimbic dopaminergic（中脑边缘多巴胺能的）- 复合专业词
- ✅ hypothalamic（下丘脑的）- 专业形容词
- ✅ neurobiological（神经生物学的）- 长单词，专业形容词
- ✅ oxytocin, amygdala, hippocampus（专业名词）
- ✅ attenuate, facilitate, modulate（学术动词，8+字母）
- ✅ perinatal, gestational, longitudinal（医学/研究术语）
- ❌ attachment, bonding, maternal（词本身太简单）
- ❌ important, significant（太常见）

#### 标注格式：
每个术语必须包含：
- **text**: 完整准确的英文术语（在论文中实际出现的形式）
- **translation**: 5-15字的中文翻译
- **note**: 简短解释（可选，10-25字，帮助理解）

#### 关于重复：
- 每个术语在数组中只出现一次
- 不要为了凑数重复相同的词

---

### 任务3：段落总结（5-10个）

为每个主要段落（100字以上）生成一份详细精炼的中文总结，说明这段主要讲什么，包括关键方法、发现或结论。

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
            "section": "章节名",
            "type": "insight"
        }},
        ... (20-30个关键观点)
    ],
    "terms": [
        {{
            "text": "professional term",
            "translation": "专业术语",
            "note": "简短解释（可选）"
        }},
        {{
            "text": "another complex term",
            "translation": "另一个复杂术语",
            "note": "帮助理解的说明"
        }},
        ... (积极标注所有可能困难的术语，包括专业术语、长单词、形容词化专业词等，每个术语只出现一次）
    ],
    "summaries": [
        {{
            "paragraph_start": "段落开头的前20个字（用于定位）",
            "summary": "这段主要内容的详细中文总结（40-80字），包括关键方法、发现或结论"
        }},
        ... (5-10个主要段落)
    ]
}}

**重要提示：**
1. highlights数组：20-30个观点（均匀分布全文）

2. terms数组：**积极标注所有可能困难的术语（宁可多标注，不要遗漏）**
   - **标注策略：宽松标注，重点关注长单词和专业术语**
   - **必须标注（优先级从高到低）：**
     - 形容词化专业词：mesolimbic, dopaminergic, hypothalamic, neurobiological, serotonergic
     - 复合专业词：mesolimbic dopaminergic system, nucleus accumbens, ventral tegmental area
     - 专业名词：oxytocin, amygdala, hippocampus, olfactory bulb, striatum
     - 长单词（8+字母）：neuroplasticity, conceptualization, heterogeneity, facilitation
     - 学术动词/形容词：attenuate, facilitate, modulate, elucidate, salient, reciprocal
     - 所有缩写：fMRI, HPA, ANOVA, SEM
   - **不要标注：**
     - 太常见的：study, research, important, significant, demonstrate
     - 太简单的：show, find, make, use, get
   - **严禁重复：每个词只能出现一次**
   - **全文覆盖：确保前中后各部分都有术语**
   
3. summaries数组：5-10个总结

4. **自检清单：**
   - ✅ 所有专业术语已标注（如 mesolimbic dopaminergic, ventral tegmental area）
   - ✅ 所有形容词化的专业词已标注（如 hypothalamic, neurobiological）
   - ✅ 所有长单词（8+字母）已标注
   - ✅ 没有重复的术语
   - ✅ 全文各部分都有术语分布
"""

