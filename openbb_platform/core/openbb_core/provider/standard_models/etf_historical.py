"""ETF 历史价格标准模型

本模块定义了 ETF 历史价格查询和数据的标准接口。
"""

from datetime import (
    date as dateType,
    datetime,
)

from dateutil import parser
from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.utils.descriptions import (
    DATA_DESCRIPTIONS,
    QUERY_DESCRIPTIONS,
)
from pydantic import Field, NonNegativeInt, PositiveFloat, field_validator


class EtfHistoricalQueryParams(QueryParams):
    """ETF 历史价格查询参数

    Attributes
    ----------
    symbol : str
        ETF 代码
    start_date : date | None
        开始日期
    end_date : date | None
        结束日期
    """

    symbol: str = Field(description=QUERY_DESCRIPTIONS.get("symbol", "") + " (ETF)")
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
        """将 ETF 代码转换为大写"""
        return v.upper()


class EtfHistoricalData(Data):
    """ETF 历史价格数据

    Attributes
    ----------
    date : date | datetime
        日期
    open : PositiveFloat
        开盘价
    high : PositiveFloat
        最高价
    low : PositiveFloat
        最低价
    close : PositiveFloat
        收盘价
    volume : NonNegativeInt | None
        成交量
    """

    date: dateType | datetime = Field(description=DATA_DESCRIPTIONS.get("date", ""))
    open: PositiveFloat = Field(description=DATA_DESCRIPTIONS.get("open", ""))
    high: PositiveFloat = Field(description=DATA_DESCRIPTIONS.get("high", ""))
    low: PositiveFloat = Field(description=DATA_DESCRIPTIONS.get("low", ""))
    close: PositiveFloat = Field(description=DATA_DESCRIPTIONS.get("close", ""))
    volume: NonNegativeInt | None = Field(
        description=DATA_DESCRIPTIONS.get("volume", "")
    )

    @field_validator("date", mode="before", check_fields=False)
    def date_validate(cls, v):  # pylint: disable=E0213
        """验证并格式化日期"""
        if ":" in str(v):
            return parser.isoparse(str(v))
        return parser.parse(str(v)).date()
