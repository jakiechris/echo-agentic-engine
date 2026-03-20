"""
BubblewrapLauncher 模块

职责: Bubblewrap 进程启动,隔离运行 OpenCode Serve

参与流程: 3 个流程 (3.2.1, 3.2.4, 3.2.5)
"""

import os
import signal
import subprocess
import uuid
import time
from typing import Tuple

from ..exceptions import BubblewrapStartError


class BubblewrapLauncher:
    """Bubblewrap 进程启动"""

    # 默认 OpenCode 命令路径
    DEFAULT_OPENCODE_COMMAND = "/usr/local/bin/opencode"

    # 进程退出等待超时（秒）
    KILL_TIMEOUT = 10

    # 健康检查等待超时（秒）
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self):
        self._opencode_command = self.DEFAULT_OPENCODE_COMMAND
        # 存储进程引用
        self._processes: dict = {}  # pid -> subprocess.Popen

    def configure(self, opencode_command: str):
        """配置 OpenCode 命令路径"""
        self._opencode_command = opencode_command

    def launchSandbox(self, domainID: str, sandboxID: str, nasPath: str, port: int) -> Tuple[int, str]:
        """
        构建正确的 Bubblewrap 命令启动沙箱进程，等待进程就绪后返回进程 ID 和密码

        流程: 3.2.1 - OpenCode API 代理主流程
        流程: 3.2.4 - 管理接口：创建沙箱

        Args:
            domainID: 租户标识
            sandboxID: 沙箱标识
            nasPath: NAS 根目录路径（沙箱根目录）
            port: 宿主机端口

        Returns:
            Tuple[int, str]: (pid, password) 进程 ID 和 OpenCode 访问密码 (UUID)

        Raises:
            BubblewrapStartError: 启动失败时抛出
        """
        # 生成随机密码 (UUID)
        password = str(uuid.uuid4())

        # 构建用户数据目录路径
        # nasPath 是沙箱根目录，例如: /data/users/domainID/sandboxID
        data_dir = os.path.join(nasPath, "data")
        config_dir = os.path.join(nasPath, "config")
        workspace_dir = os.path.join(nasPath, "workspace")
        tmp_dir = os.path.join(nasPath, "tmp")

        # 构建 Bubblewrap 命令
        command = [
            "bwrap",
            "--ro-bind", "/usr", "/usr",
            "--ro-bind", "/etc/resolv.conf", "/etc/resolv.conf",
            "--ro-bind", "/etc/ssl", "/etc/ssl",
            "--ro-bind", "/lib", "/lib",
            "--ro-bind", "/lib64", "/lib64",
            "--ro-bind", "/bin", "/bin",
            "--ro-bind", "/sbin", "/sbin",
            "--ro-bind", "/proc", "/proc",
            "--dev", "/dev",
            "--bind", data_dir, "/data",
            "--bind", config_dir, "/config",
            "--bind", workspace_dir, "/workspace",
            "--bind", tmp_dir, "/tmp",
            "--unshare-user",
            "--unshare-pid",
            "--die-with-parent",
            "--new-session",
            "--chdir", "/workspace",
            "--setenv", "PATH", "/usr/local/bin:/usr/bin:/bin",
            "--setenv", "HOME", "/tmp",
            "--setenv", "XDG_DATA_HOME", "/data",
            "--setenv", "XDG_CONFIG_HOME", "/config",
            "--setenv", "XDG_STATE_HOME", "/data/state",
            "--setenv", "XDG_CACHE_HOME", "/data/cache",
            "--",
            self._opencode_command,
            "serve",
            "--hostname=127.0.0.1",
            "--port", str(port)
        ]

        # 设置环境变量
        env = os.environ.copy()
        env["SANDBOX_PORT"] = str(port)

        # 打印 bwrap 命令到日志
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[Bubblewrap] Launching sandbox with command: {' '.join(command)}")

        try:
            # 启动进程
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                preexec_fn=os.setsid,  # 创建新的进程组
                cwd=nasPath
            )

            pid = process.pid
            self._processes[pid] = process

            # 等待进程就绪（健康检查）
            self._wait_for_ready(port, timeout=self.HEALTH_CHECK_TIMEOUT)

            return (pid, password)

        except OSError as e:
            raise BubblewrapStartError(
                f"Bubblewrap 启动失败: {str(e)}",
                nasPath=nasPath,
                port=port
            )
        except Exception as e:
            raise BubblewrapStartError(
                f"沙箱启动异常: {str(e)}",
                nasPath=nasPath,
                port=port
            )

    def _wait_for_ready(self, port: int, timeout: int):
        """等待沙箱进程就绪"""
        import httpx

        start_time = time.time()
        url = f"http://127.0.0.1:{port}/global/health"

        last_error = None
        while time.time() - start_time < timeout:
            try:
                response = httpx.get(url, timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("healthy", False):
                        return
            except Exception as e:
                last_error = e
            time.sleep(1)

        raise BubblewrapStartError(
            f"沙箱健康检查超时: {last_error or 'timeout'}",
            port=port
        )

    def killSandbox(self, pid: int) -> bool:
        """
        终止沙箱进程,先发送 SIGTERM 信号,等待进程退出,若超时未退出则发送 SIGKILL 信号强制终止

        流程: 3.2.5 - 管理接口：销毁沙箱

        Args:
            pid: 沙箱进程 ID

        Returns:
            bool: 是否终止成功
        """
        process = self._processes.get(pid)

        try:
            # 检查进程是否存在
            try:
                os.kill(pid, 0)  # 信号 0 用于检查进程是否存在
            except OSError:
                # 进程不存在
                self._processes.pop(pid, None)
                if process:
                    try:
                        process.wait()  # 回收僵尸进程
                    except:
                        pass
                return True

            # 发送 SIGTERM 信号
            try:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
            except (OSError, ProcessLookupError):
                # 进程组不存在，尝试直接发送给进程
                os.kill(pid, signal.SIGTERM)

            # 等待进程退出
            start_time = time.time()
            while time.time() - start_time < self.KILL_TIMEOUT:
                try:
                    os.kill(pid, 0)
                    # 进程还存在，继续等待
                    time.sleep(0.5)
                except OSError:
                    # 进程已退出
                    self._processes.pop(pid, None)
                    if process:
                        try:
                            process.wait()  # 回收僵尸进程
                        except:
                            pass
                    return True

            # 超时，发送 SIGKILL 强制终止
            try:
                os.killpg(os.getpgid(pid), signal.SIGKILL)
            except (OSError, ProcessLookupError):
                os.kill(pid, signal.SIGKILL)

            # 等待进程退出并回收
            time.sleep(1)
            self._processes.pop(pid, None)
            if process:
                try:
                    process.wait()  # 回收僵尸进程
                except:
                    pass
            return True

        except Exception:
            return False

    def getProcess(self, pid: int) -> subprocess.Popen:
        """获取进程引用"""
        return self._processes.get(pid)
