"""Finviz 数据提供者模块

Finviz 股票筛选和分析数据集成。
提供股票筛选、关键指标、价格表现等数据。
"""

from openbb_core.provider.abstract.provider import Provider
from openbb_finviz.models.compare_groups import FinvizCompareGroupsFetcher
from openbb_finviz.models.equity_profile import FinvizEquityProfileFetcher
from openbb_finviz.models.equity_screener import FinvizEquityScreenerFetcher
from openbb_finviz.models.key_metrics import FinvizKeyMetricsFetcher
from openbb_finviz.models.price_performance import FinvizPricePerformanceFetcher
from openbb_finviz.models.price_target import FinvizPriceTargetFetcher

finviz_provider = Provider(
    name="finviz",
    website="https://finviz.com",
    description="Unofficial Finviz API - https://github.com/lit26/finvizfinance/releases",
    credentials=None,
    fetcher_dict={
        "CompareGroups": FinvizCompareGroupsFetcher,
        "EtfPricePerformance": FinvizPricePerformanceFetcher,
        "EquityInfo": FinvizEquityProfileFetcher,
        "EquityScreener": FinvizEquityScreenerFetcher,
        "KeyMetrics": FinvizKeyMetricsFetcher,
        "PricePerformance": FinvizPricePerformanceFetcher,
        "PriceTarget": FinvizPriceTargetFetcher,
    },
    repr_name="FinViz",
)
