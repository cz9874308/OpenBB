"""数据提供者自定义异常模块

本模块定义了数据提供者相关的自定义异常类。
"""

from openbb_core.app.model.abstract.error import OpenBBError


class EmptyDataError(OpenBBError):
    """空数据异常

    当查询未返回任何数据时抛出。
    """

    def __init__(
        self, message: str = "No results found. Try adjusting the query parameters."
    ):
        """初始化异常"""
        self.message = message
        super().__init__(self.message)


class UnauthorizedError(OpenBBError):
    """未授权异常

    当 API 请求未通过授权验证时抛出。
    """

    def __init__(
        self,
        message: str | tuple[str] = (
            "Unauthorized <provider name> API request."
            " Please check your <provider name> credentials and subscription access.",
        ),
        provider_name: str = "<provider name>",
    ):
        """初始化异常"""
        if provider_name and provider_name != "<provider name>":
            msg = message
            if isinstance(msg, tuple):
                msg = msg[0].replace("<provider name>", provider_name)
            elif isinstance(msg, str):
                msg = msg.replace("<provider name>", provider_name)
            message = msg
        self.message = message
        super().__init__(str(self.message))
