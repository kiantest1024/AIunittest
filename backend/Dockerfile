# 构建阶段
FROM python:3.11-slim AS builder

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 运行阶段
FROM python:3.11-slim

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 从构建阶段复制Python包
COPY --from=builder /root/.local /home/appuser/.local

# 复制应用代码
COPY . .

# 创建必要的目录并设置权限
RUN mkdir -p /app/logs /app/temp /app/shared && \
    chown -R appuser:appuser /app

# 切换到非root用户
USER appuser

# 设置PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8888/health || exit 1

EXPOSE 8888

# 使用Gunicorn运行，提高并发性能
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8888", \
     "--timeout", "300", \
     "--keep-alive", "5", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--preload"]
