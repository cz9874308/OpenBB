"""偏好设置模块

本模块定义了 OpenBB 平台的用户偏好设置。
"""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, PositiveInt


class Preferences(BaseModel):
    """用户偏好设置

    定义 OpenBB 平台的用户可配置选项。

    Attributes
    ----------
    cache_directory : str
        缓存目录路径
    chart_style : Literal["dark", "light"]
        图表样式（深色/浅色）
    data_directory : str
        数据目录路径
    export_directory : str
        导出目录路径
    metadata : bool
        是否在 OBBject 中包含元数据
    output_type : str
        Python SDK 默认输出类型
    request_timeout : PositiveInt
        请求超时时间（秒）
    show_warnings : bool
        是否显示警告
    table_style : Literal["dark", "light"]
        表格样式（深色/浅色）
    user_styles_directory : str
        用户自定义样式目录路径
    """

    cache_directory: str = str(Path.home() / "OpenBBUserData" / "cache")
    chart_style: Literal["dark", "light"] = "dark"
    data_directory: str = str(Path.home() / "OpenBBUserData")
    export_directory: str = str(Path.home() / "OpenBBUserData" / "exports")
    metadata: bool = True
    output_type: Literal[
        "OBBject", "dataframe", "polars", "numpy", "dict", "chart", "llm"
    ] = Field(
        default="OBBject",
        description="Python 默认输出类型",
        validate_default=True,
    )
    request_timeout: PositiveInt = 60
    show_warnings: bool = False
    table_style: Literal["dark", "light"] = "dark"
    user_styles_directory: str = str(Path.home() / "OpenBBUserData" / "styles" / "user")

    model_config = ConfigDict(validate_assignment=True)

    def __repr__(self) -> str:
        """返回模型的字符串表示"""
        return f"{self.__class__.__name__}\n\n" + "\n".join(
            f"{k}: {v}" for k, v in self.model_dump().items()
        )
