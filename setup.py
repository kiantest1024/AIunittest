#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI单元测试生成工具 - 安装脚本

此脚本用于安装AI单元测试生成工具所需的依赖。
"""

import os
import sys
import subprocess
import platform

def print_header(message):
    """打印带有格式的标题"""
    print("\n" + "=" * 60)
    print(f" {message}")
    print("=" * 60)

def print_step(message):
    """打印步骤信息"""
    print(f"\n>> {message}")

def run_command(command):
    """运行命令并返回结果"""
    print(f"执行: {' '.join(command)}")
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"错误: {e}")
        if e.stdout:
            print(f"输出: {e.stdout}")
        if e.stderr:
            print(f"错误输出: {e.stderr}")
        return False

def check_python_version():
    """检查Python版本"""
    print_step("检查Python版本")

    major, minor, _ = platform.python_version_tuple()
    version = f"{major}.{minor}"
    print(f"当前Python版本: {version}")

    if int(major) < 3 or (int(major) == 3 and int(minor) < 8):
        print("错误: 需要Python 3.8或更高版本")
        return False

    print("Python版本检查通过")
    return True

def install_dependencies():
    """安装依赖"""
    print_step("安装依赖")

    # 基本依赖
    basic_deps = ["requests"]

    # GUI依赖
    gui_deps = []

    # 测试依赖
    test_deps = ["pytest"]

    # 安装基本依赖
    print("安装基本依赖...")
    if not run_command([sys.executable, "-m", "pip", "install", "--upgrade"] + basic_deps):
        return False

    # 询问是否安装GUI依赖
    install_gui = input("\n是否安装GUI依赖? (y/n): ").strip().lower() == 'y'
    if install_gui and gui_deps:
        print("安装GUI依赖...")
        if not run_command([sys.executable, "-m", "pip", "install", "--upgrade"] + gui_deps):
            return False

    # 询问是否安装测试依赖
    install_test = input("\n是否安装测试依赖? (y/n): ").strip().lower() == 'y'
    if install_test:
        print("安装测试依赖...")
        if not run_command([sys.executable, "-m", "pip", "install", "--upgrade"] + test_deps):
            return False

    print("所有依赖安装完成")
    return True

def create_directories():
    """创建必要的目录"""
    print_step("创建必要的目录")

    dirs = ["tests/generated"]

    for directory in dirs:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"目录已创建: {directory}")
        except Exception as e:
            print(f"创建目录 {directory} 时出错: {e}")
            return False

    return True

def setup_api_keys():
    """设置API密钥"""
    print_step("设置API密钥")

    print("您可以通过以下两种方式设置API密钥:")
    print("1. 在config.py文件中直接设置")
    print("2. 设置环境变量")

    print("\n支持的API密钥环境变量:")
    print("- OPENAI_API_KEY: 用于OpenAI模型 (ChatGPT, GPT-4)")
    print("- AZURE_OPENAI_API_KEY: 用于Azure OpenAI模型")
    print("- ANTHROPIC_API_KEY: 用于Anthropic Claude模型")
    print("- GOOGLE_API_KEY: 用于Google Gemini模型")
    print("- GROK_API_KEY: 用于xAI Grok模型")
    print("- DEEPSEEK_API_KEY: 用于DeepSeek模型")

    print("\n请参考README.md文件了解更多信息。")

    return True

def main():
    """主函数"""
    print_header("AI单元测试生成工具安装")

    # 检查Python版本
    if not check_python_version():
        sys.exit(1)

    # 安装依赖
    if not install_dependencies():
        print("安装依赖失败")
        sys.exit(1)

    # 创建目录
    if not create_directories():
        print("创建目录失败")
        sys.exit(1)

    # 设置API密钥
    setup_api_keys()

    print_header("安装完成")
    print("您现在可以使用以下命令运行工具:")
    print("- 命令行界面: python initial.py")
    print("- 图形界面: python gui.py")
    print("\n请确保在运行前设置了API密钥。")

if __name__ == "__main__":
    main()
