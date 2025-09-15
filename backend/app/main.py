# backend/app/main.py

import logging
import time
import os
from fastapi import FastAPI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base

# --- 1. 配置日志 ---
# 确保日志能实时输出，而不是被 uvicorn 缓存
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- 2. 数据库配置 ---
# 从环境变量中安全地获取数据库连接字符串
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/mydb")

# 创建 SQLAlchemy 引擎
# pool_pre_ping=True 会在每次从连接池获取连接时，先发送一个简单的 "ping" 查询来检查连接是否有效
# 这对于 Docker 环境中可能存在的网络瞬断非常有帮助
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# 创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建所有数据模型的基础类
# 注意：你的实际模型应该在 models.py 中定义并导入
try:
    from .models import Base
except ImportError:
    logger.warning("models.py not found, creating a placeholder Base. The application will run, but no tables will be created.")
    Base = declarative_base()


# --- 3. 应用启动事件 ---
# 使用 FastAPI 的 on_event 装饰器来处理应用启动时的逻辑
# 这是一个更现代、更推荐的方式
app = FastAPI(
    title="企业知识库问答 API",
    description="为企业知识库问答产品提供后端服务",
    version="0.1.0",
)

@app.on_event("startup")
def on_startup():
    """
    应用启动时执行：
    1. 循环重试以确保数据库服务已准备好。
    2. 创建所有定义的数据库表。
    """
    logger.info("Application starting up...")
    
    max_retries = 30
    retries = 0
    
    # 循环等待数据库准备就绪
    while retries < max_retries:
        try:
            # 使用 with engine.connect() 来获取一个临时连接
            with engine.connect() as connection:
                # =========================================================
                #  ↓↓↓ 这里是关键的修复点 ↓↓↓
                #
                # 使用 text() 函数将字符串标记为可执行的SQL语句
                # 这是新版 SQLAlchemy 的要求
                connection.execute(text("SELECT 1"))
                # =========================================================
                
                logger.info(f"Database connection successful on attempt {retries + 1}.")
                
                # 连接成功后，创建所有表
                logger.info("Creating database tables if they don't exist...")
                Base.metadata.create_all(bind=engine)
                logger.info("Tables created successfully.")
                
                # 成功后跳出循环
                break

        except OperationalError as e:
            retries += 1
            logger.warning(f"Database connection attempt {retries}/{max_retries} failed: {e}")
            time.sleep(2) # 等待2秒再重试

    if retries >= max_retries:
        logger.error("Failed to connect to the database after maximum retries. The application will start, but database operations will fail.")

    logger.info("Application startup complete.")


# --- 4. API 路由定义 ---
@app.get("/", summary="根路径", tags=["Default"])
def read_root():
    """
    一个简单的根路径，用于验证服务是否正在运行。
    """
    return {"message": "Welcome to the Knowledge Base API!", "status": "running"}

@app.get("/health", summary="健康检查", tags=["Default"])
def health_check():
    """
    一个标准的健康检查端点，可用于负载均衡器或监控系统。
    """
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ok", "database_connection": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: Database connection error: {e}")
        return {"status": "error", "database_connection": "unhealthy"}

# 注意: FastAPI 会自动在 /docs 和 /redoc 生成 API 文档页面
# 你不需要为 /docs 单独创建一个路由

# 在这里，你可以包含其他模块的路由
# from .api import users, knowledge_bases
# app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
# app.include_router(knowledge_bases.router, prefix="/api/v1/kbs", tags=["Knowledge Bases"])