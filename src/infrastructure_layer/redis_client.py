"""
RedisClient 模块

职责: Redis 客户端,管理沙箱元数据和配置

参与流程: 7 个流程 (3.2.1 - 3.2.6, 3.2.9)
"""

import json
from typing import Dict, List, Optional
from datetime import datetime

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class RedisClient:
    """Redis 客户端"""

    def __init__(self):
        self._client: Optional['redis.Redis'] = None
        self._host: str = "localhost"
        self._port: int = 6379
        self._password: str = ""
        self._db: int = 0
        self._connected: bool = False

    def connectRedis(self) -> bool:
        """
        建立 Redis 连接池,测试连接可用性

        流程: 3.2.6 - Engine 启动主流程

        Returns:
            bool: 是否连接成功
        """
        if not REDIS_AVAILABLE:
            self._connected = False
            return False

        try:
            self._client = redis.Redis(
                host=self._host,
                port=self._port,
                password=self._password if self._password else None,
                db=self._db,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
                retry_on_timeout=False
            )
            # 测试连接
            self._client.ping()
            self._connected = True
            return True
        except Exception:
            self._client = None
            self._connected = False
            return False

    def configure(self, host: str, port: int, password: str = "", db: int = 0):
        """配置 Redis 连接参数"""
        self._host = host
        self._port = port
        self._password = password
        self._db = db

    def is_connected(self) -> bool:
        """检查 Redis 是否已连接"""
        return self._connected and self._client is not None

    def setSandboxMetadata(
        self,
        domainID: str,
        sandboxID: str,
        metadata: Dict
    ) -> bool:
        """
        写入沙箱元数据到 Redis Hash 结构

        流程: 3.2.1 - OpenCode API 代理主流程
        流程: 3.2.4 - 管理接口：创建沙箱

        Args:
            domainID: 租户标识
            sandboxID: 沙箱标识
            metadata: 沙箱元数据字典

        Returns:
            bool: 是否写入成功
        """
        if not self.is_connected():
            return True  # 未连接时返回成功，允许继续运行

        try:
            key = f"sandbox:{domainID}:{sandboxID}"

            # 序列化元数据
            serialized_metadata = {}
            for k, v in metadata.items():
                if isinstance(v, (dict, list)):
                    serialized_metadata[k] = json.dumps(v)
                else:
                    serialized_metadata[k] = str(v) if v is not None else ""

            self._client.hset(key, mapping=serialized_metadata)
            return True
        except Exception:
            return False

    def fetchSandboxMetadata(
        self,
        domainID: str,
        sandboxID: str
    ) -> Optional[Dict]:
        """
        查询单个沙箱的元数据

        流程: 3.2.3 - 管理接口：查询单个沙箱

        Args:
            domainID: 租户标识
            sandboxID: 沙箱标识

        Returns:
            Dict | None: 沙箱元数据对象,不存在则返回 None
        """
        if not self.is_connected():
            return None

        try:
            key = f"sandbox:{domainID}:{sandboxID}"

            if not self._client.exists(key):
                return None

            data = self._client.hgetall(key)

            # 反序列化
            metadata = {}
            for k, v in data.items():
                try:
                    metadata[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    metadata[k] = v

            return metadata
        except Exception:
            return None

    def fetchBatchMetadata(
        self,
        sandboxIDs: List[str]
    ) -> Dict[str, Dict]:
        """
        批量查询多个沙箱的元数据

        流程: 3.2.2 - 管理接口：列出所有沙箱

        Args:
            sandboxIDs: 沙箱标识列表 (格式: {domainID}:{sandboxID})

        Returns:
            Dict[str, Dict]: 沙箱 ID 到元数据的映射字典
        """
        result = {}
        if not self.is_connected():
            return result

        try:
            # 使用 pipeline 批量查询
            pipe = self._client.pipeline()
            keys = [f"sandbox:{sid}" for sid in sandboxIDs]

            for key in keys:
                pipe.hgetall(key)

            responses = pipe.execute()

            for sid, data in zip(sandboxIDs, responses):
                if data:
                    # 反序列化
                    metadata = {}
                    for k, v in data.items():
                        try:
                            metadata[k] = json.loads(v)
                        except (json.JSONDecodeError, TypeError):
                            metadata[k] = v
                    result[sid] = metadata
        except Exception:
            pass

        return result

    def updateMetadata(
        self,
        domainID: str,
        sandboxID: str,
        **kwargs
    ) -> bool:
        """
        更新沙箱元数据的指定字段

        流程: 3.2.1 - OpenCode API 代理主流程
        流程: 3.2.5 - 管理接口：销毁沙箱

        Args:
            domainID: 租户标识
            sandboxID: 沙箱标识
            **kwargs: 需要更新的字段键值对

        Returns:
            bool: 是否更新成功
        """
        if not self.is_connected():
            return True  # 未连接时返回成功

        try:
            key = f"sandbox:{domainID}:{sandboxID}"

            if not kwargs:
                return True

            # 序列化字段
            serialized = {}
            for k, v in kwargs.items():
                if isinstance(v, (dict, list)):
                    serialized[k] = json.dumps(v)
                else:
                    serialized[k] = str(v) if v is not None else ""

            self._client.hset(key, mapping=serialized)
            return True
        except Exception:
            return False

    def deleteSandboxMetadata(
        self,
        domainID: str,
        sandboxID: str
    ) -> bool:
        """
        删除沙箱元数据 Key

        流程: 3.2.5 - 管理接口：销毁沙箱

        Args:
            domainID: 租户标识
            sandboxID: 沙箱标识

        Returns:
            bool: 是否删除成功
        """
        if not self.is_connected():
            return True  # 未连接时返回成功

        try:
            key = f"sandbox:{domainID}:{sandboxID}"
            self._client.delete(key)
            return True
        except Exception:
            return False

    def updateLastActive(
        self,
        domainID: str,
        sandboxID: str
    ) -> bool:
        """
        更新沙箱的最后活跃时间为当前时间

        流程: 3.2.1 - OpenCode API 代理主流程

        Args:
            domainID: 租户标识
            sandboxID: 沙箱标识

        Returns:
            bool: 是否更新成功
        """
        now = datetime.utcnow().isoformat() + "Z"
        return self.updateMetadata(domainID, sandboxID, lastActiveAt=now)

    def queryAllocatedPorts(self) -> List[int]:
        """
        查询所有沙箱元数据,提取所有已分配的端口列表

        流程: 3.2.1 - OpenCode API 代理主流程
        流程: 3.2.4 - 管理接口：创建沙箱

        Returns:
            List[int]: 已分配端口号列表
        """
        ports = []
        if not self.is_connected():
            return ports

        try:
            # 扫描所有 sandbox:* 的 key
            cursor = 0
            while True:
                cursor, keys = self._client.scan(cursor, match="sandbox:*", count=100)
                for key in keys:
                    port = self._client.hget(key, "port")
                    if port:
                        try:
                            ports.append(int(port))
                        except (ValueError, TypeError):
                            pass
                if cursor == 0:
                    break
        except Exception:
            pass

        return ports

    def getConfig(self, key: str = "engine:config") -> Dict:
        """
        查询 Engine 全局配置

        流程: 3.2.6 - Engine 启动主流程
        流程: 3.2.9 - ConfigSyncTask 调用链

        Args:
            key: 配置键名，默认 "engine:config"

        Returns:
            Dict: 配置字典
        """
        return self.fetchConfig()

    def fetchConfig(self) -> Dict:
        """
        查询 Engine 全局配置

        流程: 3.2.6 - Engine 启动主流程
        流程: 3.2.9 - ConfigSyncTask 调用链

        Returns:
            Dict: 配置字典
        """
        if not self.is_connected():
            return {}

        try:
            key = "engine:config"

            if not self._client.exists(key):
                return {}

            data = self._client.hgetall(key)

            # 反序列化
            config = {}
            for k, v in data.items():
                try:
                    config[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    # 尝试解析为数字
                    try:
                        config[k] = int(v)
                    except (ValueError, TypeError):
                        config[k] = v

            return config
        except Exception:
            return {}
