"""OpenBB 平台系统设置模块

本模块定义了 OpenBB 平台的系统级设置。
"""

import json
import platform as pl  # 避免与变量名冲突
from pathlib import Path
from typing import Literal

from openbb_core.app.constants import (
    HOME_DIRECTORY,
    OPENBB_DIRECTORY,
    SYSTEM_SETTINGS_PATH,
    USER_SETTINGS_PATH,
)
from openbb_core.app.model.abstract.tagged import Tagged
from openbb_core.app.model.api_settings import APISettings
from openbb_core.app.model.python_settings import PythonSettings
from openbb_core.app.version import CORE_VERSION, VERSION
from openbb_core.env import Env
from pydantic import ConfigDict, Field, field_validator, model_validator


class SystemSettings(Tagged):
    """系统设置模型

    包含 OpenBB 平台的系统级配置，如日志设置、API 设置等。
    此模型是不可变的（frozen=True）。

    Attributes
    ----------
    os : str
        操作系统名称
    python_version : str
        Python 版本
    platform : str
        平台信息
    version : str
        OpenBB 版本
    core : str
        OpenBB Core 版本
    logging_* : various
        日志相关设置
    api_settings : APISettings
        FastAPI 配置
    python_settings : PythonSettings
        Python SDK 配置
    debug_mode : bool
        调试模式
    test_mode : bool
        测试模式
    """

    # System section
    os: str = str(pl.system())
    python_version: str = str(pl.python_version())
    platform: str = str(pl.platform())

    # OpenBB section
    version: str = VERSION
    core: str = CORE_VERSION
    home_directory: str = str(HOME_DIRECTORY)
    openbb_directory: str = str(OPENBB_DIRECTORY)
    user_settings_path: str = str(USER_SETTINGS_PATH)
    system_settings_path: str = str(SYSTEM_SETTINGS_PATH)

    # Logging section
    logging_app_name: Literal["platform"] = "platform"
    logging_commit_hash: str | None = None
    logging_frequency: Literal["D", "H", "M", "S"] = "H"
    logging_handlers: list[str] = Field(default_factory=lambda: ["file"])
    logging_rolling_clock: bool = False
    logging_verbosity: int = 20
    logging_sub_app: Literal["python", "api", "pro", "cli"] = "python"
    logging_suppress: bool = True

    # API section
    api_settings: APISettings = Field(default_factory=APISettings)

    # Python section
    python_settings: PythonSettings = Field(default_factory=PythonSettings)

    # Others
    debug_mode: bool = False
    test_mode: bool = False
    headless: bool = False
    allow_mutable_extensions: bool = getattr(Env(), "ALLOW_MUTABLE_EXTENSIONS", False)
    allow_on_command_output: bool = getattr(Env(), "ALLOW_ON_COMMAND_OUTPUT", False)

    model_config = ConfigDict(validate_assignment=True, frozen=True)

    def __repr__(self) -> str:
        """返回模型的字符串表示"""
        return f"{self.__class__.__name__}\n\n" + "\n".join(
            f"{k}: {v}" for k, v in self.model_dump().items()
        )

    @staticmethod
    def create_json(path: Path, template: dict | None = None) -> None:
        """创建 JSON 配置文件

        Parameters
        ----------
        path : Path
            文件路径
        template : dict | None, optional
            模板内容，默认为空字典
        """
        path.write_text(json.dumps(obj=template or {}, indent=4), encoding="utf-8")

    # TODO: 弄清楚为什么这与文档说的相反
    # https://docs.pydantic.dev/latest/concepts/validators/#model-validators
    # 根据文档第一个参数应该是 self，但只有 cls 才有效
    @model_validator(mode="after")  # type: ignore
    @classmethod
    def create_openbb_directory(cls, values: "SystemSettings") -> "SystemSettings":
        """如果 OpenBB 目录不存在则创建"""
        obb_dir = Path(values.openbb_directory).resolve()
        user_settings = Path(values.user_settings_path).resolve()
        system_settings = Path(values.system_settings_path).resolve()
        obb_dir.mkdir(parents=True, exist_ok=True)

        if not user_settings.exists():
            cls.create_json(
                user_settings,
                {"credentials": {}, "preferences": {}, "defaults": {"commands": {}}},
            )

        if not system_settings.exists():
            cls.create_json(system_settings, {})

        return values

    @field_validator("logging_handlers")
    @classmethod
    def validate_logging_handlers(cls, v):
        """验证日志处理器

        确保日志处理器是有效的类型。

        Parameters
        ----------
        v : list[str]
            日志处理器列表

        Returns
        -------
        list[str]
            验证后的日志处理器列表

        Raises
        ------
        ValueError
            如果处理器类型无效
        """
        for value in v:
            if value not in ["stdout", "stderr", "noop", "file"]:
                raise ValueError("无效的日志处理器")
        return v
