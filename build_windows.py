#!/usr/bin/env python3
"""
Windows打包脚本
使用PyInstaller将程序打包成.exe文件
"""
import os
import sys
import subprocess


def build_exe():
    """打包成Windows可执行文件"""
    print("=" * 60)
    print("开始打包Windows可执行文件...")
    print("=" * 60)
    
    # PyInstaller命令
    cmd = [
        "pyinstaller",
        "--name=PDF智能标注工具",
        "--onefile",  # 打包成单个文件
        "--windowed",  # 不显示控制台窗口
        "--hidden-import=tiktoken_ext.openai_public",
        "--hidden-import=tiktoken_ext",
        "gui.py"
    ]
    
    # 添加图标（如果存在）
    if os.path.exists("icon.ico"):
        cmd.insert(4, "--icon=icon.ico")
    
    # 移除空字符串
    cmd = [c for c in cmd if c]
    
    print("\n执行命令:")
    print(" ".join(cmd))
    print()
    
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "=" * 60)
        print("✅ 打包成功！")
        print("=" * 60)
        print("\n可执行文件位置: dist/PDF智能标注工具.exe")
        print("\n下一步:")
        print("1. 将 dist/PDF智能标注工具.exe 复制到目标文件夹")
        print("2. 首次运行时配置API密钥")
        print("3. 选择PDF文件开始使用")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 打包失败: {e}")
        print("\n请确保已安装 PyInstaller:")
        print("  pip install pyinstaller")
        return False
    
    return True


def install_requirements():
    """安装打包所需的依赖"""
    print("正在安装打包依赖...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        install_requirements()
    else:
        build_exe()

