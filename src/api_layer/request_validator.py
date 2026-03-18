"""
RequestValidator 模块

职责: 请求参数验证与提取

参与流程: 5 个流程 (3.2.1 - 3.2.5)
"""

from typing import Dict, Tuple

from ..exceptions import ValidationError


class RequestValidator:
    """请求参数验证与提取"""

    def validateProxyRequest(self, headers: Dict[str, str]) -> Tuple[str, str]:
        """
        验证 OpenCode API 代理请求，从 HTTP Headers 中提取租户标识和沙箱标识

        流程: 3.2.1 - OpenCode API 代理主流程

        Args:
            headers: HTTP 请求头字典

        Returns:
            Tuple[str, str]: (domainID, sandboxID)

        Raises:
            ValidationError: 验证失败时抛出，错误码 MISSING_DOMAIN_ID 或 MISSING_SANDBOX_ID
        """
        # 提取 X-Domain-ID
        domainID = headers.get("X-Domain-ID") or headers.get("x-domain-id")
        if not domainID:
            raise ValidationError(
                code="MISSING_DOMAIN_ID",
                message="缺少 X-Domain-ID Header",
                details={"header": "X-Domain-ID"}
            )

        # 提取 X-Sandbox-ID
        sandboxID = headers.get("X-Sandbox-ID") or headers.get("x-sandbox-id")
        if not sandboxID:
            raise ValidationError(
                code="MISSING_SANDBOX_ID",
                message="缺少 X-Sandbox-ID Header",
                details={"header": "X-Sandbox-ID"}
            )

        return (domainID, sandboxID)

    def validateAdminListRequest(self, body: Dict) -> Dict:
        """
        验证列出所有沙箱的管理接口请求，确保请求体为空

        流程: 3.2.2 - 管理接口：列出所有沙箱

        Args:
            body: HTTP 请求体，必须为空对象

        Returns:
            Dict: 返回空字典

        Raises:
            ValidationError: 请求体不为空时抛出，错误码 INVALID_REQUEST_BODY
        """
        if body and len(body) > 0:
            raise ValidationError(
                code="INVALID_REQUEST_BODY",
                message="请求体必须为空",
                details={"body": body}
            )
        return {}

    def validateAdminGetRequest(self, body: Dict) -> Tuple[str, str]:
        """
        验证查询单个沙箱的管理接口请求，从请求体中提取租户标识和沙箱标识

        流程: 3.2.3 - 管理接口：查询单个沙箱

        Args:
            body: HTTP 请求体，包含 domainID 和 sandboxID

        Returns:
            Tuple[str, str]: (domainID, sandboxID)

        Raises:
            ValidationError: 参数缺失时抛出，错误码 MISSING_DOMAIN_ID 或 MISSING_SANDBOX_ID
        """
        domainID = body.get("domainID")
        if not domainID:
            raise ValidationError(
                code="MISSING_DOMAIN_ID",
                message="缺少 domainID 参数",
                details={"field": "domainID"}
            )

        sandboxID = body.get("sandboxID")
        if not sandboxID:
            raise ValidationError(
                code="MISSING_SANDBOX_ID",
                message="缺少 sandboxID 参数",
                details={"field": "sandboxID"}
            )

        return (domainID, sandboxID)

    def validateAdminCreateRequest(self, body: Dict) -> Tuple[str, str]:
        """
        验证创建沙箱的管理接口请求，从请求体中提取租户标识和沙箱标识

        流程: 3.2.4 - 管理接口：创建沙箱

        Args:
            body: HTTP 请求体，包含 domainID 和 sandboxID

        Returns:
            Tuple[str, str]: (domainID, sandboxID)

        Raises:
            ValidationError: 参数缺失时抛出，错误码 MISSING_DOMAIN_ID 或 MISSING_SANDBOX_ID
        """
        domainID = body.get("domainID")
        if not domainID:
            raise ValidationError(
                code="MISSING_DOMAIN_ID",
                message="缺少 domainID 参数",
                details={"field": "domainID"}
            )

        sandboxID = body.get("sandboxID")
        if not sandboxID:
            raise ValidationError(
                code="MISSING_SANDBOX_ID",
                message="缺少 sandboxID 参数",
                details={"field": "sandboxID"}
            )

        return (domainID, sandboxID)

    def validateAdminDestroyRequest(self, body: Dict) -> Tuple[str, str]:
        """
        验证销毁沙箱的管理接口请求，从请求体中提取租户标识和沙箱标识

        流程: 3.2.5 - 管理接口：销毁沙箱

        Args:
            body: HTTP 请求体，包含 domainID 和 sandboxID

        Returns:
            Tuple[str, str]: (domainID, sandboxID)

        Raises:
            ValidationError: 参数缺失时抛出，错误码 MISSING_DOMAIN_ID 或 MISSING_SANDBOX_ID
        """
        domainID = body.get("domainID")
        if not domainID:
            raise ValidationError(
                code="MISSING_DOMAIN_ID",
                message="缺少 domainID 参数",
                details={"field": "domainID"}
            )

        sandboxID = body.get("sandboxID")
        if not sandboxID:
            raise ValidationError(
                code="MISSING_SANDBOX_ID",
                message="缺少 sandboxID 参数",
                details={"field": "sandboxID"}
            )

        return (domainID, sandboxID)
