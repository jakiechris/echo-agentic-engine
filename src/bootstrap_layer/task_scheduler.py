"""
TaskScheduler 模块

职责: 定时任务调度器,管理后台定时任务的注册和执行

参与流程: 2 个流程 (3.2.6, 3.2.9)
"""

import threading
import time
import logging
from typing import Protocol, Dict, Optional

logger = logging.getLogger(__name__)


class Task(Protocol):
    """任务协议"""

    @property
    def name(self) -> str:
        """任务名称"""
        ...

    def execute(self) -> None:
        """执行任务"""
        ...


class TaskScheduler:
    """定时任务调度器"""

    def __init__(self):
        self._tasks: Dict[str, dict] = {}
        self._threads: Dict[str, threading.Thread] = {}
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def registerTask(self, task: Task, interval: int) -> None:
        """
        注册定时任务，记录任务对象和执行间隔，任务将在调用 startScheduler() 后按指定间隔循环执行

        流程: 3.2.6 - Engine 启动主流程

        Args:
            task: 任务对象，包含任务名称和执行方法
            interval: 执行间隔时间（秒）
        """
        with self._lock:
            task_name = task.name
            self._tasks[task_name] = {
                "task": task,
                "interval": interval
            }
            logger.info(f"[TaskScheduler] Registered task: {task_name} (interval: {interval}s)")

    def startScheduler(self) -> None:
        """
        启动任务调度器，为每个已注册任务创建独立的后台线程，启动所有定时任务循环执行

        流程: 3.2.6 - Engine 启动主流程

        线程模型:
        - 每个定时任务在独立线程中运行
        - 线程名称：task-{taskId}
        - 线程类型：Daemon 线程（随主进程退出）
        """
        self._stop_event.clear()

        with self._lock:
            for task_name, task_info in self._tasks.items():
                if task_name in self._threads:
                    continue  # 已经启动

                thread = threading.Thread(
                    target=self._run_task_loop,
                    args=(task_name, task_info["task"], task_info["interval"]),
                    name=f"task-{task_name}",
                    daemon=True
                )
                self._threads[task_name] = thread
                thread.start()
                logger.info(f"[TaskScheduler] Started task thread: {task_name}")

        logger.info(f"[TaskScheduler] Scheduler started with {len(self._threads)} tasks")

    def _run_task_loop(self, task_name: str, task: Task, interval: int) -> None:
        """
        任务循环执行函数

        Args:
            task_name: 任务名称
            task: 任务对象
            interval: 执行间隔（秒）
        """
        logger.debug(f"[TaskScheduler] Task loop started: {task_name}")

        while not self._stop_event.is_set():
            try:
                task.execute()
            except Exception as e:
                logger.exception(f"[TaskScheduler] Task {task_name} failed: {e}")

            # 使用 wait 而不是 sleep，以便可以中断
            self._stop_event.wait(timeout=interval)

        logger.debug(f"[TaskScheduler] Task loop stopped: {task_name}")

    def stopScheduler(self) -> None:
        """
        停止所有定时任务，设置停止标志位，等待所有任务线程退出，用于 Engine 关闭时优雅停止后台任务

        流程: Engine 关闭流程（非标准流程编号）
        """
        logger.info("[TaskScheduler] Stopping scheduler...")
        self._stop_event.set()

        # 等待所有线程退出
        for task_name, thread in self._threads.items():
            if thread.is_alive():
                thread.join(timeout=5)
                logger.debug(f"[TaskScheduler] Task thread stopped: {task_name}")

        self._threads.clear()
        logger.info("[TaskScheduler] Scheduler stopped")

    def triggerTask(self, taskName: str) -> None:
        """
        立即触发指定任务执行一次，不等待定时器到期，用于配置变更时立即触发相关任务

        流程: 3.2.9 - ConfigSyncTask 调用链

        Args:
            taskName: 任务名称，如 "IdleCleanupTask"
        """
        with self._lock:
            task_info = self._tasks.get(taskName)

        if task_info is None:
            logger.warning(f"[TaskScheduler] Task not found: {taskName}")
            return

        task = task_info["task"]

        try:
            logger.info(f"[TaskScheduler] Manually triggering task: {taskName}")
            task.execute()
        except Exception as e:
            logger.exception(f"[TaskScheduler] Task {taskName} failed: {e}")
