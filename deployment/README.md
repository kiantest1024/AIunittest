# 🚀 AIunittest 负载均衡部署方案

## 🎯 方案概述

本方案为 AIunittest 项目提供了完整的负载均衡部署解决方案，旨在最大化用户并发能力和系统可靠性。

### 🏗️ 架构特点

- **高并发**: 3个后端实例，总计15个并发任务处理能力
- **负载均衡**: Nginx least_conn 算法，智能分发请求
- **缓存优化**: Redis 会话共享和API响应缓存
- **数据持久化**: PostgreSQL 存储任务状态和系统数据
- **实时监控**: Prometheus + Grafana 监控告警
- **高可用**: 健康检查、自动重启、故障转移

### 📊 性能指标

| 指标 | 单实例 | 负载均衡 | 提升倍数 |
|------|--------|----------|----------|
| 并发任务数 | 3-5个 | 15个 | 3-5倍 |
| QPS | ~30 | ~100+ | 3倍+ |
| 可用性 | 99% | 99.9% | 显著提升 |
| 响应时间 | 1-3s | 0.5-2s | 优化 |

## 📁 文件结构

```
deployment/
├── load-balanced-docker-compose.yml  # 主部署配置
├── nginx/
│   └── nginx.conf                    # Nginx负载均衡配置
├── redis/
│   └── redis.conf                    # Redis配置
├── postgres/
│   └── init.sql                      # 数据库初始化脚本
├── monitoring/
│   └── prometheus.yml                # 监控配置
├── .env.production                   # 生产环境变量
├── deploy.sh                         # 一键部署脚本
├── performance_test.py               # 性能测试脚本
├── DEPLOYMENT_GUIDE.md               # 详细部署指南
└── README.md                         # 本文件
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 确保已安装 Docker 和 Docker Compose
docker --version
docker-compose --version

# 克隆项目到部署目录
cd deployment/
```

### 2. 配置环境

```bash
# 复制并编辑环境配置
cp .env.production.template .env.production
nano .env.production

# 必须修改的配置项：
# - POSTGRES_PASSWORD (数据库密码)
# - OPENAI_API_KEY (至少一个AI API密钥)
# - GRAFANA_PASSWORD (监控面板密码)
```

### 3. 一键部署

```bash
# 给脚本执行权限
chmod +x deploy.sh

# 开始部署
./deploy.sh deploy

# 等待部署完成（约2-5分钟）
```

### 4. 验证部署

```bash
# 检查服务状态
./deploy.sh status

# 健康检查
./deploy.sh health

# 性能测试
python3 performance_test.py --users 20 --requests 10
```

## 🌐 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 主应用 | http://your-server-ip | AI单元测试生成工具 |
| 监控面板 | http://your-server-ip:3000 | Grafana仪表板 |
| 指标监控 | http://your-server-ip:9090 | Prometheus监控 |

## 🔧 运维命令

```bash
# 部署/启动
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

## 📈 性能测试

### 基础测试

```bash
# 轻量测试 (10用户, 每用户5请求)
python3 performance_test.py --users 10 --requests 5

# 中等负载测试 (20用户, 每用户10请求)
python3 performance_test.py --users 20 --requests 10

# 高负载测试 (50用户, 每用户20请求)
python3 performance_test.py --users 50 --requests 20
```

### 负载均衡测试

```bash
# 测试负载均衡效果
python3 performance_test.py --test-lb --users 30 --requests 5
```

### 预期性能指标

- **成功率**: > 99%
- **平均响应时间**: < 2秒
- **QPS**: > 50 (理想情况 > 100)
- **并发处理**: 15个同时任务

## 🔍 监控告警

### Grafana 仪表板

访问 `http://your-server-ip:3000`，使用配置的用户名密码登录。

**关键监控指标**:
- 系统资源使用率 (CPU, 内存, 磁盘)
- 应用响应时间和错误率
- 数据库连接数和查询性能
- Redis缓存命中率
- Nginx请求分发统计

### 告警规则

- CPU使用率 > 80%
- 内存使用率 > 85%
- 应用错误率 > 5%
- 响应时间 > 5秒
- 数据库连接数 > 80%

## 🔒 安全配置

### 基础安全

- 非root用户运行容器
- 网络隔离和端口限制
- 环境变量敏感信息保护
- 定期安全更新

### HTTPS 配置

```bash
# 1. 获取SSL证书 (Let's Encrypt)
sudo certbot certonly --standalone -d your-domain.com

# 2. 复制证书
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem

# 3. 启用HTTPS配置
# 编辑 nginx/nginx.conf，取消注释HTTPS部分

# 4. 重启服务
./deploy.sh restart
```

## 🔄 扩容方案

### 水平扩容

1. **增加后端实例**:
   ```yaml
   # 在 load-balanced-docker-compose.yml 中添加
   backend-4:
     # 复制 backend-1 配置
   ```

2. **更新负载均衡**:
   ```nginx
   # 在 nginx.conf 的 upstream 中添加
   server backend-4:8888 max_fails=3 fail_timeout=30s;
   ```

3. **重新部署**:
   ```bash
   ./deploy.sh restart
   ```

### 垂直扩容

调整资源限制：
```yaml
deploy:
  resources:
    limits:
      cpus: '4'      # 增加CPU
      memory: 4G     # 增加内存
```

## 🐛 故障排除

### 常见问题

1. **服务启动失败**
   ```bash
   # 查看具体错误
   docker-compose -f load-balanced-docker-compose.yml logs backend-1
   ```

2. **数据库连接问题**
   ```bash
   # 检查数据库状态
   docker-compose -f load-balanced-docker-compose.yml exec postgres pg_isready
   ```

3. **负载均衡不生效**
   ```bash
   # 检查Nginx配置
   docker-compose -f load-balanced-docker-compose.yml exec nginx nginx -t
   ```

4. **性能问题**
   - 检查资源使用情况
   - 调整并发配置
   - 优化数据库查询
   - 增加缓存

### 日志查看

```bash
# 查看所有服务日志
./deploy.sh logs

# 查看特定服务日志
docker-compose -f load-balanced-docker-compose.yml logs backend-1
docker-compose -f load-balanced-docker-compose.yml logs nginx
```

## 📚 相关文档

- [详细部署指南](DEPLOYMENT_GUIDE.md) - 完整的部署步骤和配置说明
- [性能优化指南](../docs/PERFORMANCE_OPTIMIZATION.md) - 性能调优建议
- [监控配置指南](../docs/MONITORING_SETUP.md) - 监控系统配置

## 🆘 技术支持

如遇到部署问题：

1. 查看 [故障排除](#-故障排除) 部分
2. 检查日志文件获取详细错误信息
3. 参考 [详细部署指南](DEPLOYMENT_GUIDE.md)
4. 联系技术支持团队

---

**部署成功后，您的 AIunittest 系统将具备高并发、高可用、可监控的企业级特性！** 🎉
