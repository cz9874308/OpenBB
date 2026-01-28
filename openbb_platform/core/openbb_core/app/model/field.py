"""OpenBB 自定义字段模块

本模块定义了 OpenBB 的自定义字段类型。
"""

from typing import Any

from pydantic.fields import FieldInfo


class OpenBBField(FieldInfo):
    """OpenBB 自定义字段

    扩展 Pydantic 的 FieldInfo，支持 choices 属性。

    Attributes
    ----------
    choices : list[Any] | None
        字段的可选值列表
    """

    def __repr__(self):
        """重写字符串表示"""
        # 使用 repr() 避免解码特殊字符如 \n
        if self.choices:
            return f"OpenBBField(description={repr(self.description)}, choices={repr(self.choices)})"
        return f"OpenBBField(description={repr(self.description)})"

    def __init__(self, description: str, choices: list[Any] | None = None):
        """初始化 OpenBBField

        Parameters
        ----------
        description : str
            字段描述
        choices : list[Any] | None, optional
            可选值列表，默认为 None
        """
        json_schema_extra = {"choices": choices} if choices else None
        super().__init__(description=description, json_schema_extra=json_schema_extra)  # type: ignore[arg-type]

    @property
    def choices(self) -> list[Any] | None:
        """获取可选值列表"""
        if self.json_schema_extra:
            return self.json_schema_extra.get("choices")  # type: ignore[union-attr,return-value]
        return None
