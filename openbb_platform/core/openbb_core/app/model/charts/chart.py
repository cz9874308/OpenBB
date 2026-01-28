"""OpenBB 图表模型模块

本模块定义了图表数据的容器模型。
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Chart(BaseModel):
    """图表模型

    存储图表数据和图形对象。

    Attributes
    ----------
    content : dict[str, Any] | None
        图表的原始文本表示
    format : str | None
        图表格式（如 "plotly"）
    fig : Any | None
        图形对象（不会序列化到 API 响应）
    """

    content: dict[str, Any] | None = Field(
        default=None,
        description="图表的原始文本表示",
    )
    format: str | None = Field(
        default=None,
        description="图表格式",
    )
    fig: Any | None = Field(
        default=None,
        description="图形对象",
        json_schema_extra={"exclude_from_api": True},
    )
    model_config = ConfigDict(validate_assignment=True)

    def __repr__(self) -> str:
        """返回字符串表示"""
        return f"{self.__class__.__name__}\n\n" + "\n".join(
            f"{k}: {v}" for k, v in self.model_dump().items()
        )
