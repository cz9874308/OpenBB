"""股票搜索标准模型

本模块定义了股票搜索查询和数据的标准接口。
"""

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.utils.descriptions import DATA_DESCRIPTIONS
from pydantic import Field


class EquitySearchQueryParams(QueryParams):
    """股票搜索查询参数

    Attributes
    ----------
    query : str
        搜索查询字符串
    is_symbol : bool
        是否按股票代码搜索
    """

    query: str = Field(description="Search query.", default="")
    is_symbol: bool = Field(
        description="Whether to search by ticker symbol.", default=False
    )


class EquitySearchData(Data):
    """股票搜索数据

    包含匹配的股票代码和公司名称。
    """

    symbol: str | None = Field(
        default=None, description=DATA_DESCRIPTIONS.get("symbol", "")
    )
    name: str | None = Field(default=None, description="Name of the company.")
