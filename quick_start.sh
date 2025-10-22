#!/bin/bash
# 快速启动脚本 - 自动创建虚拟环境并安装依赖

echo "📚 PDF智能标注工具 - 快速开始"
echo "================================"

# 检查是否安装了Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python"
    exit 1
fi

echo "✓ Python已安装 ($(python3 --version))"

# 检查或创建虚拟环境
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo ""
    echo "🔧 未找到虚拟环境，正在创建..."
    python3 -m venv "$VENV_DIR"
    if [ $? -eq 0 ]; then
        echo "✓ 虚拟环境创建成功: $VENV_DIR/"
    else
        echo "❌ 创建虚拟环境失败"
        exit 1
    fi
else
    echo "✓ 虚拟环境已存在: $VENV_DIR/"
fi

# 激活虚拟环境
echo ""
echo "🚀 正在激活虚拟环境..."
source "$VENV_DIR/bin/activate"

if [ $? -eq 0 ]; then
    echo "✓ 虚拟环境已激活"
    echo "   Python路径: $(which python)"
else
    echo "❌ 激活虚拟环境失败"
    exit 1
fi

# 检查并安装依赖
echo ""
if ! python -c "import fitz" 2>/dev/null; then
    echo "📦 正在安装依赖包..."
    pip install --upgrade pip
    pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        echo "✓ 依赖安装成功"
    else
        echo "❌ 依赖安装失败"
        exit 1
    fi
else
    echo "✓ 依赖已安装"
fi

# 检查.env文件
echo ""
if [ ! -f .env ]; then
    echo "⚠️  警告: 未找到.env文件"
    
    # 检查是否有env_template.txt
    if [ -f env_template.txt ]; then
        echo "📝 发现 env_template.txt，正在创建 .env 文件..."
        cp env_template.txt .env
        echo "✓ 已创建 .env 文件"
        echo ""
        echo "⚠️  请编辑 .env 文件，填入你的 OpenAI API 密钥："
        echo "   nano .env"
        echo "   或"
        echo "   open .env"
    else
        echo "请创建.env文件并设置你的OpenAI API密钥："
        echo ""
        echo "  OPENAI_API_KEY=your_api_key_here"
        echo "  OPENAI_MODEL=gpt-4o"
        echo "  OPENAI_BASE_URL=https://api.zhizengzeng.com/v1"
    fi
    echo ""
    read -p "是否继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        deactivate 2>/dev/null
        exit 1
    fi
else
    echo "✓ .env 文件已存在"
fi

echo ""
echo "================================"
echo "✅ 环境准备完成！"
echo "================================"
echo ""
echo "使用方法："
echo "  1. 激活虚拟环境（如果还没激活）："
echo "     source venv/bin/activate"
echo ""
echo "  2. 运行程序："
echo "     python main.py your_paper.pdf"
echo ""
echo "  3. 查看帮助："
echo "     python main.py --help"
echo ""
echo "  4. 退出虚拟环境："
echo "     deactivate"
echo "================================"
echo ""
echo "💡 提示: 虚拟环境已激活，可以直接运行 python main.py"
echo ""

