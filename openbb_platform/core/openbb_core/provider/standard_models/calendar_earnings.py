"""财报日历标准模型

本模块定义了财报日历查询和数据的标准接口。
"""

from datetime import date as dateType

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.utils.descriptions import (
    DATA_DESCRIPTIONS,
    QUERY_DESCRIPTIONS,
)
from pydantic import Field


class CalendarEarningsQueryParams(QueryParams):
    """财报日历查询参数

    Attributes
    ----------
    start_date : date | None
        开始日期
    end_date : date | None
        结束日期
    """

    start_date: dateType | None = Field(
        default=None, description=QUERY_DESCRIPTIONS.get("start_date", "")
    )
    end_date: dateType | None = Field(
        default=None, description=QUERY_DESCRIPTIONS.get("end_date", "")
    )


class CalendarEarningsData(Data):
    """财报日历数据

    包含公司的财报发布日期和预期数据。
    """

    report_date: dateType = Field(description="The date of the earnings report.")
    symbol: str = Field(description=DATA_DESCRIPTIONS.get("symbol", ""))
    name: str | None = Field(description="Name of the entity.", default=None)
    eps_previous: float | None = Field(
        default=None,
        description="The earnings-per-share from the same previously reported period.",
    )
    eps_consensus: float | None = Field(
        default=None,
        description="The analyst conesus earnings-per-share estimate.",
    )
