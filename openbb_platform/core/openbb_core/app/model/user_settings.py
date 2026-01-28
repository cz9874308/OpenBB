"""用户设置模型模块

本模块定义了用户设置的顶层容器模型。
"""

import json
import os
import warnings

from openbb_core.app.constants import USER_SETTINGS_PATH
from openbb_core.app.model.abstract.tagged import Tagged
from openbb_core.app.model.credentials import Credentials
from openbb_core.app.model.defaults import Defaults
from openbb_core.app.model.preferences import Preferences
from pydantic import Field


class UserSettings(Tagged):
    """用户设置

    用户配置的顶层容器，包含凭证、偏好和默认值。

    设置会从 ~/.openbb_platform/user_settings.json 自动加载。

    Attributes
    ----------
    credentials : Credentials
        API 凭证
    preferences : Preferences
        用户偏好设置
    defaults : Defaults
        命令默认参数
    """

    credentials: Credentials = Field(default_factory=Credentials)
    preferences: Preferences = Field(default_factory=Preferences)
    defaults: Defaults = Field(default_factory=Defaults)

    def __init__(self, **kwargs):
        """初始化用户设置

        如果用户设置文件存在，则从文件加载设置。
        """
        # Check if user settings file exists and load from it
        if os.path.exists(USER_SETTINGS_PATH):
            try:
                with open(USER_SETTINGS_PATH) as f:
                    file_settings = json.load(f)
                # Initialize with settings from file
                super().__init__(**{k: v for k, v in file_settings.items() if v})
            except (json.JSONDecodeError, OSError) as e:
                warnings.warn(
                    f"Error loading user settings from file: {e}",
                    stacklevel=2,
                    category=UserWarning,
                )
                # Fall back to defaults if file can't be read
                super().__init__(**kwargs)
        else:
            # Use defaults if file doesn't exist
            super().__init__(**kwargs)

    def __repr__(self) -> str:
        """返回对象的可读字符串表示"""
        return f"{self.__class__.__name__}\n\n" + "\n".join(
            f"{k}: {v}" for k, v in self.model_dump().items()
        )
