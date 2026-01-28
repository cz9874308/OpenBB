"""FINRA 数据提供者模块

金融业监管局 (FINRA) 数据集成。
提供场外交易、空头利息等市场数据。
"""

from openbb_core.provider.abstract.provider import Provider
from openbb_finra.models.equity_short_interest import FinraShortInterestFetcher
from openbb_finra.models.otc_aggregate import FinraOTCAggregateFetcher

finra_provider = Provider(
    name="finra",
    website="https://www.finra.org/finra-data",
    description="""FINRA Data provides centralized access to the abundance of data FINRA
makes available to the public, media, researchers and member firms.""",
    credentials=None,
    fetcher_dict={
        "OTCAggregate": FinraOTCAggregateFetcher,
        "EquityShortInterest": FinraShortInterestFetcher,
    },
    repr_name="Financial Industry Regulatory Authority (FINRA)",
)
