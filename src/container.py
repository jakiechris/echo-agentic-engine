"""
依赖注入容器

管理各模块的单例实例和依赖关系
"""

from typing import Optional, Dict, Any


class Container:
    """依赖注入容器"""

    _instance: Optional['Container'] = None

    def __new__(cls) -> 'Container':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # 配置对象
        self._config: Any = None

        # 基础设施层 - 延迟导入
        self._redis_client: Any = None
        self._port_allocator: Any = None
        self._nas_manager: Any = None
        self._bubblewrap_launcher: Any = None

        # 监控层 - 延迟导入
        self._health_checker: Any = None
        self._resource_monitor: Any = None
        self._idle_monitor: Any = None
        self._log_reader: Any = None

        # 核心层 - 延迟导入
        self._sandbox_manager: Any = None
        self._request_proxy: Any = None
        self._config_manager: Any = None

        # API 层 - 延迟导入
        self._request_validator: Any = None
        self._response_builder: Any = None

        # 启动层 - 延迟导入
        self._task_scheduler: Any = None

        # 沙箱存储 (内存中的沙箱实例)
        self._sandboxes: Dict[str, Any] = {}  # key: f"{domainID}:{sandboxID}", value: Sandbox

    # ============ 配置 ============

    @property
    def config(self) -> Any:
        if self._config is None:
            from .core_layer.config_models import Config
            self._config = Config()
        return self._config

    def set_config(self, config: Any):
        self._config = config

    # ============ 基础设施层 ============

    @property
    def redis_client(self) -> Any:
        if self._redis_client is None:
            from .infrastructure_layer.redis_client import RedisClient
            self._redis_client = RedisClient()
        return self._redis_client

    @property
    def port_allocator(self) -> Any:
        if self._port_allocator is None:
            from .infrastructure_layer.port_allocator import PortAllocator
            self._port_allocator = PortAllocator()
        return self._port_allocator

    @property
    def nas_manager(self) -> Any:
        if self._nas_manager is None:
            from .infrastructure_layer.nas_manager import NasManager
            self._nas_manager = NasManager()
        return self._nas_manager

    @property
    def bubblewrap_launcher(self) -> Any:
        if self._bubblewrap_launcher is None:
            from .infrastructure_layer.bubblewrap_launcher import BubblewrapLauncher
            self._bubblewrap_launcher = BubblewrapLauncher()
        return self._bubblewrap_launcher

    # ============ 监控层 ============

    @property
    def health_checker(self) -> Any:
        if self._health_checker is None:
            from .monitoring_layer.health_checker import HealthChecker
            self._health_checker = HealthChecker()
        return self._health_checker

    @property
    def resource_monitor(self) -> Any:
        if self._resource_monitor is None:
            from .monitoring_layer.resource_monitor import ResourceMonitor
            self._resource_monitor = ResourceMonitor()
        return self._resource_monitor

    @property
    def idle_monitor(self) -> Any:
        if self._idle_monitor is None:
            from .monitoring_layer.idle_monitor import IdleMonitor
            self._idle_monitor = IdleMonitor()
        return self._idle_monitor

    @property
    def log_reader(self) -> Any:
        if self._log_reader is None:
            from .monitoring_layer.log_reader import LogReader
            self._log_reader = LogReader()
        return self._log_reader

    # ============ 核心层 ============

    @property
    def sandbox_manager(self) -> Any:
        if self._sandbox_manager is None:
            from .core_layer.sandbox_manager import SandboxManager
            self._sandbox_manager = SandboxManager()
        return self._sandbox_manager

    @property
    def request_proxy(self) -> Any:
        if self._request_proxy is None:
            from .core_layer.request_proxy import RequestProxy
            self._request_proxy = RequestProxy()
        return self._request_proxy

    @property
    def config_manager(self) -> Any:
        if self._config_manager is None:
            from .core_layer.config_manager import ConfigManager
            self._config_manager = ConfigManager()
        return self._config_manager

    # ============ API 层 ============

    @property
    def request_validator(self) -> Any:
        if self._request_validator is None:
            from .api_layer.request_validator import RequestValidator
            self._request_validator = RequestValidator()
        return self._request_validator

    @property
    def response_builder(self) -> Any:
        if self._response_builder is None:
            from .api_layer.response_builder import ResponseBuilder
            self._response_builder = ResponseBuilder()
        return self._response_builder

    # ============ 启动层 ============

    @property
    def task_scheduler(self) -> Any:
        if self._task_scheduler is None:
            from .bootstrap_layer.task_scheduler import TaskScheduler
            self._task_scheduler = TaskScheduler()
        return self._task_scheduler

    # ============ 沙箱存储 ============

    def get_sandbox_from_memory(self, domainID: str, sandboxID: str) -> Any:
        """从内存获取沙箱实例"""
        key = f"{domainID}:{sandboxID}"
        return self._sandboxes.get(key)

    def set_sandbox_to_memory(self, sandbox: Any):
        """将沙箱实例存入内存"""
        key = f"{sandbox.domainID}:{sandbox.sandboxID}"
        self._sandboxes[key] = sandbox

    def remove_sandbox_from_memory(self, domainID: str, sandboxID: str):
        """从内存移除沙箱实例"""
        key = f"{domainID}:{sandboxID}"
        if key in self._sandboxes:
            del self._sandboxes[key]

    def get_all_sandboxes_from_memory(self) -> list:
        """获取所有沙箱实例"""
        return list(self._sandboxes.values())

    def count_sandboxes(self) -> int:
        """获取沙箱数量"""
        return len(self._sandboxes)


# 全局容器实例
container = Container()