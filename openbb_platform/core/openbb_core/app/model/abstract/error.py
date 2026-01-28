"""OpenBB 异常模块

本模块定义了 OpenBB 平台的自定义异常类。
"""


class OpenBBError(Exception):
    """OpenBB 异常类

    所有 OpenBB 特定错误的基类。

    Attributes
    ----------
    original : str | Exception | None
        原始错误信息或异常对象
    """

    def __init__(self, original: str | Exception | None = None):
        """初始化 OpenBBError

        Parameters
        ----------
        original : str | Exception | None, optional
            原始错误信息或异常，默认为 None
        """
        self.original = original
        super().__init__(str(original))
