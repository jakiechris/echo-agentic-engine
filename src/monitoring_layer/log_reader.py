"""
LogReader 模块

职责: 日志读取,读取沙箱内 OpenCode 的日志文件

参与流程: 1 个流程 (3.2.3)
"""

import os
from typing import List


class LogReader:
    """日志读取"""

    # 默认日志文件路径
    DEFAULT_LOG_FILE = "defaultProject/logs/opencode.log"

    def readLogs(self, nasPath: str, limit: int = 50) -> List[str]:
        """
        读取沙箱内 OpenCode 的日志文件,返回最近 N 行日志内容

        流程: 3.2.3 - 管理接口：查询单个沙箱

        Args:
            nasPath: NAS 目录路径
            limit: 返回日志行数,默认 50

        Returns:
            List[str]: 日志行列表,按时间倒序
        """
        # 构建日志文件路径
        log_path = os.path.join(nasPath, self.DEFAULT_LOG_FILE)

        # 检查文件是否存在
        if not os.path.exists(log_path):
            return []

        try:
            # 读取文件末尾 N 行
            logs = self._tail_file(log_path, limit)
            return logs

        except (IOError, PermissionError):
            return []

    def _tail_file(self, file_path: str, n: int) -> List[str]:
        """
        读取文件末尾 N 行

        Args:
            file_path: 文件路径
            n: 行数

        Returns:
            List[str]: 文件行列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # 使用 deque 实现高效的尾部读取
                from collections import deque
                lines = deque(f, maxlen=n)
                return list(lines)
        except Exception:
            return []
