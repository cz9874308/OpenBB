"""Python 配置设置模块

本模块定义了 Python SDK 的配置设置。
"""

from pydantic import BaseModel, ConfigDict, Field, PositiveInt


class PythonSettings(BaseModel):
    """Python 接口配置设置

    用于配置 Python SDK 的行为，如自动生成的文档字符串、
    HTTP 请求设置和 Uvicorn 服务器设置。

    Attributes
    ----------
    docstring_sections : list[str]
        自动生成文档字符串中包含的部分
    docstring_max_length : PositiveInt | None
        自动生成文档字符串的最大长度
    http : dict | None
        HTTP 请求设置
    uvicorn : dict | None
        Uvicorn 服务器设置
    """

    model_config = ConfigDict(extra="allow")

    docstring_sections: list[str] = Field(
        default_factory=lambda: ["description", "parameters", "returns", "examples"],
        description="自动生成文档字符串中包含的部分",
    )
    docstring_max_length: PositiveInt | None = Field(
        default=None, description="自动生成文档字符串的最大长度"
    )
    http: dict | None = Field(
        default_factory=dict,
        description="HTTP settings covers all requests made by the internal, utility, functions."
        + " The configuration applies to both the requests and aiohttp libraries."
        + "\n    "
        + """Available settings:
            - cafile: str - Path to a CA certificate file.
            - certfile: str - Path to a client certificate file.
            - keyfile: str - Path to a client key file.
            - password: str - Password for the client key file.  # aiohttp only
            - verify_ssl: bool - Verify SSL certificates.
            - fingerprint: str - SSL fingerprint.  # aiohttp only
            - proxy: str - Proxy URL.
            - proxy_auth: str | list - Proxy authentication.  # aiohttp only
            - proxy_headers: dict - Proxy headers.  # aiohttp only
            - timeout: int - Request timeout.
            - auth: str | list - Basic authentication.
            - headers: dict - Request headers.
            - cookies: dict - Dictionary of session cookies.

        Any additional keys supplied will be ignored unless explicitly implemented via custom code.

        The settings are passed into the `requests.Session` object and the `aiohttp.ClientSession` object by:
            - `openbb_core.provider.utils.helpers.make_request` - Sync
            - `openbb_core.provider.utils.helpers.amake_request` - Async
            - `openbb_core.provider.utils.helpers.amake_requests` - Async (multiple requests)
            - Inserted to use with YFinance & Finviz library implementations.

        Return a session object with the settings applied by:
            - `openbb_core.provider.utils.helpers.get_requests_session`
            - `openbb_core.provider.utils.helpers.get_async_requests_session`
        """,
    )
    uvicorn: dict | None = Field(
        default_factory=dict,
        description="Uvicorn settings, covers all the launch of FastAPI when using the following entry points:"
        + "\n    "
        + """
            - Running the FastAPI as a Python module script.
              - python -m openbb_core.api.rest_api
            - Running the `openbb-api` command.
                - openbb-api

        All settings are passed directly to `uvicorn.run`, and can be found in the Uvicorn documentation.
            - https://www.uvicorn.org/settings/

        Keyword arguments supplied to the command line will take priority over the settings in this configuration.
        """,
    )

    def __repr__(self) -> str:
        """返回模型的字符串表示"""
        return f"{self.__class__.__name__}\n\n" + "\n".join(
            f"{k}: {v}" for k, v in self.model_dump().items()
        )
