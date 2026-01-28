"""数据提供者抽象类模块

本模块定义了 Provider 类，作为所有数据提供者扩展的入口点。

核心概念
--------

Provider（数据提供者）是 OpenBB 平台与外部数据源的桥梁。
每个数据提供者（如 Yahoo Finance、FMP、FRED 等）都需要创建一个 Provider 实例，
将其 Fetcher 注册到平台中。

使用方式
--------

```python
from openbb_core.provider.abstract.provider import Provider
from my_provider.models.equity_historical import MyEquityHistoricalFetcher

my_provider = Provider(
    name="myprovider",
    website="https://myprovider.com",
    description="我的数据提供者",
    credentials=["api_key"],  # 将自动添加前缀为 myprovider_api_key
    fetcher_dict={
        "EquityHistorical": MyEquityHistoricalFetcher,
    },
)
```

凭证管理
--------

credentials 列表中的每个凭证名称会自动添加提供者名称前缀。
例如，如果 name="yfinance"，credentials=["api_key"]，
则实际的凭证名称会变成 "yfinance_api_key"。
"""

from openbb_core.provider.abstract.fetcher import Fetcher


class Provider:
    """数据提供者类

    作为数据提供者扩展的入口点，每个数据提供者都必须创建此类的实例。
    Provider 负责将 Fetcher（数据获取器）注册到 OpenBB 平台。

    核心职责
    --------

    1. 定义提供者的基本信息（名称、描述、网站）
    2. 注册数据获取器（Fetcher）到标准数据模型
    3. 管理 API 凭证和认证信息
    4. 提供设置说明

    使用示例
    --------

    ```python
    yfinance_provider = Provider(
        name="yfinance",
        website="https://finance.yahoo.com",
        description="Yahoo Finance 数据连接器",
        fetcher_dict={
            "EquityHistorical": YFinanceEquityHistoricalFetcher,
            "CryptoHistorical": YFinanceCryptoHistoricalFetcher,
        },
    )
    ```

    Attributes
    ----------
    name : str
        提供者名称（小写，用于凭证前缀）
    description : str
        提供者描述
    website : str | None
        提供者官方网站
    credentials : list[str]
        所需凭证列表（带提供者前缀）
    fetcher_dict : dict[str, type[Fetcher]]
        Fetcher 字典，键为标准模型名称
    repr_name : str | None
        提供者显示名称
    deprecated_credentials : dict[str, str | None] | None
        已废弃凭证的映射
    instructions : str | None
        设置说明（如如何获取 API 密钥）
    """

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        name: str,
        description: str,
        website: str | None = None,
        credentials: list[str] | None = None,
        fetcher_dict: dict[str, type[Fetcher]] | None = None,
        repr_name: str | None = None,
        deprecated_credentials: dict[str, str | None] | None = None,
        instructions: str | None = None,
    ) -> None:
        """初始化数据提供者

        Parameters
        ----------
        name : str
            提供者名称（将用作凭证前缀）
        description : str
            提供者描述
        website : str | None, optional
            提供者官方网站，默认为 None
        credentials : list[str] | None, optional
            所需凭证列表（不带前缀），默认为 None
        fetcher_dict : dict[str, type[Fetcher]] | None, optional
            Fetcher 字典，键为标准模型名称，值为 Fetcher 类，默认为 None
        repr_name : str | None, optional
            提供者显示名称（完整名称），默认为 None
        deprecated_credentials : dict[str, str | None] | None, optional
            已废弃凭证到当前名称的映射，默认为 None
        instructions : str | None, optional
            设置说明，例如如何获取 API 密钥，默认为 None
        """
        self.name = name
        self.description = description
        self.website = website
        self.fetcher_dict = fetcher_dict or {}
        # 处理凭证列表，添加提供者名称前缀
        if credentials is None:
            self.credentials: list = []
        else:
            self.credentials = []
            for c in credentials:
                # 为每个凭证添加提供者名称前缀
                self.credentials.append(f"{self.name.lower()}_{c}")
        self.repr_name = repr_name
        self.deprecated_credentials = deprecated_credentials
        self.instructions = instructions
