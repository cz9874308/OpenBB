"""ETF 持仓标准模型

本模块定义了 ETF 持仓查询和数据的标准接口。
"""

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.utils.descriptions import (
    DATA_DESCRIPTIONS,
    QUERY_DESCRIPTIONS,
)
from pydantic import Field, field_validator


class EtfHoldingsQueryParams(QueryParams):
    """ETF 持仓查询参数

    Attributes
    ----------
    symbol : str
        ETF 代码
    """

    symbol: str = Field(description=QUERY_DESCRIPTIONS.get("symbol", "") + " (ETF)")

    @field_validator("symbol")
    @classmethod
    def to_upper(cls, v: str) -> str:
        """将 ETF 代码转换为大写"""
        return v.upper()


class EtfHoldingsData(Data):
    """ETF 持仓数据

    包含 ETF 的持仓明细。
    """

    symbol: str | None = Field(
        default=None, description=DATA_DESCRIPTIONS.get("symbol", "")
    )
    name: str | None = Field(
        default=None,
        description="Name of the asset.",
    )
