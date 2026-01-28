"""空结果模块

本模块定义了空结果类型。
"""

from openbb_core.app.model.abstract.results import Results


class Empty(Results):
    """空结果类

    用于表示没有返回数据的情况。
    """
