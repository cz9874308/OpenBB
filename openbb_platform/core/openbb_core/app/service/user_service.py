"""用户服务模块

本模块提供用户设置的读写和管理功能。
"""

import json
from collections.abc import MutableMapping
from functools import reduce
from pathlib import Path
from typing import Any

from openbb_core.app.constants import USER_SETTINGS_PATH
from openbb_core.app.model.abstract.singleton import SingletonMeta
from openbb_core.app.model.user_settings import UserSettings


class UserService(metaclass=SingletonMeta):
    """用户服务

    管理用户设置的读取、写入和合并。

    Attributes
    ----------
    USER_SETTINGS_PATH : Path
        用户设置文件路径
    USER_SETTINGS_ALLOWED_FIELD_SET : set
        允许持久化的字段集合
    default_user_settings : UserSettings
        默认用户设置
    """

    USER_SETTINGS_PATH = USER_SETTINGS_PATH
    USER_SETTINGS_ALLOWED_FIELD_SET = {"credentials", "preferences", "defaults"}

    def __init__(
        self,
        default_user_settings: UserSettings | None = None,
    ):
        """初始化用户服务

        Parameters
        ----------
        default_user_settings : UserSettings | None, optional
            默认用户设置，默认从文件读取
        """
        self._default_user_settings = default_user_settings or self.read_from_file()

    @classmethod
    def read_from_file(cls, path: Path | None = None) -> UserSettings:
        """从 JSON 文件读取用户设置

        Parameters
        ----------
        path : Path | None, optional
            文件路径，默认使用 USER_SETTINGS_PATH

        Returns
        -------
        UserSettings
            用户设置对象
        """
        path = path or cls.USER_SETTINGS_PATH

        return (
            UserSettings.model_validate(json.loads(path.read_text(encoding="utf-8")))
            if path.exists()
            else UserSettings()
        )

    @classmethod
    def write_to_file(
        cls,
        user_settings: UserSettings,
        path: Path | None = None,
    ) -> None:
        """将用户设置写入 JSON 文件

        Parameters
        ----------
        user_settings : UserSettings
            要写入的用户设置
        path : Path | None, optional
            文件路径，默认使用 USER_SETTINGS_PATH
        """
        path = path or cls.USER_SETTINGS_PATH
        user_settings_json = user_settings.model_dump_json(
            indent=4, include=cls.USER_SETTINGS_ALLOWED_FIELD_SET, exclude_defaults=True
        )
        path.write_text(user_settings_json, encoding="utf-8")

    @staticmethod
    def _merge_dicts(list_of_dicts: list[dict[str, Any]]) -> dict[str, Any]:
        """合并字典列表

        Parameters
        ----------
        list_of_dicts : list[dict[str, Any]]
            要合并的字典列表

        Returns
        -------
        dict[str, Any]
            合并后的字典
        """

        def recursive_merge(d1: dict, d2: dict) -> dict:
            """递归合并字典，如果 d2 的值不为 None 则合并到 d1"""
            for k, v in d1.items():
                if k in d2 and all(isinstance(e, MutableMapping) for e in (v, d2[k])):
                    d2[k] = recursive_merge(v, d2[k])

            d3 = d1.copy()
            d3.update((k, v) for k, v in d2.items() if v is not None)
            return d3

        result: dict[str, Any] = {}
        for d in list_of_dicts:
            result = reduce(recursive_merge, (result, d))
        return result

    @property
    def default_user_settings(self) -> UserSettings:
        """获取默认用户设置"""
        return self._default_user_settings

    @default_user_settings.setter
    def default_user_settings(self, default_user_settings: UserSettings) -> None:
        """设置默认用户设置"""
        self._default_user_settings = default_user_settings
