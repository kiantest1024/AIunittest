#!/bin/bash

# AIunittest 服务启动脚本 (Linux/Mac)

# 设置颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${2}${1}${NC}"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 清屏并显示标题
clear
print_message "========================================" $CYAN
print_message "   AIunittest AI单元测试生成工具" $CYAN
print_message "========================================" $CYAN
echo

print_message "🚀 正在启动服务..." $BLUE
echo

# 检查Python是否安装
if ! command_exists python3; then
    print_message "❌ 错误: 未找到Python3，请先安装Python 3.8+" $RED
    exit 1
fi

# 检查Node.js是否安装
if ! command_exists node; then
    print_message "❌ 错误: 未找到Node.js，请先安装Node.js" $RED
    exit 1
fi

print_message "✅ Python和Node.js环境检查通过" $GREEN
echo

# 检查后端依赖
print_message "📦 检查后端依赖..." $YELLOW
cd backend

if [ ! -d "venv" ]; then
    print_message "🔧 创建Python虚拟环境..." $YELLOW
    python3 -m venv venv
fi

print_message "🔧 激活虚拟环境并安装依赖..." $YELLOW
source venv/bin/activate
pip install -r requirements.txt >/dev/null 2>&1

print_message "✅ 后端依赖安装完成" $GREEN
echo

# 检查前端依赖
print_message "📦 检查前端依赖..." $YELLOW
cd ../frontend

if [ ! -d "node_modules" ]; then
    print_message "🔧 安装前端依赖..." $YELLOW
    npm install
else
    print_message "✅ 前端依赖已存在" $GREEN
fi

echo
print_message "🎯 准备启动服务..." $BLUE
echo

# 启动后端服务
print_message "🔥 启动后端服务 (端口: 8888)..." $YELLOW
cd ../backend

# 在新终端窗口启动后端
if command_exists gnome-terminal; then
    gnome-terminal --title="AIunittest Backend" -- bash -c "source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8888; exec bash"
elif command_exists xterm; then
    xterm -title "AIunittest Backend" -e "bash -c 'source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8888; exec bash'" &
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e 'tell app "Terminal" to do script "cd \"'$(pwd)'\" && source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8888"'
else
    # 后台启动
    print_message "⚠️  在后台启动后端服务..." $YELLOW
    source venv/bin/activate
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8888 > backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > backend.pid
fi

# 等待后端启动
print_message "⏳ 等待后端服务启动..." $YELLOW
sleep 5

# 启动前端服务
print_message "🎨 启动前端服务 (端口: 3000)..." $YELLOW
cd ../frontend

# 在新终端窗口启动前端
if command_exists gnome-terminal; then
    gnome-terminal --title="AIunittest Frontend" -- bash -c "npm start; exec bash"
elif command_exists xterm; then
    xterm -title "AIunittest Frontend" -e "bash -c 'npm start; exec bash'" &
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e 'tell app "Terminal" to do script "cd \"'$(pwd)'\" && npm start"'
else
    # 后台启动
    print_message "⚠️  在后台启动前端服务..." $YELLOW
    nohup npm start > frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > frontend.pid
fi

echo
print_message "========================================" $CYAN
print_message "🎉 服务启动完成！" $GREEN
print_message "========================================" $CYAN
echo

print_message "📋 服务信息:" $BLUE
print_message "  • 后端服务: http://localhost:8888" $NC
print_message "  • 前端界面: http://localhost:3000" $NC
print_message "  • API文档: http://localhost:8888/docs" $NC
echo

print_message "🔧 AI配置管理:" $PURPLE
print_message "  • 点击右上角\"AI配置\"按钮" $NC
print_message "  • 默认密码: password" $NC
print_message "  • 建议首次使用后修改密码" $NC
echo

print_message "📚 使用说明:" $CYAN
print_message "  • 查看 docs/AI_CONFIG_GUIDE.md" $NC
print_message "  • 查看 OPTIMIZATION_SUMMARY.md" $NC
echo

# 等待用户输入
print_message "按Enter键打开Web界面..." $YELLOW
read -r

# 打开浏览器
if command_exists xdg-open; then
    xdg-open http://localhost:3000
elif command_exists open; then
    open http://localhost:3000
elif command_exists firefox; then
    firefox http://localhost:3000 &
elif command_exists google-chrome; then
    google-chrome http://localhost:3000 &
else
    print_message "⚠️  请手动打开浏览器访问: http://localhost:3000" $YELLOW
fi

print_message "🌐 Web界面已在浏览器中打开" $GREEN
echo

# 提供停止服务的选项
print_message "按Enter键退出，或输入'stop'停止后台服务..." $YELLOW
read -r input

if [ "$input" = "stop" ] && [ -f "../backend/backend.pid" ]; then
    print_message "🛑 停止后台服务..." $YELLOW
    
    if [ -f "../backend/backend.pid" ]; then
        kill $(cat ../backend/backend.pid) 2>/dev/null
        rm ../backend/backend.pid
    fi
    
    if [ -f "frontend.pid" ]; then
        kill $(cat frontend.pid) 2>/dev/null
        rm frontend.pid
    fi
    
    print_message "✅ 服务已停止" $GREEN
fi

print_message "👋 感谢使用 AIunittest！" $CYAN
