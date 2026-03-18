"""
异常定义模块

定义 Engine 中使用的所有自定义异常
"""


class EngineError(Exception):
    """Engine 基础异常"""

    def __init__(self, code: str, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ValidationError(EngineError):
    """验证错误异常"""

    def __init__(self, code: str, message: str, details: dict = None):
        super().__init__(code, message, details)


class SandboxUnavailableError(EngineError):
    """沙箱不可用异常"""

    def __init__(self, message: str, domainID: str = None, sandboxID: str = None):
        details = {}
        if domainID:
            details["domainID"] = domainID
        if sandboxID:
            details["sandboxID"] = sandboxID
        super().__init__("SANDBOX_UNAVAILABLE", message, details)


class SandboxTimeoutError(EngineError):
    """沙箱超时异常"""

    def __init__(self, message: str, domainID: str = None, sandboxID: str = None):
        details = {}
        if domainID:
            details["domainID"] = domainID
        if sandboxID:
            details["sandboxID"] = sandboxID
        super().__init__("SANDBOX_TIMEOUT", message, details)


class SandboxNotFoundError(EngineError):
    """沙箱不存在异常"""

    def __init__(self, domainID: str, sandboxID: str):
        super().__init__(
            "SANDBOX_NOT_FOUND",
            "沙箱不存在",
            {"domainID": domainID, "sandboxID": sandboxID}
        )


class SandboxAlreadyExistsError(EngineError):
    """沙箱已存在异常"""

    def __init__(self, domainID: str, sandboxID: str):
        super().__init__(
            "SANDBOX_ALREADY_EXISTS",
            "沙箱已存在",
            {"domainID": domainID, "sandboxID": sandboxID}
        )


class PortAllocationError(EngineError):
    """端口分配异常"""

    def __init__(self, message: str = "端口分配失败，无可用端口"):
        super().__init__("PORT_ALLOCATION_FAILED", message, {})


class NasPreparationError(EngineError):
    """NAS 目录准备异常"""

    def __init__(self, message: str, nasPath: str = None):
        details = {"nasPath": nasPath} if nasPath else {}
        super().__init__("NAS_PREPARATION_FAILED", message, details)


class BubblewrapStartError(EngineError):
    """Bubblewrap 启动异常"""

    def __init__(self, message: str, nasPath: str = None, port: int = None):
        details = {}
        if nasPath:
            details["nasPath"] = nasPath
        if port:
            details["port"] = port
        super().__init__("BUBBLEWRAP_START_FAILED", message, details)


class ProcessKillError(EngineError):
    """进程终止异常"""

    def __init__(self, pid: int, message: str = None):
        super().__init__(
            "PROCESS_KILL_FAILED",
            message or f"进程终止失败: PID {pid}",
            {"pid": pid}
        )


class RedisConnectionError(EngineError):
    """Redis 连接异常"""

    def __init__(self, message: str = "Redis 连接失败"):
        super().__init__("REDIS_CONNECTION_FAILED", message, {})
