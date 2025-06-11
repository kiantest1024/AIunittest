# AIuintCode 启动指南

## 🚀 **快速启动**

### **方法1: 使用批处理文件（推荐）**
```bash
# 在AIuintCode目录下运行
.\start.bat
```

### **方法2: 手动启动**
```bash
# 1. 进入后端目录
cd AIuintCode\backend\app

# 2. 启动服务
python main.py
```

### **方法3: 使用Python启动脚本**
```bash
# 在AIuintCode目录下运行
python start_server.py
```

## 🔧 **环境检查**

### **1. 检查Python环境**
```bash
python --version
# 应该显示 Python 3.8+
```

### **2. 安装依赖**
```bash
cd AIuintCode\backend
pip install -r requirements.txt
```

### **3. 运行诊断脚本**
```bash
cd AIuintCode
python diagnose.py
```

## 📡 **验证服务**

### **1. 检查服务状态**
打开浏览器访问：
- **健康检查**: http://localhost:8888/api/health
- **前端界面**: http://localhost:8888/
- **API文档**: http://localhost:8888/docs

### **2. 测试API接口**
```bash
# 健康检查
curl http://localhost:8888/api/health

# 获取支持的模型
curl http://localhost:8888/api/models

# 获取支持的语言
curl http://localhost:8888/api/languages
```

## 🐛 **常见问题解决**

### **问题1: 端口被占用**
```bash
# 查找占用8888端口的进程
netstat -ano | findstr :8888

# 杀掉进程（替换PID）
taskkill /f /pid <PID>
```

### **问题2: 依赖包缺失**
```bash
# 重新安装依赖
pip install --upgrade -r backend/requirements.txt
```

### **问题3: Python路径问题**
确保在正确的目录下运行：
```bash
# 应该在这个目录结构下
AIuintCode/
├── backend/
│   └── app/
│       └── main.py
├── frontend/
└── start.bat
```

### **问题4: 前端文件缺失**
检查前端构建文件：
```bash
# 检查是否存在
ls frontend/build/index.html

# 如果不存在，需要构建前端
cd frontend
npm install
npm run build
```

## 🎯 **服务信息**

### **后端服务**
- **地址**: http://localhost:8888
- **API前缀**: /api
- **文档**: http://localhost:8888/docs

### **支持的功能**
- ✅ **AI测试生成** - 支持Python、Java、Go、C++、C#
- ✅ **Java增强分析** - 92%覆盖率的Java测试生成
- ✅ **Git集成** - GitHub/GitLab仓库操作
- ✅ **文件上传** - 代码文件处理
- ✅ **前端界面** - React用户界面

### **支持的AI模型**
- chatgpt4nano
- chatgpt4.1mini
- google_gemini
- anthropic_claude
- xai_grok
- deepseek-V3
- deepseek-R1

## 📋 **启动检查清单**

- [ ] Python 3.8+ 已安装
- [ ] 依赖包已安装 (`pip install -r backend/requirements.txt`)
- [ ] 端口8888未被占用
- [ ] 后端文件完整 (`backend/app/main.py`存在)
- [ ] 前端文件完整 (`frontend/build/index.html`存在)
- [ ] 服务启动成功 (访问 http://localhost:8888/api/health)

## 🎉 **成功启动标志**

当看到以下日志时，表示服务启动成功：
```
INFO:     Uvicorn running on http://0.0.0.0:8888 (Press CTRL+C to quit)
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

然后可以访问：
- **前端界面**: http://localhost:8888/
- **API文档**: http://localhost:8888/docs
- **健康检查**: http://localhost:8888/api/health

## 🆘 **获取帮助**

如果仍然无法启动，请：

1. **运行诊断脚本**: `python diagnose.py`
2. **检查日志文件**: `logs/app.log`
3. **查看错误信息**: 启动时的控制台输出
4. **确认环境**: Python版本、依赖包、文件完整性

**🎯 按照这个指南，AIuintCode服务应该能够正常启动和运行！**
