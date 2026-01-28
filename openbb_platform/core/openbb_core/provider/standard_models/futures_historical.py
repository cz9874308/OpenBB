"""期货历史价格标准模型

本模块定义了期货历史价格查询和数据的标准接口。
"""

from datetime import date, datetime

from dateutil import parser
from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.utils.descriptions import (
    DATA_DESCRIPTIONS,
    QUERY_DESCRIPTIONS,
)
from pydantic import Field, field_validator


class FuturesHistoricalQueryParams(QueryParams):
    """期货历史价格查询参数

    Attributes
    ----------
    symbol : str
        期货代码
    start_date : date | None
        开始日期
    end_date : date | None
        结束日期
    expiration : str | None
        期货到期日（格式：YYYY-MM）
    """

    symbol: str = Field(description=QUERY_DESCRIPTIONS.get("symbol", ""))
    start_date: date | None = Field(
        default=None,
        description=QUERY_DESCRIPTIONS.get("start_date", ""),
    )
    end_date: date | None = Field(
        default=None,
        description=QUERY_DESCRIPTIONS.get("end_date", ""),
    )
    expiration: str | None = Field(
        default=None,
        description="Future expiry date with format YYYY-MM",
    )

    @field_validator("symbol", mode="before", check_fields=False)
    @classmethod
    def to_upper(cls, v: str) -> str:
        """将期货代码转换为大写"""
        return v.upper()


class FuturesHistoricalData(Data):
    """期货历史价格数据

    包含期货合约的 OHLCV 数据。
    """

    date: datetime = Field(description=DATA_DESCRIPTIONS.get("date", ""))
    open: float = Field(description=DATA_DESCRIPTIONS.get("open", ""))
    high: float = Field(description=DATA_DESCRIPTIONS.get("high", ""))
    low: float = Field(description=DATA_DESCRIPTIONS.get("low", ""))
    close: float = Field(description=DATA_DESCRIPTIONS.get("close", ""))
    volume: float = Field(description=DATA_DESCRIPTIONS.get("volume", ""))

    @field_validator("symbol", mode="before", check_fields=False)
    @classmethod
    def date_validate(cls, v):
        """验证并格式化日期"""
        return parser.isoparse(str(v))
