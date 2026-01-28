"""现金流量表标准模型

本模块定义了现金流量表查询和数据的标准接口。
"""

from datetime import date as dateType

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.utils.descriptions import QUERY_DESCRIPTIONS
from pydantic import Field, NonNegativeInt, field_validator


class CashFlowStatementQueryParams(QueryParams):
    """现金流量表查询参数

    Attributes
    ----------
    symbol : str
        股票代码
    limit : NonNegativeInt | None
        返回记录数限制
    """

    symbol: str = Field(description=QUERY_DESCRIPTIONS.get("symbol", ""))
    limit: NonNegativeInt | None = Field(
        default=5, description=QUERY_DESCRIPTIONS.get("limit", "")
    )

    @field_validator("symbol", mode="before", check_fields=False)
    @classmethod
    def to_upper(cls, v: str):
        """将股票代码转换为大写"""
        return v.upper()


class CashFlowStatementData(Data):
    """现金流量表数据

    包含公司的经营、投资和筹资活动现金流信息。
    """

    period_ending: dateType = Field(description="The end date of the reporting period.")
    fiscal_period: str | None = Field(
        description="The fiscal period of the report.", default=None
    )
    fiscal_year: int | None = Field(
        description="The fiscal year of the fiscal period.", default=None
    )
