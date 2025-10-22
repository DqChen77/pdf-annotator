# PDF智能标注工具 🤖📄

一个使用AI自动分析和标注学术论文PDF的工具。它可以：
- ✨ 自动识别论文中的关键观点和重要发现
- 🖍️ 在PDF上高亮关键句子
- 📝 在合适位置添加AI生成的总结注释
- 📚 生成更便于阅读和理解的标注版PDF

## 功能特点

- **智能识别**: 使用GPT-4等大语言模型分析论文内容
- **精准标注**: 自动在重要观点处添加黄色高亮
- **总结注释**: 为每个重要段落生成简洁的总结笔记
- **保留原版**: 基于原PDF生成，保持原有格式和质量
- **易于使用**: 简单的命令行界面

## 安装

### 1. 克隆或下载项目

```bash
cd /Users/sokratis/Fudan/zzr/pdf_annotator
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

需要的主要依赖：
- `PyMuPDF` (fitz): PDF处理
- `openai`: OpenAI API调用
- `python-dotenv`: 环境变量管理
- `tqdm`: 进度条显示

### 3. 配置API密钥

创建 `.env` 文件（可以复制 `.env.example`）：

```bash
# .env 文件内容
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4
# 如果使用其他API端点（如国内代理），可以设置：
# OPENAI_BASE_URL=https://api.openai.com/v1
```

**获取OpenAI API密钥**: 访问 https://platform.openai.com/api-keys

## 使用方法

### 基本用法

```bash
python main.py your_paper.pdf
```

这将在同一目录下生成 `your_paper_annotated.pdf`

### 指定输出文件

```bash
python main.py input.pdf -o output.pdf
```

### 使用不同的模型

```bash
# 使用GPT-3.5（更快，成本更低）
python main.py paper.pdf --model gpt-3.5-turbo

# 使用GPT-4（更准确，推荐）
python main.py paper.pdf --model gpt-4
```

### 直接传入API密钥

```bash
python main.py paper.pdf --api-key sk-xxxxxxxxxxxxx
```

### 查看详细信息

```bash
python main.py paper.pdf -v
```

## 工作原理

1. **PDF解析**: 使用PyMuPDF提取PDF中的文本和结构信息
2. **文本分块**: 将论文内容按段落分块，便于AI处理
3. **AI分析**: 调用OpenAI API分析每个文本块，识别关键观点
4. **智能标注**: 
   - 在关键句子上添加黄色高亮
   - 在段落旁边添加总结注释
5. **生成PDF**: 保存带有所有标注的新PDF文件

## 项目结构

```
pdf_annotator/
├── main.py              # 主程序入口
├── config.py            # 配置文件
├── pdf_reader.py        # PDF读取模块
├── ai_analyzer.py       # AI分析模块
├── pdf_annotator.py     # PDF标注模块
├── requirements.txt     # Python依赖
├── .env.example         # 环境变量示例
└── README.md           # 说明文档
```

## 配置选项

在 `config.py` 中可以自定义：

- `MAX_TOKENS_PER_CHUNK`: 每次发送给AI的最大token数（默认2000）
- `HIGHLIGHT_COLOR`: 高亮颜色（默认黄色）
- `NOTE_COLOR`: 注释框颜色（默认蓝色）
- `SYSTEM_PROMPT`: AI系统提示词
- `ANALYSIS_PROMPT`: AI分析提示词模板

## 注意事项

⚠️ **API费用**: 
- 使用OpenAI API会产生费用
- GPT-4的成本约为 $0.03/1K tokens（输入）
- 一篇20页的论文大约需要消耗 0.5-1美元
- 建议先用短文档测试

⚠️ **处理时间**:
- 取决于论文长度和API响应速度
- 一篇标准论文（20-30页）通常需要5-10分钟
- 工具会显示进度条

⚠️ **PDF格式**:
- 最适合处理文本型PDF（非扫描版）
- 扫描版PDF需要先进行OCR处理

## 示例

使用工作区中的PDF文件：

```bash
# 标注Embodied parenting论文
python main.py "/Users/sokratis/Fudan/zzr/Embodied+parenting_25_10_06_13_20_20.pdf"

# 标注Rilling & Young论文
python main.py "/Users/sokratis/Fudan/zzr/Rilling+%26+Young%2C+2014.pdf" -o rilling_annotated.pdf
```

## 高级用法

### 自定义提示词

编辑 `config.py` 中的 `ANALYSIS_PROMPT`，可以调整AI分析的侧重点：

```python
ANALYSIS_PROMPT = """请分析以下论文片段，重点关注：
1. 研究方法和实验设计
2. 统计显著的发现
3. 创新性观点

论文片段：
{text}

请以JSON格式返回...
"""
```

### 批量处理

创建一个简单的bash脚本：

```bash
#!/bin/bash
for pdf in *.pdf; do
    python main.py "$pdf"
done
```

## 故障排除

### 问题：无法提取PDF文本
- 检查PDF是否为扫描版
- 尝试先用OCR工具处理

### 问题：API调用失败
- 检查API密钥是否正确
- 检查网络连接
- 如果在国内，可能需要设置代理

### 问题：标注位置不准确
- PyMuPDF的文本搜索有时不够精确
- 可以尝试调整 `pdf_annotator.py` 中的搜索逻辑

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License

## 致谢

- [PyMuPDF](https://pymupdf.readthedocs.io/) - 强大的PDF处理库
- [OpenAI](https://openai.com/) - 提供AI能力

---

**提示**: 这个工具特别适合需要快速了解大量论文的研究人员和学生。AI生成的标注可以作为第一遍阅读的辅助，帮助快速抓住重点！📚✨

