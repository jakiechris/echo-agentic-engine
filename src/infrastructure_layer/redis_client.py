"""
RedisClient 模块

职责: Redis 客户端,管理引擎信息和沙箱信息的两张表
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
                socket_timeout=2
            )
            # 测试连接
            self._client.ping()
            self._connected = True
            return True
        except Exception as e:
            print(f"Redis connection error: {e}")
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

    # ==================== 引擎信息表操作 ====================

    def setEngineInfo(
        self,
        engine_url: str,
        max_sandboxes: int,
        used_sandboxes: int,
        timestamp: str
    ) -> bool:
        """
        写入引擎信息到 Redis Hash

        Args:
            engine_url: 引擎完整URL (如 http://ip:8000/trans)
            max_sandboxes: 支持的最大沙箱数量
            used_sandboxes: 当前已使用的沙箱数量
            timestamp: 当前时间戳

        Returns:
            bool: 是否写入成功
        """
        if not self.is_connected():
            return True

        try:
            key = f"engine:{engine_url}"

            self._client.hset(key, mapping={
                "engineUrl": engine_url,
                "maxSandboxes": str(max_sandboxes),
                "usedSandboxes": str(used_sandboxes),
                "timestamp": timestamp
            })
            return True
        except Exception:
            return False

    def getEngineInfo(self, engine_url: str) -> Optional[Dict]:
        """
        查询引擎信息

        Args:
            engine_url: 引擎完整URL

        Returns:
            Dict | None: 引擎信息
        """
        if not self.is_connected():
            return None

        try:
            key = f"engine:{engine_url}"

            if not self._client.exists(key):
                return None

            data = self._client.hgetall(key)

            return {
                "engineUrl": data.get("engineUrl"),
                "maxSandboxes": int(data.get("maxSandboxes", 0)),
                "usedSandboxes": int(data.get("usedSandboxes", 0)),
                "timestamp": data.get("timestamp")
            }
        except Exception:
            return None

    def getAllEngines(self) -> List[Dict]:
        """
        获取所有引擎信息

        Returns:
            List[Dict]: 引擎信息列表
        """
        engines = []
        if not self.is_connected():
            return engines

        try:
            cursor = 0
            while True:
                cursor, keys = self._client.scan(cursor, match="engine:*", count=100)
                for key in keys:
                    data = self._client.hgetall(key)
                    if data:
                        engines.append({
                            "engineUrl": data.get("engineUrl"),
                            "maxSandboxes": int(data.get("maxSandboxes", 0)),
                            "usedSandboxes": int(data.get("usedSandboxes", 0)),
                            "timestamp": data.get("timestamp")
                        })
                if cursor == 0:
                    break
        except Exception:
            pass

        return engines

    def deleteEngineInfo(self, engine_url: str) -> bool:
        """
        删除引擎信息

        Args:
            engine_url: 引擎完整URL

        Returns:
            bool: 是否删除成功
        """
        if not self.is_connected():
            return True

        try:
            key = f"engine:{engine_url}"
            self._client.delete(key)
            return True
        except Exception:
            return False

    # ==================== 沙箱信息表操作 ====================

    def setSandboxInfo(
        self,
        domain_id: str,
        sandbox_id: str,
        engine_url: str,
        timestamp: str,
        last_request_time: str
    ) -> bool:
        """
        写入沙箱信息到 Redis Hash

        Args:
            domain_id: 租户标识
            sandbox_id: 沙箱标识
            engine_url: 所属引擎完整URL
            timestamp: 当前时间戳
            last_request_time: 最近一次请求处理完成时间

        Returns:
            bool: 是否写入成功
        """
        if not self.is_connected():
            return True

        try:
            key = f"sandbox:{domain_id}:{sandbox_id}"

            self._client.hset(key, mapping={
                "domainID": domain_id,
                "sandboxID": sandbox_id,
                "engineUrl": engine_url,
                "timestamp": timestamp,
                "lastRequestTime": last_request_time
            })
            return True
        except Exception:
            return False

    def getSandboxInfo(self, domain_id: str, sandbox_id: str) -> Optional[Dict]:
        """
        查询单个沙箱信息

        Args:
            domain_id: 租户标识
            sandbox_id: 沙箱标识

        Returns:
            Dict | None: 沙箱信息
        """
        if not self.is_connected():
            return None

        try:
            key = f"sandbox:{domain_id}:{sandbox_id}"

            if not self._client.exists(key):
                return None

            data = self._client.hgetall(key)

            return {
                "domainID": data.get("domainID"),
                "sandboxID": data.get("sandboxID"),
                "engineUrl": data.get("engineUrl"),
                "timestamp": data.get("timestamp"),
                "lastRequestTime": data.get("lastRequestTime")
            }
        except Exception:
            return None

    def getSandboxesByEngine(self, engine_url: str) -> List[Dict]:
        """
        查询指定引擎的所有沙箱

        Args:
            engine_url: 引擎完整URL

        Returns:
            List[Dict]: 沙箱信息列表
        """
        sandboxes = []
        if not self.is_connected():
            return sandboxes

        try:
            cursor = 0
            while True:
                cursor, keys = self._client.scan(cursor, match="sandbox:*", count=100)
                for key in keys:
                    data = self._client.hgetall(key)
                    if data and data.get("engineUrl") == engine_url:
                        sandboxes.append({
                            "domainID": data.get("domainID"),
                            "sandboxID": data.get("sandboxID"),
                            "engineUrl": data.get("engineUrl"),
                            "timestamp": data.get("timestamp"),
                            "lastRequestTime": data.get("lastRequestTime")
                        })
                if cursor == 0:
                    break
        except Exception:
            pass

        return sandboxes

    def getAllSandboxes(self) -> List[Dict]:
        """
        获取所有沙箱信息

        Returns:
            List[Dict]: 沙箱信息列表
        """
        sandboxes = []
        if not self.is_connected():
            return sandboxes

        try:
            cursor = 0
            while True:
                cursor, keys = self._client.scan(cursor, match="sandbox:*", count=100)
                for key in keys:
                    data = self._client.hgetall(key)
                    if data:
                        sandboxes.append({
                            "domainID": data.get("domainID"),
                            "sandboxID": data.get("sandboxID"),
                            "engineUrl": data.get("engineUrl"),
                            "timestamp": data.get("timestamp"),
                            "lastRequestTime": data.get("lastRequestTime")
                        })
                if cursor == 0:
                    break
        except Exception:
            pass

        return sandboxes

    def deleteSandboxInfo(self, domain_id: str, sandbox_id: str) -> bool:
        """
        删除沙箱信息

        Args:
            domain_id: 租户标识
            sandbox_id: 沙箱标识

        Returns:
            bool: 是否删除成功
        """
        if not self.is_connected():
            return True

        try:
            key = f"sandbox:{domain_id}:{sandbox_id}"
            self._client.delete(key)
            return True
        except Exception:
            return False

    def updateSandboxLastRequest(
        self,
        domain_id: str,
        sandbox_id: str,
        last_request_time: str
    ) -> bool:
        """
        更新沙箱的最后请求时间

        Args:
            domain_id: 租户标识
            sandbox_id: 沙箱标识
            last_request_time: 最近一次请求处理完成时间

        Returns:
            bool: 是否更新成功
        """
        if not self.is_connected():
            return True

        try:
            key = f"sandbox:{domain_id}:{sandbox_id}"
            timestamp = datetime.utcnow().isoformat() + "Z"

            self._client.hset(key, mapping={
                "timestamp": timestamp,
                "lastRequestTime": last_request_time
            })
            return True
        except Exception:
            return False

    # ==================== 兼容旧接口 ====================

    def queryAllocatedPorts(self) -> List[int]:
        """
        查询所有沙箱元数据,提取所有已分配的端口列表 (兼容旧接口)

        Returns:
            List[int]: 已分配端口号列表
        """
        # 从内存中的沙箱管理器获取，不从Redis获取
        return []
