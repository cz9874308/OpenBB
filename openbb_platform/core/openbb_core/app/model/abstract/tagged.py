"""带标签的模型基类

本模块定义了 Tagged 类，为模型提供唯一标识符。
"""

from pydantic import BaseModel, Field
from uuid_extensions import uuid7str


class Tagged(BaseModel):
    """带标签的模型基类

    为继承类提供自动生成的 UUID7 标识符。
    UUID7 是基于时间戳的 UUID，具有时间排序性。

    Attributes
    ----------
    id : str
        自动生成的 UUID7 标识符
    """

    id: str = Field(default_factory=uuid7str)
