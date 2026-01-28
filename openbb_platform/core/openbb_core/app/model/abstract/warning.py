"""警告模块

本模块定义了 OpenBB 平台的警告相关类和函数。
"""

from warnings import WarningMessage

from pydantic import BaseModel


class Warning_(BaseModel):
    """警告模型

    用于序列化警告信息的 Pydantic 模型。

    Attributes
    ----------
    category : str
        警告类别名称
    message : str
        警告消息内容
    """

    category: str
    message: str


def cast_warning(w: WarningMessage) -> Warning_:
    """将警告转换为 Pydantic 模型

    Parameters
    ----------
    w : WarningMessage
        Python 警告消息对象

    Returns
    -------
    Warning_
        转换后的警告模型
    """
    return Warning_(
        category=w.category.__name__,
        message=str(w.message),
    )


class OpenBBWarning(Warning):
    """OpenBB 警告基类

    所有 OpenBB 特定警告的基类。
    """
