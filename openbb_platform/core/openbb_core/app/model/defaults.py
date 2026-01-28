"""默认值模型模块

本模块定义了命令的默认参数设置。
"""

from typing import Any
from warnings import warn

from openbb_core.app.model.abstract.warning import OpenBBWarning
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Defaults(BaseModel):
    """默认值设置

    存储命令的默认参数配置，允许用户为特定命令预设参数值。

    Attributes
    ----------
    commands : dict[str, dict[str, Any]]
        命令路径到默认参数的映射

    示例
    ----

    在 user_settings.json 中配置：

    ```json
    {
        "defaults": {
            "commands": {
                "equity.price.historical": {
                    "provider": ["yfinance"]
                }
            }
        }
    }
    ```
    """

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)

    commands: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        alias="routes",
    )

    def __repr__(self) -> str:
        """返回字符串表示"""
        return f"{self.__class__.__name__}\n\n" + "\n".join(
            f"{k}: {v}" for k, v in self.model_dump().items()
        )

    @model_validator(mode="before")
    @classmethod
    def validate_before(cls, values: dict) -> dict:
        """验证模型（前置处理）

        将旧版 'routes' 键转换为 'commands' 键，
        并规范化命令路径格式。
        """
        key = "commands"
        if "routes" in values:
            if not values.get("routes"):
                del values["routes"]
            show_warnings = values.get("preferences", {}).get("show_warnings")
            if show_warnings is False or show_warnings in ["False", "false"]:
                warn(
                    message="The 'routes' key is deprecated within 'defaults' of 'user_settings.json'."
                    + " Suppress this warning by updating the key to 'commands'.",
                    category=OpenBBWarning,
                )
                key = "routes"

        new_values: dict = {"commands": {}}
        for k, v in values.get(key, {}).items():
            clean_k = k.strip("/").replace("/", ".")
            provider = v.get("provider") if v else None
            if isinstance(provider, str):
                v["provider"] = [provider]
            new_values["commands"][clean_k] = v

        return new_values

    def update(self, incoming: "Defaults"):
        """更新当前默认值

        Parameters
        ----------
        incoming : Defaults
            要合并的默认值对象
        """
        incoming_commands = incoming.model_dump(exclude_none=True).get("commands", {})
        self.__dict__["commands"].update(incoming_commands)
