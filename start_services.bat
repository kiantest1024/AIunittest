@echo off
chcp 65001 >nul
title AIunittest 服务启动器

echo.
echo ========================================
echo    AIunittest AI单元测试生成工具
echo ========================================
echo.

echo 🚀 正在启动服务...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查Node.js是否安装
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Node.js，请先安装Node.js
    pause
    exit /b 1
)

echo ✅ Python和Node.js环境检查通过
echo.

REM 检查后端依赖
echo 📦 检查后端依赖...
cd backend
if not exist "venv" (
    echo 🔧 创建Python虚拟环境...
    python -m venv venv
)

echo 🔧 激活虚拟环境并安装依赖...
call venv\Scripts\activate.bat
pip install -r requirements.txt >nul 2>&1

echo ✅ 后端依赖安装完成
echo.

REM 检查前端依赖
echo 📦 检查前端依赖...
cd ..\frontend
if not exist "node_modules" (
    echo 🔧 安装前端依赖...
    npm install
) else (
    echo ✅ 前端依赖已存在
)

echo.
echo 🎯 准备启动服务...
echo.

REM 启动后端服务
echo 🔥 启动后端服务 (端口: 8888)...
cd ..\backend
start "AIunittest Backend" cmd /k "call venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8888"

REM 等待后端启动
echo ⏳ 等待后端服务启动...
timeout /t 5 /nobreak >nul

REM 启动前端服务
echo 🎨 启动前端服务 (端口: 3000)...
cd ..\frontend
start "AIunittest Frontend" cmd /k "npm start"

echo.
echo ========================================
echo 🎉 服务启动完成！
echo ========================================
echo.
echo 📋 服务信息:
echo   • 后端服务: http://localhost:8888
echo   • 前端界面: http://localhost:3000
echo   • API文档: http://localhost:8888/docs
echo.
echo 🔧 AI配置管理:
echo   • 点击右上角"AI配置"按钮
echo   • 默认密码: password
echo   • 建议首次使用后修改密码
echo.
echo 📚 使用说明:
echo   • 查看 docs/AI_CONFIG_GUIDE.md
echo   • 查看 OPTIMIZATION_SUMMARY.md
echo.
echo ⚠️  注意: 请保持此窗口打开以监控服务状态
echo.

REM 等待用户输入
echo 按任意键打开Web界面...
pause >nul

REM 打开浏览器
start http://localhost:3000

echo.
echo 🌐 Web界面已在浏览器中打开
echo.
echo 按任意键退出...
pause >nul
