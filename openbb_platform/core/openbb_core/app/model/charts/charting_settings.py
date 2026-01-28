"""图表设置模块

本模块定义了图表相关的配置设置。
"""

import importlib
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from openbb_core.env import Env

if TYPE_CHECKING:
    from openbb_core.app.model.system_settings import SystemSettings
    from openbb_core.app.model.user_settings import UserSettings


# pylint: disable=too-many-instance-attributes
class ChartingSettings:
    """图表设置

    汇集图表相关的系统和用户设置。

    Attributes
    ----------
    logging_suppress : bool
        是否抑制日志
    version : str
        OpenBB 版本
    python_version : str
        Python 版本
    test_mode : bool
        测试模式
    debug_mode : bool
        调试模式
    headless : bool
        无头模式
    user_data_directory : str
        用户数据目录
    user_exports_directory : str
        用户导出目录
    user_styles_directory : str
        用户样式目录
    chart_style : str
        图表样式
    table_style : str
        表格样式
    """

    def __init__(
        self,
        user_settings: Optional["UserSettings"] = None,
        system_settings: Optional["SystemSettings"] = None,
    ):
        """初始化图表设置

        Parameters
        ----------
        user_settings : UserSettings | None, optional
            用户设置，默认自动创建
        system_settings : SystemSettings | None, optional
            系统设置，默认自动创建
        """
        user_settings_module = importlib.import_module(
            "openbb_core.app.model.user_settings", "UserSettings"
        )
        system_settings_module = importlib.import_module(
            "openbb_core.app.model.system_settings", "SystemSettings"
        )

        UserSettings = user_settings_module.UserSettings
        SystemSettings = system_settings_module.SystemSettings
        user_settings = user_settings or UserSettings()
        system_settings = system_settings or SystemSettings()

        user_data_directory = (
            str(Path.home() / "OpenBBUserData")
            if not user_settings.preferences
            else user_settings.preferences.data_directory
        )

        # System
        self.logging_suppress: bool = system_settings.logging_suppress
        self.version: str = system_settings.version
        self.python_version: str = system_settings.python_version
        self.test_mode = system_settings.test_mode
        self.debug_mode: bool = system_settings.debug_mode or Env().DEBUG_MODE
        self.headless: bool = system_settings.headless
        # User
        self.user_data_directory: str = user_data_directory
        self.user_exports_directory = user_settings.preferences.export_directory
        self.user_styles_directory = user_settings.preferences.user_styles_directory
        # Theme
        self.chart_style: str = user_settings.preferences.chart_style
        self.table_style = user_settings.preferences.table_style
