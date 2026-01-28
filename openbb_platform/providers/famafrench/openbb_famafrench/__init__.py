"""Fama-French 数据提供者模块

Fama-French 因子研究数据集成。
提供三因子、五因子、组合收益等学术研究数据。
"""

from openbb_core.provider.abstract.provider import Provider
from openbb_famafrench.models.breakpoints import FamaFrenchBreakpointFetcher
from openbb_famafrench.models.country_portfolio_returns import (
    FamaFrenchCountryPortfolioReturnsFetcher,
)
from openbb_famafrench.models.factors import FamaFrenchFactorsFetcher
from openbb_famafrench.models.international_index_returns import (
    FamaFrenchInternationalIndexReturnsFetcher,
)
from openbb_famafrench.models.regional_portfolio_returns import (
    FamaFrenchRegionalPortfolioReturnsFetcher,
)
from openbb_famafrench.models.us_portfolio_returns import (
    FamaFrenchUSPortfolioReturnsFetcher,
)

famafrench_provider = Provider(
    name="famafrench",
    website="https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html",
    description="""
    This provider implements the Fama-French research portfolios and factors data library,
    maintained and hosted by Kenneth R. French at Dartmouth College.
    """,
    fetcher_dict={
        "FamaFrenchBreakpoints": FamaFrenchBreakpointFetcher,
        "FamaFrenchCountryPortfolioReturns": FamaFrenchCountryPortfolioReturnsFetcher,
        "FamaFrenchFactors": FamaFrenchFactorsFetcher,
        "FamaFrenchInternationalIndexReturns": FamaFrenchInternationalIndexReturnsFetcher,
        "FamaFrenchRegionalPortfolioReturns": FamaFrenchRegionalPortfolioReturnsFetcher,
        "FamaFrenchUSPortfolioReturns": FamaFrenchUSPortfolioReturnsFetcher,
    },
    repr_name="Fama-French Research Portfolios and Factors",
)
