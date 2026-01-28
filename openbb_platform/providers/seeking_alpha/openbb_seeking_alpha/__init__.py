"""Seeking Alpha 数据提供者模块

Seeking Alpha 投资分析数据集成。
提供财报日历、EPS 和销售预测等数据。
"""

from openbb_core.provider.abstract.provider import Provider
from openbb_seeking_alpha.models.calendar_earnings import SACalendarEarningsFetcher
from openbb_seeking_alpha.models.forward_eps_estimates import (
    SAForwardEpsEstimatesFetcher,
)
from openbb_seeking_alpha.models.forward_sales_estimates import (
    SAForwardSalesEstimatesFetcher,
)

seeking_alpha_provider = Provider(
    name="seeking_alpha",
    website="https://seekingalpha.com",
    description="""Seeking Alpha is a data provider with access to news, analysis, and
real-time alerts on stocks.""",
    fetcher_dict={
        "CalendarEarnings": SACalendarEarningsFetcher,
        "ForwardEpsEstimates": SAForwardEpsEstimatesFetcher,
        "ForwardSalesEstimates": SAForwardSalesEstimatesFetcher,
    },
    repr_name="Seeking Alpha",
)
