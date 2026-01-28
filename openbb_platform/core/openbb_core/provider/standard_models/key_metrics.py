"""关键指标标准模型

本模块定义了公司关键指标查询和数据的标准接口。
"""

from datetime import date as dateType

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.utils.descriptions import (
    DATA_DESCRIPTIONS,
    QUERY_DESCRIPTIONS,
)
from pydantic import Field, field_validator


class KeyMetricsQueryParams(QueryParams):
    """关键指标查询参数

    Attributes
    ----------
    symbol : str
        股票代码
    """

    symbol: str = Field(description=QUERY_DESCRIPTIONS.get("symbol", ""))

    @field_validator("symbol", mode="before", check_fields=False)
    @classmethod
    def to_upper(cls, v: str) -> str:
        """将股票代码转换为大写"""
        return v.upper()


class KeyMetricsData(Data):
    """关键指标数据

    包含公司的关键财务指标，如市值等。
    """

    symbol: str = Field(description=DATA_DESCRIPTIONS.get("symbol", ""))
    period_ending: dateType | None = Field(
        default=None, description="End date of the reporting period."
    )
    fiscal_year: int | None = Field(
        default=None, description="Fiscal year for the fiscal period, if available."
    )
    fiscal_period: str | None = Field(
        default=None, description="Fiscal period for the data, if available."
    )
    currency: str | None = Field(
        default=None,
        description="Currency in which the data is reported.",
    )
    market_cap: int | float | None = Field(
        default=None, description=DATA_DESCRIPTIONS.get("market_cap", "")
    )
