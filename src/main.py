"""
Echo Agentic Engine - FastAPI 应用入口

流程 3.2.1 - OpenCode API 代理主流程入口
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import time
import logging

from .container import container
from .router_layer.proxy_router import ProxyRouter
from .router_layer.list_sandbox_router import ListSandboxRouter
from .router_layer.get_sandbox_router import GetSandboxRouter
from .router_layer.create_sandbox_router import CreateSandboxRouter
from .router_layer.destroy_sandbox_router import DestroySandboxRouter
from .exceptions import EngineError

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="Echo Agentic Engine",
    description="沙箱隔离的 OpenCode 代理引擎",
    version="1.0.0"
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    return response


# 异常处理中间件
@app.exception_handler(EngineError)
async def engine_error_handler(request: Request, exc: EngineError):
    """处理 EngineError 异常"""
    return container.response_builder.handleException(exc)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理通用异常"""
    logger.exception(f"Unhandled exception: {exc}")
    return container.response_builder.handleException(exc)


# ==================== 业务代理接口 ====================

# Router 实例
proxy_router = ProxyRouter()
list_sandbox_router = ListSandboxRouter()
get_sandbox_router = GetSandboxRouter()
create_sandbox_router = CreateSandboxRouter()
destroy_sandbox_router = DestroySandboxRouter()


@app.api_route("/trans/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_request(path: str, request: Request):
    """
    OpenCode API 代理接口

    流程: 3.2.1 - OpenCode API 代理主流程

    将请求透传到沙箱内 OpenCode Serve，自动处理沙箱创建、健康检查、故障恢复
    """
    return await proxy_router.handleProxyRequest(path, request)


# ==================== 健康检查接口 ====================

@app.get("/health")
async def health_check():
    """Engine 健康检查接口"""
    return {"status": "healthy", "service": "echo-agentic-engine"}


# ==================== 管理接口 ====================

@app.post("/admin/sandbox/list")
async def list_sandboxes(request: Request):
    """
    列出所有沙箱

    流程: 3.2.2 - 管理接口：列出所有沙箱
    """
    return await list_sandbox_router.handleListSandboxes(request)


@app.post("/admin/sandbox/get")
async def get_sandbox(request: Request):
    """
    查询单个沙箱

    流程: 3.2.3 - 管理接口：查询单个沙箱
    """
    return await get_sandbox_router.handleGetSandbox(request)


@app.post("/admin/sandbox/create")
async def create_sandbox(request: Request):
    """
    创建沙箱

    流程: 3.2.4 - 管理接口：创建沙箱
    """
    return await create_sandbox_router.handleCreateSandbox(request)


@app.post("/admin/sandbox/destroy")
async def destroy_sandbox(request: Request):
    """
    销毁沙箱

    流程: 3.2.5 - 管理接口：销毁沙箱
    """
    return await destroy_sandbox_router.handleDestroySandbox(request)


# ==================== 启动事件 ====================

@app.on_event("startup")
async def startup_event():
    """
    应用启动事件

    流程: 3.2.6 - Engine 启动主流程
    """
    logger.info("Echo Agentic Engine starting...")

    # 1. 先加载本地配置文件（获取 Redis 连接信息）
    logger.info("Loading configuration from file...")
    from .core_layer.config_models import Config
    config = Config()

    # 从配置文件加载
    import json
    import os
    config_file = "config.json"
    search_paths = [
        config_file,
        os.path.join(os.getcwd(), config_file),
    ]

    file_data = None
    for path in search_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                logger.info(f"Configuration file loaded: {path}")
                break
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load config file {path}: {e}")
                continue

    # 应用配置文件的 Redis 配置
    if file_data:
        if "redis" in file_data:
            redis_conf = file_data["redis"]
            config.redisHost = redis_conf.get("host", "localhost")
            config.redisPort = redis_conf.get("port", 6379)
            config.redisPassword = redis_conf.get("password", "")
            config.redisDB = redis_conf.get("db", 0)

        if "nas" in file_data:
            config.nasRootPath = file_data["nas"].get("rootPath", "/nas")

        if "engine" in file_data:
            config.enginePort = file_data["engine"].get("port", 8000)
            config.maxSandboxes = file_data["engine"].get("maxSandboxes", 50)

        if "sandbox" in file_data:
            sandbox_conf = file_data["sandbox"]
            config.idleTimeout = sandbox_conf.get("idleTimeout", 3600)

        if "tasks" in file_data:
            tasks_conf = file_data["tasks"]
            config.healthCheckInterval = tasks_conf.get("healthCheckInterval", 30)
            config.idleCheckInterval = tasks_conf.get("idleCheckInterval", 60)
            config.configSyncInterval = tasks_conf.get("configSyncInterval", 300)
            config.healthCheckTimeout = tasks_conf.get("healthCheckTimeout", 5)
            config.maxRetries = tasks_conf.get("maxRetries", 3)

    # 2. 配置 Redis 客户端并连接
    logger.info(f"Connecting to Redis at {config.redisHost}:{config.redisPort}...")
    container.redis_client.configure(
        host=config.redisHost,
        port=config.redisPort,
        password=config.redisPassword,
        db=config.redisDB
    )
    if container.redis_client.connectRedis():
        logger.info("Redis connected successfully")
    else:
        logger.warning("Redis connection failed, running in standalone mode")

    # 3. 加载完整配置（从 Redis 覆盖）
    config = container.config_manager.loadConfig()
    logger.info(f"Configuration loaded: enginePort={config.enginePort}, maxSandboxes={config.maxSandboxes}, nasRootPath={config.nasRootPath}")

    # 4. 配置各模块
    container.port_allocator.configure(config.portRange.min, config.portRange.max)
    container.nas_manager.configure(config.nasRootPath)
    container.bubblewrap_launcher.configure(config.openCodeCommand)
    container.health_checker.configure(config.healthCheckTimeout)
    container.request_proxy.configure(config.maxRetries * 60)

    # 5. 注册并启动后台任务
    from .background_tasks.health_check_task import HealthCheckTask
    from .background_tasks.idle_cleanup_task import IdleCleanupTask
    from .background_tasks.config_sync_task import ConfigSyncTask

    container.task_scheduler.registerTask(HealthCheckTask(), config.healthCheckInterval)
    container.task_scheduler.registerTask(IdleCleanupTask(), config.idleCheckInterval)
    container.task_scheduler.registerTask(ConfigSyncTask(), config.configSyncInterval)

    container.task_scheduler.startScheduler()
    logger.info("Background tasks started")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("Echo Agentic Engine shutting down...")

    # 停止后台任务
    container.task_scheduler.stopScheduler()
    logger.info("Background tasks stopped")
