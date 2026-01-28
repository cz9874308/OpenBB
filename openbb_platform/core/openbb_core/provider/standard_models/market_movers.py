"""市场动向标准模型

本模块定义了市场动向（涨跌幅排行）查询和数据的标准接口。
"""

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.utils.descriptions import DATA_DESCRIPTIONS
from pydantic import Field


class MarketMoversQueryParams(QueryParams):
    """市场动向查询参数"""


class MarketMoversData(Data):
    """市场动向数据

    包含股票的涨跌幅信息。
    """

    symbol: str = Field(description=DATA_DESCRIPTIONS.get("symbol", ""))
    name: str | None = Field(
        default=None, description="The name associated with the ticker."
    )
    price: float = Field(description="The last price of the ticker.")
    change: float = Field(description="The change in price from open.")
    change_percent: float = Field(description="The change in percent from open.")
