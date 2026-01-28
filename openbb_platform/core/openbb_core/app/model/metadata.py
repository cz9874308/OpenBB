"""元数据模型模块

本模块定义了命令执行的元数据模型。
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from openbb_core.provider.abstract.data import Data
from pydantic import BaseModel, Field, field_validator


class Metadata(BaseModel):
    """命令执行元数据

    记录命令执行的相关信息，包括参数、耗时、路由和时间戳。

    Attributes
    ----------
    arguments : dict[str, Any]
        命令参数
    duration : int
        执行耗时（纳秒）
    route : str
        命令路由
    timestamp : datetime
        执行开始时间戳
    """

    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="命令参数",
    )
    duration: int = Field(
        description="执行耗时（纳秒）"
    )
    route: str = Field(description="命令路由")
    timestamp: datetime = Field(description="执行开始时间戳")

    def __repr__(self) -> str:
        """返回字符串表示"""
        return f"{self.__class__.__name__}\n\n" + "\n".join(
            f"{k}: {v}" for k, v in self.model_dump().items()
        )

    @field_validator("arguments")
    @classmethod
    def scale_arguments(cls, v):
        """缩放参数

        此函数用于限制命令输入参数的大小。
        如果类型是以下之一：Data、List[Data]、DataFrame、List[DataFrame]、
        Series、List[Series] 或 ndarray，则参数值会被替换为包含类型和列名的字典。
        如果类型不是上述之一，则保留原值或截断到 80 个字符。
        """
        # pylint: disable=import-outside-toplevel
        from inspect import isclass  # noqa
        from numpy import ndarray  # noqa
        from pandas import DataFrame, Series  # noqa

        arguments: dict[str, Any] = {}
        for item in ["provider_choices", "standard_params", "extra_params"]:
            arguments[item] = {}
            # The item could be class or it could a dictionary.
            v_item = (
                v.__dict__.get(item, {}) if not isinstance(v, dict) else v.get(item, {})
            )
            # The item might not be a dictionary yet.
            v_item = v_item if isinstance(v_item, dict) else v_item.__dict__
            for arg, arg_val in v_item.items():
                new_arg_val: str | dict[str, Sequence[Any]] | None = None

                # Data
                if isclass(type(arg_val)) and issubclass(type(arg_val), Data):
                    new_arg_val = {
                        "type": f"{type(arg_val).__name__}",
                        "columns": list(arg_val.model_dump().keys()),
                    }

                # List[Data]
                if isinstance(arg_val, list) and issubclass(type(arg_val[0]), Data):
                    _columns = [list(d.model_dump().keys()) for d in arg_val]
                    ld_columns = (
                        item for sublist in _columns for item in sublist
                    )  # flatten
                    new_arg_val = {
                        "type": f"List[{type(arg_val[0]).__name__}]",
                        "columns": list(set(ld_columns)),
                    }

                # DataFrame
                elif isinstance(arg_val, DataFrame):
                    df_columns = (
                        list(arg_val.index.names) + arg_val.columns.tolist()
                        if any(index is not None for index in list(arg_val.index.names))
                        else arg_val.columns.tolist()
                    )
                    new_arg_val = {
                        "type": f"{type(arg_val).__name__}",
                        "columns": df_columns,
                    }

                # List[DataFrame]
                elif isinstance(arg_val, list) and issubclass(
                    type(arg_val[0]), DataFrame
                ):
                    ldf_columns = [
                        (
                            list(df.index.names) + df.columns.tolist()
                            if any(index is not None for index in list(df.index.names))
                            else df.columns.tolist()
                        )
                        for df in arg_val
                    ]
                    new_arg_val = {
                        "type": f"List[{type(arg_val[0]).__name__}]",
                        "columns": ldf_columns,
                    }

                # Series
                elif isinstance(arg_val, Series):
                    new_arg_val = {
                        "type": f"{type(arg_val).__name__}",
                        "columns": list(arg_val.index.names) + [arg_val.name],
                    }

                # List[Series]
                elif isinstance(arg_val, list) and isinstance(arg_val[0], Series):
                    ls_columns = [
                        (
                            list(series.index.names) + [series.name]
                            if any(
                                index is not None for index in list(series.index.names)
                            )
                            else series.name
                        )
                        for series in arg_val
                    ]
                    new_arg_val = {
                        "type": f"List[{type(arg_val[0]).__name__}]",
                        "columns": ls_columns,
                    }

                # ndarray
                elif isinstance(arg_val, ndarray):
                    new_arg_val = {
                        "type": f"{type(arg_val).__name__}",
                        "columns": list(arg_val.dtype.names or []),
                    }

                else:
                    str_repr_arg_val = str(arg_val)
                    if len(str_repr_arg_val) > 80:
                        new_arg_val = str_repr_arg_val[:80]

                arguments[item][arg] = new_arg_val or arg_val

        return arguments
