"""OpenBB CLI 控制台模块

提供富文本控制台输出，支持面板显示和主题样式。
"""

from typing import TYPE_CHECKING, Any

from rich import panel
from rich.console import Console as RichConsole
from rich.text import Text
from rich.theme import Theme

from openbb_cli.config.menu_text import RICH_TAGS

if TYPE_CHECKING:
    from openbb_cli.models.settings import Settings


class Console:
    """富文本控制台类。

    封装 Rich 控制台，支持面板输出。
    """

    def __init__(
        self,
        settings: "Settings",
        style: dict[str, Any] | None = None,
    ):
        """初始化控制台类。"""
        self._console = RichConsole(
            theme=Theme(style),
            highlight=False,
            soft_wrap=True,
        )
        self._settings = settings
        self.menu_text = ""
        self.menu_path = ""

    @staticmethod
    def _filter_rich_tags(text):
        """从文本中过滤 Rich 标签。"""
        for val in RICH_TAGS:
            text = text.replace(val, "")

        return text

    @staticmethod
    def _blend_text(
        message: str, color1: tuple[int, int, int], color2: tuple[int, int, int]
    ) -> Text:
        """将文本从一种颜色渐变到另一种颜色。"""
        text = Text(message)
        r1, g1, b1 = color1
        r2, g2, b2 = color2
        dr = r2 - r1
        dg = g2 - g1
        db = b2 - b1
        size = len(text) + 5
        for index in range(size):
            blend = index / size
            color = f"#{int(r1 + dr * blend):02X}{int(g1 + dg * blend):02X}{int(b1 + db * blend):02X}"
            text.stylize(color, index, index + 1)
        return text

    def print(self, *args, **kwargs):
        """将文本打印到控制台。"""
        if kwargs and "text" in list(kwargs) and "menu" in list(kwargs):
            if not self._settings.TEST_MODE:
                if self._settings.ENABLE_RICH_PANEL:
                    if self._settings.SHOW_VERSION:
                        version = self._settings.VERSION
                        version = f"[param]OpenBB Platform CLI v{version}[/param] (https://openbb.co)"
                    else:
                        version = (
                            "[param]OpenBB Platform CLI[/param] (https://openbb.co)"
                        )
                    self._console.print(
                        panel.Panel(
                            "\n" + kwargs["text"],
                            title=kwargs["menu"],
                            subtitle_align="right",
                            subtitle=version,
                        )
                    )

                else:
                    self._console.print(kwargs["text"])
            else:
                print(self._filter_rich_tags(kwargs["text"]))  # noqa: T201
        elif not self._settings.TEST_MODE:
            self._console.print(*args, **kwargs)
        else:
            print(*args, **kwargs)  # noqa: T201

    def input(self, *args, **kwargs):
        """获取用户输入。"""
        self.print(*args, **kwargs, end="")
        return input()
