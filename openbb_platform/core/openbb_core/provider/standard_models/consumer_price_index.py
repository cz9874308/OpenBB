"""消费者价格指数 (CPI) 标准模型

本模块定义了 CPI 查询和数据的标准接口。
"""

from datetime import date as dateType
from typing import Literal

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.utils.descriptions import (
    DATA_DESCRIPTIONS,
    QUERY_DESCRIPTIONS,
)
from pydantic import Field


class ConsumerPriceIndexQueryParams(QueryParams):
    """CPI 查询参数

    Attributes
    ----------
    country : str
        国家
    transform : str
        数据转换方式
    frequency : Literal["annual", "quarter", "monthly"]
        数据频率
    harmonized : bool
        是否返回调和数据
    start_date : date | None
        开始日期
    end_date : date | None
        结束日期
    """

    country: str = Field(
        description=QUERY_DESCRIPTIONS.get("country"),
        default="united_states",
    )
    transform: str = Field(
        description="Transformation of the CPI data.",
        default="yoy",
    )
    frequency: Literal["annual", "quarter", "monthly"] = Field(
        default="monthly",
        description=QUERY_DESCRIPTIONS.get("frequency"),
    )
    harmonized: bool = Field(
        default=False, description="If true, returns harmonized data."
    )
    start_date: dateType | None = Field(
        default=None, description=QUERY_DESCRIPTIONS.get("start_date")
    )
    end_date: dateType | None = Field(
        default=None, description=QUERY_DESCRIPTIONS.get("end_date")
    )


class ConsumerPriceIndexData(Data):
    """CPI 数据

    包含消费者价格指数值。
    """

    date: dateType = Field(description=DATA_DESCRIPTIONS.get("date"))
    country: str = Field(description=DATA_DESCRIPTIONS.get("country"))
    value: float = Field(description="CPI index value or period change.")
