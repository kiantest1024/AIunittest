#!/bin/bash

# AIunittest 负载均衡部署脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    log_success "系统依赖检查完成"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p logs/nginx
    mkdir -p logs/backend-1
    mkdir -p logs/backend-2
    mkdir -p logs/backend-3
    mkdir -p nginx/ssl
    mkdir -p monitoring/grafana/dashboards
    mkdir -p monitoring/grafana/datasources
    
    log_success "目录创建完成"
}

# 检查环境配置
check_environment() {
    log_info "检查环境配置..."
    
    if [ ! -f ".env.production" ]; then
        log_warning "未找到 .env.production 文件，复制模板..."
        cp .env.production.template .env.production
        log_warning "请编辑 .env.production 文件，配置必要的环境变量"
        exit 1
    fi
    
    # 检查必要的环境变量
    source .env.production
    
    if [ -z "$POSTGRES_PASSWORD" ] || [ "$POSTGRES_PASSWORD" = "your_secure_password_here" ]; then
        log_error "请在 .env.production 中设置 POSTGRES_PASSWORD"
        exit 1
    fi
    
    if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_api_key" ]; then
        log_warning "未设置 OPENAI_API_KEY，某些功能可能无法使用"
    fi
    
    log_success "环境配置检查完成"
}

# 构建镜像
build_images() {
    log_info "构建 Docker 镜像..."
    
    # 构建后端镜像
    log_info "构建后端镜像..."
    docker-compose -f load-balanced-docker-compose.yml build backend-1
    
    # 构建前端镜像
    log_info "构建前端镜像..."
    docker-compose -f load-balanced-docker-compose.yml build frontend
    
    log_success "镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 首先启动基础服务
    log_info "启动基础服务 (Redis, PostgreSQL)..."
    docker-compose -f load-balanced-docker-compose.yml up -d redis postgres
    
    # 等待数据库启动
    log_info "等待数据库启动..."
    sleep 10
    
    # 启动后端服务
    log_info "启动后端服务..."
    docker-compose -f load-balanced-docker-compose.yml up -d backend-1 backend-2 backend-3
    
    # 等待后端服务启动
    log_info "等待后端服务启动..."
    sleep 15
    
    # 启动前端和负载均衡器
    log_info "启动前端和负载均衡器..."
    docker-compose -f load-balanced-docker-compose.yml up -d frontend nginx
    
    # 启动监控服务
    log_info "启动监控服务..."
    docker-compose -f load-balanced-docker-compose.yml up -d prometheus grafana
    
    log_success "所有服务启动完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 检查 Nginx
    if curl -f http://localhost/health > /dev/null 2>&1; then
        log_success "Nginx 健康检查通过"
    else
        log_error "Nginx 健康检查失败"
        return 1
    fi
    
    # 检查后端服务
    for i in {1..3}; do
        if docker-compose -f load-balanced-docker-compose.yml exec -T backend-$i curl -f http://localhost:8888/health > /dev/null 2>&1; then
            log_success "Backend-$i 健康检查通过"
        else
            log_warning "Backend-$i 健康检查失败"
        fi
    done
    
    # 检查数据库
    if docker-compose -f load-balanced-docker-compose.yml exec -T postgres pg_isready > /dev/null 2>&1; then
        log_success "PostgreSQL 健康检查通过"
    else
        log_error "PostgreSQL 健康检查失败"
        return 1
    fi
    
    # 检查 Redis
    if docker-compose -f load-balanced-docker-compose.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
        log_success "Redis 健康检查通过"
    else
        log_error "Redis 健康检查失败"
        return 1
    fi
    
    log_success "健康检查完成"
}

# 显示服务状态
show_status() {
    log_info "服务状态："
    docker-compose -f load-balanced-docker-compose.yml ps
    
    echo ""
    log_info "访问地址："
    echo "  应用主页: http://localhost"
    echo "  监控面板: http://localhost:3000 (Grafana)"
    echo "  指标监控: http://localhost:9090 (Prometheus)"
    echo ""
    log_info "负载均衡状态："
    echo "  后端实例数: 3"
    echo "  每实例最大并发: 5"
    echo "  总并发能力: 15"
}

# 主函数
main() {
    log_info "开始部署 AIunittest 负载均衡系统..."
    
    check_dependencies
    create_directories
    check_environment
    build_images
    start_services
    
    log_info "等待服务完全启动..."
    sleep 30
    
    health_check
    show_status
    
    log_success "部署完成！"
}

# 处理命令行参数
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "stop")
        log_info "停止所有服务..."
        docker-compose -f load-balanced-docker-compose.yml down
        log_success "服务已停止"
        ;;
    "restart")
        log_info "重启服务..."
        docker-compose -f load-balanced-docker-compose.yml restart
        log_success "服务已重启"
        ;;
    "status")
        show_status
        ;;
    "logs")
        docker-compose -f load-balanced-docker-compose.yml logs -f
        ;;
    "health")
        health_check
        ;;
    *)
        echo "用法: $0 {deploy|stop|restart|status|logs|health}"
        exit 1
        ;;
esac
