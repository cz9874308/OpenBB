"""ETF 信息标准模型

本模块定义了 ETF 信息查询和数据的标准接口。
"""

from datetime import date as dateType

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.utils.descriptions import (
    DATA_DESCRIPTIONS,
    QUERY_DESCRIPTIONS,
)
from pydantic import Field, field_validator


class EtfInfoQueryParams(QueryParams):
    """ETF 信息查询参数

    Attributes
    ----------
    symbol : str
        ETF 代码
    """

    symbol: str = Field(description=QUERY_DESCRIPTIONS.get("symbol", "") + " (ETF)")

    @field_validator("symbol")
    @classmethod
    def to_upper(cls, v: str) -> str:
        """将 ETF 代码转换为大写"""
        return v.upper()


class EtfInfoData(Data):
    """ETF 信息数据

    包含 ETF 的基本信息。
    """

    symbol: str = Field(description=DATA_DESCRIPTIONS.get("symbol", "") + " (ETF)")
    name: str | None = Field(description="Name of the ETF.")
    issuer: str | None = Field(default=None, description="Issuer of the ETF.")
    domicile: str | None = Field(default=None, description="Domicile of the ETF.")
    website: str | None = Field(default=None, description="Website of the ETF.")
    description: str | None = Field(
        default=None, description="Description of the fund."
    )
    inception_date: dateType | None = Field(
        default=None, description="Inception date of the ETF."
    )
