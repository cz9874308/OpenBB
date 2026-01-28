"""FRED 数据序列标准模型

本模块定义了 FRED 数据序列查询和数据的标准接口。
"""

from datetime import date as dateType

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.utils.descriptions import (
    DATA_DESCRIPTIONS,
    QUERY_DESCRIPTIONS,
)
from pydantic import Field, field_validator


class SeriesQueryParams(QueryParams):
    """FRED 数据序列查询参数

    Attributes
    ----------
    symbol : str
        FRED 序列 ID
    start_date : date | None
        开始日期
    end_date : date | None
        结束日期
    limit : int | None
        返回记录数限制
    """

    symbol: str = Field(
        description=QUERY_DESCRIPTIONS.get("symbol", ""),
    )
    start_date: dateType | None = Field(
        description=QUERY_DESCRIPTIONS.get("start_date", ""), default=None
    )
    end_date: dateType | None = Field(
        description=QUERY_DESCRIPTIONS.get("end_date", ""), default=None
    )
    limit: int | None = Field(
        description=QUERY_DESCRIPTIONS.get("limit", ""), default=100000
    )

    @field_validator("symbol", mode="before", check_fields=False)
    @classmethod
    def to_upper(cls, v: str) -> str:
        """将序列 ID 转换为大写"""
        return v.upper()


class SeriesData(Data):
    """FRED 数据序列数据

    包含 FRED 经济数据序列。
    """

    date: dateType = Field(description=DATA_DESCRIPTIONS.get("date", ""))
