import sys
import os

# 添加父目录到Python路径，解决导入问题
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles

# 根据运行位置动态调整导入路径
try:
    # backend目录运行
    from app.api.endpoints import router
    from app.api.errors import validation_exception_handler, value_error_handler, general_exception_handler
    from app.config import settings
    from app.utils.logger import logger
except ModuleNotFoundError:
    # app目录运行
    from api.endpoints import router
    from api.errors import validation_exception_handler, value_error_handler, general_exception_handler
    from config import settings
    from utils.logger import logger

# 定义生命周期管理器
@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    # 启动事件
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"App instance: {app_instance.title}")
    yield
    # 关闭事件
    logger.info(f"Shutting down {settings.APP_NAME}")

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源
    allow_credentials=False,  # 不携带凭证，避免CORS预检请求
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加异常处理器
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValueError, value_error_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 添加路由
app.include_router(router, prefix="/api")

# 添加静态文件服务
frontend_build_path = os.path.join(os.path.dirname(os.path.dirname(current_dir)), "frontend", "build")
if os.path.exists(frontend_build_path):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_build_path, "static")), name="static")
    app.mount("/", StaticFiles(directory=frontend_build_path, html=True), name="frontend")
    logger.info(f"Serving frontend from: {frontend_build_path}")
else:
    logger.warning(f"Frontend build directory not found: {frontend_build_path}")

    # 根路由（仅在没有前端文件时使用）
    @app.get("/")
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "description": settings.APP_DESCRIPTION,
            "frontend_path": frontend_build_path,
            "frontend_exists": os.path.exists(frontend_build_path)
        }

# 支持直接运行
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server with uvicorn...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8888,
        reload=True,
        log_level="info"
    )
