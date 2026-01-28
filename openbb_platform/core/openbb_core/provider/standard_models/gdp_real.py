"""实际 GDP 标准模型

本模块定义了实际 GDP 查询和数据的标准接口。
"""

from datetime import date as dateType

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.utils.descriptions import (
    DATA_DESCRIPTIONS,
    QUERY_DESCRIPTIONS,
)
from pydantic import Field


class GdpRealQueryParams(QueryParams):
    """实际 GDP 查询参数

    Attributes
    ----------
    start_date : date | None
        开始日期
    end_date : date | None
        结束日期
    """

    start_date: dateType | None = Field(
        default=None, description=QUERY_DESCRIPTIONS.get("start_date")
    )
    end_date: dateType | None = Field(
        default=None, description=QUERY_DESCRIPTIONS.get("end_date")
    )


class GdpRealData(Data):
    """实际 GDP 数据

    包含各国的实际 GDP 值。
    """

    date: dateType = Field(description=DATA_DESCRIPTIONS.get("date"))
    country: str = Field(
        default=None, description="The country represented by the Real GDP value."
    )
    value: int | float = Field(
        description="Real GDP value for the country and date.",
    )
