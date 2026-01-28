"""内部交易标准模型

本模块定义了内部人交易查询和数据的标准接口。
"""

from datetime import (
    date as dateType,
    datetime,
    time,
)

from dateutil import parser
from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.utils.descriptions import (
    DATA_DESCRIPTIONS,
    QUERY_DESCRIPTIONS,
)
from pydantic import Field, field_validator


class InsiderTradingQueryParams(QueryParams):
    """内部交易查询参数

    Attributes
    ----------
    symbol : str
        股票代码
    limit : int | None
        返回记录数限制
    """

    symbol: str = Field(description=QUERY_DESCRIPTIONS.get("symbol", ""))
    limit: int | None = Field(
        default=None,
        description=QUERY_DESCRIPTIONS.get("limit", ""),
    )

    @field_validator("symbol", mode="before", check_fields=False)
    @classmethod
    def to_upper(cls, v: str) -> str:
        """将股票代码转换为大写"""
        return v.upper()


class InsiderTradingData(Data):
    """内部交易数据

    包含公司内部人士的交易记录。
    """

    symbol: str | None = Field(
        default=None, description=DATA_DESCRIPTIONS.get("symbol", "")
    )
    company_cik: str | None = Field(
        default=None,
        description="CIK number of the company.",
        coerce_numbers_to_str=True,
    )
    filing_date: dateType | datetime | None = Field(
        default=None, description="Filing date of the trade."
    )
    transaction_date: dateType | None = Field(
        default=None, description="Date of the transaction."
    )
    owner_cik: int | str | None = Field(
        default=None, description="Reporting individual's CIK."
    )
    owner_name: str | None = Field(
        default=None, description="Name of the reporting individual."
    )
    owner_title: str | None = Field(
        default=None, description="The title held by the reporting individual."
    )
    ownership_type: str | None = Field(
        default=None, description="Type of ownership, e.g., direct or indirect."
    )
    transaction_type: str | None = Field(
        default=None, description="Type of transaction being reported."
    )
    acquisition_or_disposition: str | None = Field(
        default=None, description="Acquisition or disposition of the shares."
    )
    security_type: str | None = Field(
        default=None, description="The type of security transacted."
    )
    securities_owned: float | None = Field(
        default=None,
        description="Number of securities owned by the reporting individual.",
    )
    securities_transacted: float | None = Field(
        default=None,
        description="Number of securities transacted by the reporting individual.",
    )
    transaction_price: float | None = Field(
        default=None, description="The price of the transaction."
    )
    filing_url: str | None = Field(default=None, description="Link to the filing.")

    @field_validator(
        "filing_date", "transaction_date", mode="before", check_fields=False
    )
    @classmethod
    def date_validate(cls, v):  # pylint: disable=E0213
        """验证并格式化日期"""
        if v:
            filing_date = parser.isoparse(str(v))
            if filing_date.time() == time(0, 0):
                return filing_date.date()
            return filing_date
        return None
