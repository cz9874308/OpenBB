"""Multpl 数据提供者模块

Multpl 市场估值数据集成。
提供 S&P 500 市盈率、席勒 PE 等估值指标。
"""

from openbb_core.provider.abstract.provider import Provider
from openbb_multpl.models.sp500_multiples import MultplSP500MultiplesFetcher

multpl_provider = Provider(
    name="multpl",
    website="https://www.multpl.com/",
    description="""Public broad-market data published to https://multpl.com.""",
    fetcher_dict={
        "SP500Multiples": MultplSP500MultiplesFetcher,
    },
)
