# 🚀 AIunittest 负载均衡部署指南

## 📋 部署架构

本部署方案采用负载均衡架构，最大化用户并发能力：

```
Internet
    ↓
[Nginx 负载均衡器]
    ↓
┌─────────────────────────────────┐
│  Backend-1  │  Backend-2  │  Backend-3  │
│   (5并发)   │   (5并发)   │   (5并发)   │
└─────────────────────────────────┘
    ↓
[Redis 缓存] + [PostgreSQL 数据库]
    ↓
[监控系统: Prometheus + Grafana]
```

### 🎯 性能指标

- **总并发能力**: 15个同时任务 (3实例 × 5并发)
- **负载均衡**: Nginx least_conn 算法
- **缓存**: Redis 会话共享
- **数据库**: PostgreSQL 任务状态持久化
- **监控**: 实时性能监控和告警

## 🛠️ 部署前准备

### 系统要求

- **操作系统**: Linux (推荐 Ubuntu 20.04+)
- **内存**: 最少 8GB (推荐 16GB+)
- **CPU**: 最少 4核 (推荐 8核+)
- **磁盘**: 最少 50GB 可用空间
- **网络**: 稳定的互联网连接

### 软件依赖

```bash
# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

## 🚀 快速部署

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd AIunittest/deployment
```

### 2. 配置环境变量

```bash
# 复制环境配置模板
cp .env.production.template .env.production

# 编辑配置文件
nano .env.production
```

**必须配置的环境变量**：

```bash
# 数据库密码 (必须修改)
POSTGRES_PASSWORD=your_secure_password_here

# API Keys (至少配置一个)
OPENAI_API_KEY=your_openai_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# 监控密码
GRAFANA_PASSWORD=your_grafana_password

# 域名 (如果使用HTTPS)
DOMAIN_NAME=your-domain.com
```

### 3. 执行部署

```bash
# 给部署脚本执行权限
chmod +x deploy.sh

# 开始部署
./deploy.sh deploy
```

### 4. 验证部署

```bash
# 检查服务状态
./deploy.sh status

# 查看日志
./deploy.sh logs

# 健康检查
./deploy.sh health
```

## 🌐 访问地址

部署完成后，可以通过以下地址访问：

- **应用主页**: http://your-server-ip
- **监控面板**: http://your-server-ip:3000 (Grafana)
- **指标监控**: http://your-server-ip:9090 (Prometheus)

## 📊 性能优化配置

### 并发配置

每个后端实例的并发配置：

```yaml
environment:
  - MAX_CONCURRENT_TASKS=5  # 每实例最大并发任务数
```

### Nginx 优化

```nginx
worker_processes auto;           # 自动检测CPU核心数
worker_connections 4096;         # 每个worker的连接数
keepalive_timeout 65;           # 保持连接时间
client_max_body_size 100M;      # 最大上传文件大小
```

### 资源限制

```yaml
deploy:
  resources:
    limits:
      cpus: '2'      # CPU限制
      memory: 2G     # 内存限制
    reservations:
      cpus: '1'      # CPU预留
      memory: 1G     # 内存预留
```

## 🔧 运维管理

### 常用命令

```bash
# 启动服务
./deploy.sh deploy

# 停止服务
./deploy.sh stop

# 重启服务
./deploy.sh restart

# 查看状态
./deploy.sh status

# 查看日志
./deploy.sh logs

# 健康检查
./deploy.sh health
```

### 扩容操作

如需增加后端实例：

1. 编辑 `load-balanced-docker-compose.yml`
2. 添加新的 backend-4 服务
3. 更新 nginx.conf 中的 upstream 配置
4. 重新部署

### 监控告警

访问 Grafana (http://your-server-ip:3000)：

- 默认用户名: admin
- 密码: 在 .env.production 中配置的 GRAFANA_PASSWORD

监控指标包括：
- 系统资源使用率
- 应用响应时间
- 错误率统计
- 并发任务数量

## 🔒 安全配置

### HTTPS 配置

1. 获取SSL证书：

```bash
# 使用 Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com
```

2. 复制证书到部署目录：

```bash
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem
```

3. 取消注释 nginx.conf 中的 HTTPS 配置

### 防火墙配置

```bash
# 开放必要端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 3000/tcp  # Grafana (可选，仅内网访问)
sudo ufw allow 9090/tcp  # Prometheus (可选，仅内网访问)
sudo ufw enable
```

## 🐛 故障排除

### 常见问题

1. **服务启动失败**
   ```bash
   # 查看详细日志
   docker-compose -f load-balanced-docker-compose.yml logs backend-1
   ```

2. **数据库连接失败**
   ```bash
   # 检查数据库状态
   docker-compose -f load-balanced-docker-compose.yml exec postgres pg_isready
   ```

3. **Redis连接失败**
   ```bash
   # 检查Redis状态
   docker-compose -f load-balanced-docker-compose.yml exec redis redis-cli ping
   ```

4. **负载均衡不工作**
   ```bash
   # 检查Nginx配置
   docker-compose -f load-balanced-docker-compose.yml exec nginx nginx -t
   ```

### 日志位置

- Nginx日志: `logs/nginx/`
- 后端日志: `logs/backend-1/`, `logs/backend-2/`, `logs/backend-3/`
- 应用日志: 通过 `docker-compose logs` 查看

## 📈 性能测试

### 压力测试

```bash
# 安装测试工具
sudo apt install apache2-utils

# 并发测试
ab -n 1000 -c 50 http://your-server-ip/api/health

# 文件上传测试
ab -n 100 -c 10 -p test-file.txt -T 'multipart/form-data' http://your-server-ip/api/upload
```

### 监控指标

关键性能指标：
- 响应时间 < 2秒
- 错误率 < 1%
- CPU使用率 < 80%
- 内存使用率 < 85%
- 并发处理能力: 15个任务

## 🔄 备份与恢复

### 数据备份

```bash
# 备份数据库
docker-compose -f load-balanced-docker-compose.yml exec postgres pg_dump -U aitest aitest > backup.sql

# 备份Redis数据
docker-compose -f load-balanced-docker-compose.yml exec redis redis-cli BGSAVE
```

### 数据恢复

```bash
# 恢复数据库
docker-compose -f load-balanced-docker-compose.yml exec -T postgres psql -U aitest aitest < backup.sql

# 恢复Redis数据
docker-compose -f load-balanced-docker-compose.yml exec redis redis-cli FLUSHALL
# 然后复制备份文件到Redis容器并重启
```

---

**部署支持**: 如遇问题，请查看日志文件或联系技术支持。
