"""股票历史价格标准模型

本模块定义了股票历史价格查询和数据的标准接口。
"""

from datetime import (
    date as dateType,
    datetime,
)

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.utils.descriptions import (
    DATA_DESCRIPTIONS,
    QUERY_DESCRIPTIONS,
)
from pydantic import Field, field_validator


class EquityHistoricalQueryParams(QueryParams):
    """股票历史价格查询参数

    Attributes
    ----------
    symbol : str
        股票代码
    start_date : date | None
        开始日期
    end_date : date | None
        结束日期
    """

    symbol: str = Field(description=QUERY_DESCRIPTIONS.get("symbol", ""))
    start_date: dateType | None = Field(
        default=None,
        description=QUERY_DESCRIPTIONS.get("start_date", ""),
    )
    end_date: dateType | None = Field(
        default=None,
        description=QUERY_DESCRIPTIONS.get("end_date", ""),
    )

    @field_validator("symbol", mode="before", check_fields=False)
    @classmethod
    def to_upper(cls, v: str) -> str:
        """将股票代码转换为大写"""
        return v.upper()


class EquityHistoricalData(Data):
    """股票历史价格数据

    Attributes
    ----------
    date : date | datetime
        日期
    open : float
        开盘价
    high : float
        最高价
    low : float
        最低价
    close : float
        收盘价
    volume : float | int | None
        成交量
    vwap : float | None
        成交量加权平均价
    """

    date: dateType | datetime = Field(description=DATA_DESCRIPTIONS.get("date", ""))
    open: float = Field(description=DATA_DESCRIPTIONS.get("open", ""))
    high: float = Field(description=DATA_DESCRIPTIONS.get("high", ""))
    low: float = Field(description=DATA_DESCRIPTIONS.get("low", ""))
    close: float = Field(description=DATA_DESCRIPTIONS.get("close", ""))
    volume: float | int | None = Field(
        default=None, description=DATA_DESCRIPTIONS.get("volume", "")
    )
    vwap: float | None = Field(
        default=None, description=DATA_DESCRIPTIONS.get("vwap", "")
    )

    @field_validator("date", mode="before", check_fields=False)
    @classmethod
    def date_validate(cls, v):
        """验证并格式化日期"""
        # pylint: disable=import-outside-toplevel
        from dateutil import parser

        if ":" in str(v):
            return parser.isoparse(str(v))
        return parser.parse(str(v)).date()
