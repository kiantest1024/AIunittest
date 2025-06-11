#!/usr/bin/env python3
"""
AI单元测试生成器启动脚本
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

def check_dependencies():
    """检查依赖"""
    print("🔍 检查依赖...")

    if sys.version_info < (3, 8):
        print("❌ Python版本需要3.8或更高")
        return False

    required_packages = ['fastapi', 'uvicorn', 'requests']
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"❌ 缺少依赖包: {package}")
            print(f"请运行: pip install {package}")
            return False

    print("✅ 依赖检查通过")
    return True

def start_backend():
    """启动后端服务"""
    print("🚀 启动后端服务...")

    backend_dir = Path(__file__).parent / "backend" / "app"
    if not backend_dir.exists():
        print("❌ 后端目录不存在")
        return None

    cmd = [sys.executable, "main.py"]
    process = subprocess.Popen(
        cmd,
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    time.sleep(3)

    if process.poll() is None:
        print("✅ 后端服务启动成功")
        return process
    else:
        print("❌ 后端服务启动失败")
        stdout, stderr = process.communicate()
        print(f"错误信息: {stderr}")
        return None

def check_service_health():
    """检查服务健康状态"""
    try:
        import requests
        response = requests.get("http://localhost:8888/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务健康检查通过")
            return True
    except:
        pass

    print("❌ 服务健康检查失败")
    return False

def open_browser():
    """打开浏览器"""
    try:
        import webbrowser
        print("🌐 打开浏览器...")
        webbrowser.open("http://localhost:8888")
    except:
        print("⚠️ 无法自动打开浏览器，请手动访问: http://localhost:8888")

def signal_handler(signum, frame):
    """信号处理"""
    print("\n🛑 正在关闭服务...")
    sys.exit(0)

def main():
    """主函数"""
    print("🎯 AI单元测试生成器")
    print("=" * 50)

    signal.signal(signal.SIGINT, signal_handler)

    if not check_dependencies():
        return

    backend_process = start_backend()
    if not backend_process:
        return

    try:
        print("⏳ 等待服务就绪...")
        time.sleep(5)

        if check_service_health():
            open_browser()

            print("\n🎉 服务启动成功！")
            print("📋 访问地址: http://localhost:8888")
            print("🔧 API文档: http://localhost:8888/docs")
            print("⏹️  按 Ctrl+C 停止服务")

            backend_process.wait()
        else:
            print("❌ 服务启动失败")
            backend_process.terminate()

    except KeyboardInterrupt:
        print("\n🛑 用户中断")
    finally:
        if backend_process and backend_process.poll() is None:
            backend_process.terminate()
            backend_process.wait()
        print("✅ 服务已停止")

if __name__ == "__main__":
    main()
