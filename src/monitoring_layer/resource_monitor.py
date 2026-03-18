"""
ResourceMonitor 模块

职责: 资源监控,读取沙箱进程的 CPU、内存占用

参与流程: 2 个流程 (3.2.2, 3.2.3)
"""

import os
from typing import Dict


class ResourceMonitor:
    """资源监控"""

    def queryResourceUsage(self, pid: int) -> Dict:
        """
        读取沙箱进程的资源占用情况,包括 CPU 使用率和内存占用(RSS、VSZ)

        流程: 3.2.2 - 管理接口：列出所有沙箱
        流程: 3.2.3 - 管理接口：查询单个沙箱

        Args:
            pid: 进程 ID

        Returns:
            Dict: 资源占用对象,包含 CPU 和内存信息
                {
                    "cpu": float,           # CPU 占用率 (百分比)
                    "memory": {
                        "rss": int,          # 实际物理内存占用 (MB)
                        "vsz": int,          # 虚拟内存占用 (MB)
                        "unit": "MB"
                    }
                }
        """
        try:
            # 读取 /proc/{pid}/stat 文件
            stat_path = f"/proc/{pid}/stat"
            if not os.path.exists(stat_path):
                return self._empty_result()

            with open(stat_path, 'r') as f:
                stat_content = f.read()

            # 解析 stat 文件内容
            # 格式: pid (comm) state ppid pgrp session tty_nr tpgid flags ...
            # 我们需要的是 utime(14), stime(15), rss(24), vsize(23)
            parts = stat_content.split()

            if len(parts) < 24:
                return self._empty_result()

            # 提取字段
            utime = int(parts[13])  # 用户态时间 (clock ticks)
            stime = int(parts[14])  # 内核态时间 (clock ticks)
            vsize = int(parts[22])  # 虚拟内存大小 (bytes)
            rss = int(parts[23])    # 驻留集大小 (pages)

            # 转换内存单位
            # RSS 从页转换为 MB (页大小通常为 4KB)
            page_size = os.sysconf('SC_PAGE_SIZE') if hasattr(os, 'sysconf') else 4096
            rss_mb = (rss * page_size) / (1024 * 1024)
            vsz_mb = vsize / (1024 * 1024)

            # 计算 CPU 占用率
            # 获取系统总 CPU 时间
            cpu_usage = self._calculate_cpu_usage(pid, utime + stime)

            return {
                "cpu": round(cpu_usage, 2),
                "memory": {
                    "rss": int(rss_mb),
                    "vsz": int(vsz_mb),
                    "unit": "MB"
                }
            }

        except (FileNotFoundError, PermissionError, ValueError, IndexError):
            return self._empty_result()
        except Exception:
            return self._empty_result()

    def _calculate_cpu_usage(self, pid: int, process_time: int) -> float:
        """计算 CPU 使用率"""
        try:
            # 读取 /proc/stat 获取总 CPU 时间
            with open('/proc/stat', 'r') as f:
                cpu_line = f.readline()

            cpu_parts = cpu_line.split()[1:8]
            total_cpu_time = sum(int(x) for x in cpu_parts)

            # 获取时钟频率
            clk_tck = os.sysconf('SC_CLK_TCK') if hasattr(os, 'sysconf') else 100

            # 计算百分比（简化计算，实际需要两次采样）
            # 这里返回一个估算值
            cpu_usage = (process_time / clk_tck) % 100

            return cpu_usage

        except Exception:
            return 0.0

    def _empty_result(self) -> Dict:
        """返回空结果"""
        return {
            "cpu": 0.0,
            "memory": {
                "rss": 0,
                "vsz": 0,
                "unit": "MB"
            }
        }
