"""财务比率标准模型

本模块定义了财务比率查询和数据的标准接口。
"""

from datetime import date as dateType

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.utils.descriptions import (
    DATA_DESCRIPTIONS,
    QUERY_DESCRIPTIONS,
)
from pydantic import Field, field_validator


class FinancialRatiosQueryParams(QueryParams):
    """财务比率查询参数

    Attributes
    ----------
    symbol : str
        股票代码
    limit : int | None
        返回记录数限制
    """

    symbol: str = Field(description=QUERY_DESCRIPTIONS.get("symbol", ""))
    limit: int | None = Field(
        default=None, description=QUERY_DESCRIPTIONS.get("limit", "")
    )

    @field_validator("symbol", mode="before", check_fields=False)
    @classmethod
    def to_upper(cls, v: str):
        """将股票代码转换为大写"""
        return v.upper()


class FinancialRatiosData(Data):
    """财务比率数据

    包含公司的各类财务比率。
    """

    symbol: str | None = Field(
        default=None, description=DATA_DESCRIPTIONS.get("symbol", "")
    )
    period_ending: dateType | None = Field(
        default=None, description=DATA_DESCRIPTIONS.get("date", "")
    )
    fiscal_period: str | None = Field(
        default=None, description="Period of the financial ratios."
    )
    fiscal_year: int | None = Field(default=None, description="Fiscal year.")
