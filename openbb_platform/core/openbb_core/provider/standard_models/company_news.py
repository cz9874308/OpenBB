"""公司新闻标准模型

本模块定义了公司新闻查询和数据的标准接口。
"""

from datetime import (
    date as dateType,
    datetime,
)
from typing import Any

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.utils.descriptions import (
    DATA_DESCRIPTIONS,
    QUERY_DESCRIPTIONS,
)
from pydantic import Field, NonNegativeInt, field_validator


class CompanyNewsQueryParams(QueryParams):
    """公司新闻查询参数

    Attributes
    ----------
    symbol : str | None
        股票代码
    start_date : date | None
        开始日期
    end_date : date | None
        结束日期
    limit : NonNegativeInt | None
        返回记录数限制
    """

    symbol: str | None = Field(
        default=None,
        description=QUERY_DESCRIPTIONS.get("symbol", ""),
    )
    start_date: dateType | None = Field(
        default=None, description=QUERY_DESCRIPTIONS.get("start_date", "")
    )
    end_date: dateType | None = Field(
        default=None,
        description=QUERY_DESCRIPTIONS.get("end_date", ""),
    )
    limit: NonNegativeInt | None = Field(
        default=None, description=QUERY_DESCRIPTIONS.get("limit", "")
    )

    @field_validator("symbol", mode="before")
    @classmethod
    def symbols_validate(cls, v):
        """验证股票代码"""
        return v.upper() if v else None


class CompanyNewsData(Data):
    """公司新闻数据

    包含新闻文章的详细信息。
    """

    date: datetime = Field(
        description=DATA_DESCRIPTIONS.get("date", "") + " The date of publication."
    )
    title: str = Field(description="Title of the article.")
    author: str | None = Field(default=None, description="Author of the article.")
    excerpt: str | None = Field(
        default=None, description="Excerpt of the article text."
    )
    body: str | None = Field(default=None, description="Body of the article text.")
    images: Any | None = Field(
        default=None, description="Images associated with the article."
    )
    url: str = Field(description="URL to the article.")
    symbols: str | None = Field(
        default=None, description="Symbols associated with the article."
    )
