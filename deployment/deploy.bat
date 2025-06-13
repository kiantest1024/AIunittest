@echo off
REM AIunittest 负载均衡部署脚本 (Windows版本)

setlocal enabledelayedexpansion

REM 颜色定义 (Windows 10+ 支持ANSI颜色)
set "RED=[31m"
set "GREEN=[32m"
set "YELLOW=[33m"
set "BLUE=[34m"
set "NC=[0m"

REM 日志函数
:log_info
echo %BLUE%[INFO]%NC% %~1
goto :eof

:log_success
echo %GREEN%[SUCCESS]%NC% %~1
goto :eof

:log_warning
echo %YELLOW%[WARNING]%NC% %~1
goto :eof

:log_error
echo %RED%[ERROR]%NC% %~1
goto :eof

REM 检查依赖
:check_dependencies
call :log_info "检查系统依赖..."

docker --version >nul 2>&1
if errorlevel 1 (
    call :log_error "Docker 未安装，请先安装 Docker Desktop"
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    call :log_error "Docker Compose 未安装，请先安装 Docker Compose"
    exit /b 1
)

call :log_success "系统依赖检查完成"
goto :eof

REM 创建必要的目录
:create_directories
call :log_info "创建必要的目录..."

if not exist "logs\nginx" mkdir logs\nginx
if not exist "logs\backend-1" mkdir logs\backend-1
if not exist "logs\backend-2" mkdir logs\backend-2
if not exist "logs\backend-3" mkdir logs\backend-3
if not exist "nginx\ssl" mkdir nginx\ssl
if not exist "monitoring\grafana\dashboards" mkdir monitoring\grafana\dashboards
if not exist "monitoring\grafana\datasources" mkdir monitoring\grafana\datasources

call :log_success "目录创建完成"
goto :eof

REM 检查环境配置
:check_environment
call :log_info "检查环境配置..."

if not exist ".env.production" (
    call :log_warning "未找到 .env.production 文件，复制模板..."
    if exist ".env.production.template" (
        copy ".env.production.template" ".env.production" >nul
        call :log_warning "请编辑 .env.production 文件，配置必要的环境变量"
        exit /b 1
    ) else (
        call :log_error "未找到 .env.production.template 模板文件"
        exit /b 1
    )
)

REM 简单检查关键配置
findstr /C:"your_secure_password_here" .env.production >nul
if not errorlevel 1 (
    call :log_error "请在 .env.production 中设置 POSTGRES_PASSWORD"
    exit /b 1
)

findstr /C:"your_openai_api_key" .env.production >nul
if not errorlevel 1 (
    call :log_warning "未设置 OPENAI_API_KEY，某些功能可能无法使用"
)

call :log_success "环境配置检查完成"
goto :eof

REM 构建镜像
:build_images
call :log_info "构建 Docker 镜像..."

call :log_info "构建后端镜像..."
docker-compose -f load-balanced-docker-compose.yml build backend-1
if errorlevel 1 (
    call :log_error "后端镜像构建失败"
    exit /b 1
)

call :log_info "构建前端镜像..."
docker-compose -f load-balanced-docker-compose.yml build frontend
if errorlevel 1 (
    call :log_error "前端镜像构建失败"
    exit /b 1
)

call :log_success "镜像构建完成"
goto :eof

REM 启动服务
:start_services
call :log_info "启动服务..."

call :log_info "启动基础服务 (Redis, PostgreSQL)..."
docker-compose -f load-balanced-docker-compose.yml up -d redis postgres
if errorlevel 1 (
    call :log_error "基础服务启动失败"
    exit /b 1
)

call :log_info "等待数据库启动..."
timeout /t 10 /nobreak >nul

call :log_info "启动后端服务..."
docker-compose -f load-balanced-docker-compose.yml up -d backend-1 backend-2 backend-3
if errorlevel 1 (
    call :log_error "后端服务启动失败"
    exit /b 1
)

call :log_info "等待后端服务启动..."
timeout /t 15 /nobreak >nul

call :log_info "启动前端和负载均衡器..."
docker-compose -f load-balanced-docker-compose.yml up -d frontend nginx
if errorlevel 1 (
    call :log_error "前端服务启动失败"
    exit /b 1
)

call :log_info "启动监控服务..."
docker-compose -f load-balanced-docker-compose.yml up -d prometheus grafana
if errorlevel 1 (
    call :log_warning "监控服务启动失败，但不影响主要功能"
)

call :log_success "所有服务启动完成"
goto :eof

REM 健康检查
:health_check
call :log_info "执行健康检查..."

REM 检查 Nginx
curl -f http://localhost/health >nul 2>&1
if errorlevel 1 (
    call :log_error "Nginx 健康检查失败"
    goto :eof
) else (
    call :log_success "Nginx 健康检查通过"
)

REM 检查后端服务
for %%i in (1 2 3) do (
    docker-compose -f load-balanced-docker-compose.yml exec -T backend-%%i curl -f http://localhost:8888/health >nul 2>&1
    if errorlevel 1 (
        call :log_warning "Backend-%%i 健康检查失败"
    ) else (
        call :log_success "Backend-%%i 健康检查通过"
    )
)

call :log_success "健康检查完成"
goto :eof

REM 显示服务状态
:show_status
call :log_info "服务状态："
docker-compose -f load-balanced-docker-compose.yml ps

echo.
call :log_info "访问地址："
echo   应用主页: http://localhost
echo   监控面板: http://localhost:3000 (Grafana)
echo   指标监控: http://localhost:9090 (Prometheus)
echo.
call :log_info "负载均衡状态："
echo   后端实例数: 3
echo   每实例最大并发: 5
echo   总并发能力: 15
goto :eof

REM 主函数
:main
call :log_info "开始部署 AIunittest 负载均衡系统..."

call :check_dependencies
if errorlevel 1 exit /b 1

call :create_directories
call :check_environment
if errorlevel 1 exit /b 1

call :build_images
if errorlevel 1 exit /b 1

call :start_services
if errorlevel 1 exit /b 1

call :log_info "等待服务完全启动..."
timeout /t 30 /nobreak >nul

call :health_check
call :show_status

call :log_success "部署完成！"
goto :eof

REM 停止服务
:stop_services
call :log_info "停止所有服务..."
docker-compose -f load-balanced-docker-compose.yml down
call :log_success "服务已停止"
goto :eof

REM 重启服务
:restart_services
call :log_info "重启服务..."
docker-compose -f load-balanced-docker-compose.yml restart
call :log_success "服务已重启"
goto :eof

REM 查看日志
:show_logs
docker-compose -f load-balanced-docker-compose.yml logs -f
goto :eof

REM 处理命令行参数
if "%1"=="" goto main
if "%1"=="deploy" goto main
if "%1"=="stop" goto stop_services
if "%1"=="restart" goto restart_services
if "%1"=="status" goto show_status
if "%1"=="logs" goto show_logs
if "%1"=="health" goto health_check

echo 用法: %0 {deploy^|stop^|restart^|status^|logs^|health}
exit /b 1
