"""
NasManager 模块

职责: NAS 目录管理,为沙箱准备文件存储环境

参与流程: 2 个流程 (3.2.1, 3.2.4)
"""

import os
import shutil
from ..exceptions import NasPreparationError


class NasManager:
    """NAS 目录管理"""

    # 默认 NAS 根路径
    DEFAULT_NAS_ROOT = "/nas"

    def __init__(self):
        self._nas_root = self.DEFAULT_NAS_ROOT

    def configure(self, nas_root: str):
        """配置 NAS 根路径"""
        self._nas_root = nas_root

    def prepareDirectory(self, domainID: str, sandboxID: str, projectName: str = "defaultProject") -> str:
        """
        创建沙箱 NAS 目录结构,包括 data, config, projects/{projectName}, tmp 四个子目录,并设置权限

        流程: 3.2.1 - OpenCode API 代理主流程
        流程: 3.2.4 - 管理接口：创建沙箱

        Args:
            domainID: 租户标识
            sandboxID: 沙箱标识
            projectName: 项目名称，默认为 defaultProject

        Returns:
            str: 创建的 NAS 根目录路径

        Raises:
            NasPreparationError: 目录创建失败时抛出
        """
        # 构建目录路径
        sandbox_path = os.path.join(self._nas_root, domainID, sandboxID)
        data_dir = os.path.join(sandbox_path, "data")
        config_dir = os.path.join(sandbox_path, "config")
        projects_dir = os.path.join(sandbox_path, "projects")
        project_dir = os.path.join(projects_dir, projectName)
        tmp_dir = os.path.join(sandbox_path, "tmp")

        try:
            # 创建所有必需的目录
            os.makedirs(data_dir, exist_ok=True)
            os.makedirs(config_dir, exist_ok=True)
            os.makedirs(project_dir, exist_ok=True)
            os.makedirs(tmp_dir, exist_ok=True)

            # 设置权限 (可读可写可执行)
            os.chmod(sandbox_path, 0o777)
            os.chmod(data_dir, 0o777)
            os.chmod(config_dir, 0o777)
            os.chmod(projects_dir, 0o777)
            os.chmod(project_dir, 0o777)
            os.chmod(tmp_dir, 0o777)

            return sandbox_path

        except OSError as e:
            raise NasPreparationError(
                f"NAS 目录创建失败: {str(e)}",
                nasPath=sandbox_path
            )

    def removeDirectory(self, domainID: str, sandboxID: str) -> bool:
        """
        删除沙箱 NAS 目录及其所有内容

        流程: 目前未使用

        Args:
            domainID: 租户标识
            sandboxID: 沙箱标识

        Returns:
            bool: 是否删除成功
        """
        sandbox_path = os.path.join(self._nas_root, domainID, sandboxID)

        try:
            if os.path.exists(sandbox_path):
                shutil.rmtree(sandbox_path)
            return True
        except OSError:
            return False

    def getNasPath(self, domainID: str, sandboxID: str) -> str:
        """获取沙箱 NAS 路径（不创建）"""
        return os.path.join(self._nas_root, domainID, sandboxID)

    def directoryExists(self, domainID: str, sandboxID: str) -> bool:
        """检查目录是否存在"""
        sandbox_path = os.path.join(self._nas_root, domainID, sandboxID)
        return os.path.isdir(sandbox_path)
