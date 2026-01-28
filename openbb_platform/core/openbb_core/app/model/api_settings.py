"""FastAPI 配置设置模块

本模块定义了 FastAPI 服务器的配置模型。
"""

from pydantic import BaseModel, ConfigDict, Field, computed_field


class Cors(BaseModel):
    """CORS 配置模型

    用于配置 FastAPI 的跨域资源共享设置。

    Attributes
    ----------
    allow_origins : list[str]
        允许的源列表
    allow_methods : list[str]
        允许的 HTTP 方法列表
    allow_headers : list[str]
        允许的请求头列表
    """

    model_config = ConfigDict(frozen=True)

    allow_origins: list[str] = Field(default_factory=lambda: ["*"])
    allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    allow_headers: list[str] = Field(default_factory=lambda: ["*"])


class Servers(BaseModel):
    """服务器配置模型

    用于 OpenAPI 文档的服务器定义。

    Attributes
    ----------
    url : str
        服务器 URL
    description : str
        服务器描述
    """

    model_config = ConfigDict(frozen=True)

    url: str = ""
    description: str = "Local OpenBB development server"


class APISettings(BaseModel):
    """API 设置模型

    FastAPI 应用程序的配置设置。

    Attributes
    ----------
    version : str
        API 版本
    title : str
        API 标题
    description : str
        API 描述
    servers : list[Servers]
        服务器列表
    cors : Cors
        CORS 配置
    custom_headers : dict[str, str] | None
        自定义请求头
    prefix : str
        API 前缀（计算属性）
    """

    model_config = ConfigDict(frozen=True)

    version: str = "1"
    title: str = "OpenBB Platform API"
    description: str = "Investment research for everyone, anywhere."
    terms_of_service: str = "http://example.com/terms/"
    contact_name: str = "OpenBB Team"
    contact_url: str = "https://openbb.co"
    contact_email: str = "hello@openbb.co"
    license_name: str = "AGPLv3"
    license_url: str = "https://github.com/OpenBB-finance/OpenBB/blob/develop/LICENSE"
    servers: list[Servers] = Field(default_factory=lambda: [Servers()])
    cors: Cors = Field(default_factory=Cors)
    custom_headers: dict[str, str] | None = Field(
        default=None, description="自定义请求头及其默认值"
    )

    @computed_field  # type: ignore[misc]
    @property
    def prefix(self) -> str:
        """获取 API 前缀"""
        return f"/api/v{self.version}"

    def __repr__(self) -> str:
        """返回模型的字符串表示"""
        return f"{self.__class__.__name__}\n\n" + "\n".join(
            f"{k}: {v}" for k, v in self.model_dump().items()
        )
