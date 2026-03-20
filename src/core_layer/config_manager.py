"""
ConfigManager 模块

职责: 配置管理,从本地配置文件和 Redis 加载和管理 Engine 配置

参与流程: 2 个流程 (3.2.6, 3.2.9)
"""

import json
import os
from typing import Any, Dict

from ..container import container
from .config_models import Config, PortRange


# 默认配置文件路径
DEFAULT_CONFIG_FILE = "config.json"


class ConfigManager:
    """配置管理"""

    def __init__(self):
        self._config: Config = None
        self._config_file: str = DEFAULT_CONFIG_FILE

    def setConfigFile(self, filepath: str):
        """设置配置文件路径"""
        self._config_file = filepath

    def loadConfig(self) -> Config:
        """
        从本地配置文件和 Redis 读取配置，验证配置项合法性

        加载顺序：
        1. 使用内置默认值创建配置
        2. 从本地配置文件加载（覆盖默认值）
        3. 从 Redis 加载（覆盖本地配置）

        流程: 3.2.6 - Engine 启动主流程

        Returns:
            Config: 配置对象
        """
        # 使用默认值创建配置
        config = Config()

        # 从本地配置文件加载
        self._loadFromFile(config)

        # 不再从Redis读取配置，所有配置在config.json中
        # redis_config = container.redis_client.fetchConfig()
        # if redis_config:
        #     self._applyRedisConfig(config, redis_config)

        # 验证配置合法性
        self._validate_config(config)

        # 保存到内存
        self._config = config

        return config

    def _loadFromFile(self, config: Config):
        """从本地配置文件加载配置"""
        # 查找配置文件
        config_path = self._config_file

        # 尝试多个路径
        search_paths = [
            config_path,
            os.path.join(os.getcwd(), config_path),
            os.path.join(os.path.dirname(__file__), "..", "..", config_path)
        ]

        file_data = None
        for path in search_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                    break
                except (json.JSONDecodeError, IOError):
                    continue

        if not file_data:
            return

        # 应用 Redis 配置
        if "redis" in file_data:
            redis_conf = file_data["redis"]
            config.redisHost = redis_conf.get("host", config.redisHost)
            config.redisPort = redis_conf.get("port", config.redisPort)
            config.redisPassword = redis_conf.get("password", config.redisPassword)
            config.redisDB = redis_conf.get("db", config.redisDB)

        # 应用 NAS 配置
        if "nas" in file_data:
            nas_conf = file_data["nas"]
            config.nasRootPath = nas_conf.get("rootPath", config.nasRootPath)

        # 应用 Engine 配置
        if "engine" in file_data:
            engine_conf = file_data["engine"]
            config.enginePort = engine_conf.get("port", config.enginePort)
            config.maxSandboxes = engine_conf.get("maxSandboxes", config.maxSandboxes)
            config.logLevel = engine_conf.get("logLevel", config.logLevel)

        # 应用沙箱配置
        if "sandbox" in file_data:
            sandbox_conf = file_data["sandbox"]
            if "portRange" in sandbox_conf:
                pr = sandbox_conf["portRange"]
                config.portRange = PortRange(
                    min=pr.get("min", 30001),
                    max=pr.get("max", 40000)
                )
            config.idleTimeout = sandbox_conf.get("idleTimeout", config.idleTimeout)
            config.openCodeCommand = sandbox_conf.get("openCodeCommand", config.openCodeCommand)

        # 应用任务配置
        if "tasks" in file_data:
            tasks_conf = file_data["tasks"]
            config.healthCheckInterval = tasks_conf.get("healthCheckInterval", config.healthCheckInterval)
            config.idleCheckInterval = tasks_conf.get("idleCheckInterval", config.idleCheckInterval)
            config.configSyncInterval = tasks_conf.get("configSyncInterval", config.configSyncInterval)
            config.healthCheckTimeout = tasks_conf.get("healthCheckTimeout", config.healthCheckTimeout)
            config.maxRetries = tasks_conf.get("maxRetries", config.maxRetries)

    def _applyRedisConfig(self, config: Config, redis_config: Dict):
        """应用 Redis 配置"""
        if "portRange" in redis_config:
            pr = redis_config["portRange"]
            if isinstance(pr, dict):
                config.portRange = PortRange(
                    min=pr.get("min", 30001),
                    max=pr.get("max", 40000)
                )

        if "idleTimeout" in redis_config:
            config.idleTimeout = int(redis_config["idleTimeout"])

        if "healthCheckInterval" in redis_config:
            config.healthCheckInterval = int(redis_config["healthCheckInterval"])

        if "idleCheckInterval" in redis_config:
            config.idleCheckInterval = int(redis_config["idleCheckInterval"])

        if "configSyncInterval" in redis_config:
            config.configSyncInterval = int(redis_config["configSyncInterval"])

        if "maxRetries" in redis_config:
            config.maxRetries = int(redis_config["maxRetries"])

        if "healthCheckTimeout" in redis_config:
            config.healthCheckTimeout = int(redis_config["healthCheckTimeout"])

        if "maxSandboxes" in redis_config:
            config.maxSandboxes = int(redis_config["maxSandboxes"])

        if "redisHost" in redis_config:
            config.redisHost = str(redis_config["redisHost"])

        if "redisPort" in redis_config:
            config.redisPort = int(redis_config["redisPort"])

        if "redisPassword" in redis_config:
            config.redisPassword = str(redis_config["redisPassword"])

        if "redisDB" in redis_config:
            config.redisDB = int(redis_config["redisDB"])

        if "nasRootPath" in redis_config:
            config.nasRootPath = str(redis_config["nasRootPath"])

        if "enginePort" in redis_config:
            config.enginePort = int(redis_config["enginePort"])

        if "openCodeCommand" in redis_config:
            config.openCodeCommand = str(redis_config["openCodeCommand"])

        if "logLevel" in redis_config:
            config.logLevel = str(redis_config["logLevel"])

        if "logFile" in redis_config:
            config.logFile = str(redis_config["logFile"])

    def _validate_config(self, config: Config):
        """验证配置项合法性"""
        # 验证端口范围
        if config.portRange.min >= config.portRange.max:
            config.portRange.min = 30001
            config.portRange.max = 40000

        if config.portRange.min < 1024:
            config.portRange.min = 30001

        if config.portRange.max > 65535:
            config.portRange.max = 65535

        # 验证超时值
        if config.idleTimeout < 60:
            config.idleTimeout = 60

        if config.healthCheckInterval < 5:
            config.healthCheckInterval = 5

        if config.idleCheckInterval < 10:
            config.idleCheckInterval = 10

        if config.configSyncInterval < 60:
            config.configSyncInterval = 60

        if config.healthCheckTimeout < 1:
            config.healthCheckTimeout = 5

        # 验证最大沙箱数
        if config.maxSandboxes < 1:
            config.maxSandboxes = 1

    def getConfigValue(self, key: str) -> Any:
        """
        获取单个配置项

        流程: 3.2.6 - Engine 启动主流程
        流程: 3.2.9 - ConfigSyncTask 调用链

        Args:
            key: 配置项名称

        Returns:
            Any: 配置值
        """
        if self._config is None:
            return None

        return getattr(self._config, key, None)

    def updateConfig(self, changes: Dict) -> bool:
        """
        更新内存中的配置对象

        流程: 3.2.9 - ConfigSyncTask 调用链

        Args:
            changes: 配置变更字典

        Returns:
            bool: 是否更新成功
        """
        if self._config is None:
            return False

        try:
            for key, value in changes.items():
                if hasattr(self._config, key):
                    setattr(self._config, key, value)

            # 重新验证配置
            self._validate_config(self._config)

            return True
        except Exception:
            return False

    def compareConfig(self, local: Dict, redis: Dict) -> Dict:
        """
        比较本地配置和 Redis 配置，返回差异字段

        流程: 3.2.9 - ConfigSyncTask 调用链

        Args:
            local: 本地配置字典
            redis: Redis 配置字典

        Returns:
            Dict: 差异字段字典（只包含需要更新的新值）
        """
        diff = {}

        # 比较简单字段
        simple_fields = [
            "idleTimeout", "healthCheckInterval", "idleCheckInterval",
            "configSyncInterval", "maxRetries", "healthCheckTimeout",
            "maxSandboxes", "redisHost", "redisPort", "redisPassword",
            "redisDB", "nasRootPath", "enginePort", "openCodeCommand",
            "logLevel", "logFile"
        ]

        for field in simple_fields:
            local_value = local.get(field)
            redis_value = redis.get(field)

            # 转换类型进行比较
            if redis_value is not None:
                try:
                    if isinstance(local_value, int):
                        redis_value = int(redis_value)
                    elif isinstance(local_value, str):
                        redis_value = str(redis_value)
                except (ValueError, TypeError):
                    continue

                if local_value != redis_value:
                    diff[field] = redis_value

        return diff

    @property
    def config(self) -> Config:
        """获取当前配置"""
        if self._config is None:
            self._config = Config()
        return self._config
