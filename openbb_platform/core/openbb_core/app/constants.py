"""OpenBB 平台常量定义

本模块定义了 OpenBB 平台使用的全局常量。

路径说明
--------

- HOME_DIRECTORY: 用户主目录
- OPENBB_DIRECTORY: OpenBB 配置目录 (~/.openbb_platform)
- USER_SETTINGS_PATH: 用户设置文件路径
- SYSTEM_SETTINGS_PATH: 系统设置文件路径
"""

from pathlib import Path

# 用户主目录
HOME_DIRECTORY = Path.home()

# OpenBB 平台配置目录
OPENBB_DIRECTORY = Path(HOME_DIRECTORY, ".openbb_platform")

# 用户设置文件路径
USER_SETTINGS_PATH = Path(OPENBB_DIRECTORY, "user_settings.json")

# 系统设置文件路径
SYSTEM_SETTINGS_PATH = Path(OPENBB_DIRECTORY, "system_settings.json")
