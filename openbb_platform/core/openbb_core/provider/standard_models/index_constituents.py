"""指数成分股标准模型

本模块定义了指数成分股查询和数据的标准接口。
"""

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.utils.descriptions import (
    DATA_DESCRIPTIONS,
    QUERY_DESCRIPTIONS,
)
from pydantic import Field, field_validator


class IndexConstituentsQueryParams(QueryParams):
    """指数成分股查询参数

    Attributes
    ----------
    symbol : str
        指数代码
    """

    symbol: str = Field(description=QUERY_DESCRIPTIONS.get("symbol", ""))

    @classmethod
    @field_validator("symbol")
    def _to_upper(cls, v):
        """将指数代码转换为大写"""
        return v.upper()


class IndexConstituentsData(Data):
    """指数成分股数据

    包含指数的成分股列表。
    """

    symbol: str = Field(description=DATA_DESCRIPTIONS.get("symbol", ""))
    name: str | None = Field(
        default=None, description="Name of the constituent company in the index."
    )
