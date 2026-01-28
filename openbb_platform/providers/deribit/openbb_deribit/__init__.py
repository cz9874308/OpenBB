"""Deribit 数据提供者模块

Deribit 加密货币衍生品交易所数据集成。
提供期货曲线、期权链等加密衍生品数据。
"""

from openbb_core.provider.abstract.provider import Provider
from openbb_deribit.models.futures_curve import DeribitFuturesCurveFetcher
from openbb_deribit.models.futures_historical import DeribitFuturesHistoricalFetcher
from openbb_deribit.models.futures_info import DeribitFuturesInfoFetcher
from openbb_deribit.models.futures_instruments import DeribitFuturesInstrumentsFetcher
from openbb_deribit.models.options_chains import DeribitOptionsChainsFetcher

deribit_provider = Provider(
    name="deribit",
    website="https://deribit.com/",
    description="""Unofficial Python client for public data published by Deribit.""",
    credentials=None,
    fetcher_dict={
        "FuturesCurve": DeribitFuturesCurveFetcher,
        "FuturesHistorical": DeribitFuturesHistoricalFetcher,
        "FuturesInfo": DeribitFuturesInfoFetcher,
        "FuturesInstruments": DeribitFuturesInstrumentsFetcher,
        "OptionsChains": DeribitOptionsChainsFetcher,
    },
    repr_name="Deribit Public Data",
    instructions="This provider does not require any credentials and is not meant for trading.",
)
