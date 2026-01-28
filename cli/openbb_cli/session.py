"""CLI 会话管理模块

管理 CLI 会话状态，包括用户设置、样式、控制台和对象注册表。
"""

import sys
from pathlib import Path

from openbb import obb
from openbb_charting.core.backend import create_backend, get_backend
from openbb_core.app.model.abstract.singleton import SingletonMeta
from openbb_core.app.model.charts.charting_settings import ChartingSettings
from openbb_core.app.model.user_settings import UserSettings as User
from prompt_toolkit import PromptSession

from openbb_cli.argparse_translator.obbject_registry import Registry
from openbb_cli.config.completer import CustomFileHistory
from openbb_cli.config.console import Console
from openbb_cli.config.constants import HIST_FILE_PROMPT
from openbb_cli.config.style import Style
from openbb_cli.models.settings import Settings


def _get_backend():
    """获取平台图表后端。"""
    try:
        return get_backend()
    except ValueError:
        # backend might not be created yet
        charting_settings = ChartingSettings(
            system_settings=obb.system,  # type: ignore
            user_settings=obb.user,  # type: ignore
        )
        create_backend(charting_settings)
        get_backend().start(debug=charting_settings.debug_mode)  # type: ignore
        return get_backend()


class Session(metaclass=SingletonMeta):
    """CLI 会话类。

    管理整个 CLI 生命周期的状态和资源。
    """

    def __init__(self):
        """初始化会话。"""

        self._obb = obb
        self._settings = Settings()
        self._style = Style(
            style=self._settings.RICH_STYLE,
            directory=Path(self._obb.user.preferences.user_styles_directory),  # type: ignore[union-attr]
        )
        self._console = Console(
            settings=self._settings, style=self._style.console_style
        )
        self._prompt_session = self._get_prompt_session()
        self._obbject_registry = Registry()

        self._backend = _get_backend()

    @property
    def user(self) -> User:
        """获取平台用户。"""
        return self._obb.user  # type: ignore[union-attr]

    @property
    def settings(self) -> Settings:
        """获取 CLI 设置。"""
        return self._settings

    @property
    def style(self) -> Style:
        """获取 CLI 样式。"""
        return self._style

    @property
    def console(self) -> Console:
        """获取控制台。"""
        return self._console

    @property
    def obbject_registry(self) -> Registry:
        """获取 OBBject 注册表。"""
        return self._obbject_registry

    @property
    def prompt_session(self) -> PromptSession | None:
        """获取提示会话。"""
        return self._prompt_session

    def _get_prompt_session(self) -> PromptSession | None:
        """初始化提示会话。"""
        try:
            if sys.stdin.isatty():
                prompt_session: PromptSession | None = PromptSession(
                    history=CustomFileHistory(str(HIST_FILE_PROMPT))
                )
            else:
                prompt_session = None
        except Exception:
            prompt_session = None

        return prompt_session

    def max_obbjects_exceeded(self) -> bool:
        """检查是否超过最大 OBBject 数量。"""
        return (
            len(self.obbject_registry.all) >= self.settings.N_TO_KEEP_OBBJECT_REGISTRY
        )
