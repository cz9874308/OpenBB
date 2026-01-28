"""扩展加载器模块

本模块定义了 ExtensionLoader 类，负责加载和管理 OpenBB 平台的扩展。

扩展类型
--------

OpenBB 平台支持三种类型的扩展：

1. **Core 扩展** (openbb_core_extension): 核心功能扩展，如 equity、crypto 等
2. **Provider 扩展** (openbb_provider_extension): 数据提供者扩展，如 yfinance、fmp 等
3. **OBBject 扩展** (openbb_obbject_extension): 输出对象扩展，如 charting 等

加载机制
--------

扩展通过 Python 的 entry_points 机制注册和发现。
ExtensionLoader 作为单例，在首次访问时加载所有扩展。

```
pyproject.toml
    ↓
entry_points 定义
    ↓
ExtensionLoader._sorted_entry_points()
    ↓
_load_entry_points()
    ↓
Router / Provider / Extension 对象
```
"""

from enum import Enum
from functools import lru_cache
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, FastAPI
from importlib_metadata import EntryPoint, EntryPoints, entry_points
from openbb_core.app.model.abstract.singleton import SingletonMeta
from openbb_core.app.model.extension import Extension

if TYPE_CHECKING:
    from openbb_core.app.router import Router
    from openbb_core.provider.abstract.provider import Provider


class OpenBBGroups(Enum):
    """OpenBB 扩展组枚举

    定义 OpenBB 平台支持的扩展组类型。

    Attributes
    ----------
    core : str
        核心扩展组，值为 "openbb_core_extension"
    provider : str
        数据提供者扩展组，值为 "openbb_provider_extension"
    obbject : str
        输出对象扩展组，值为 "openbb_obbject_extension"
    """

    core = "openbb_core_extension"
    provider = "openbb_provider_extension"
    obbject = "openbb_obbject_extension"

    @staticmethod
    def groups() -> list[str]:
        """获取所有扩展组名称"""
        return [
            OpenBBGroups.core.value,
            OpenBBGroups.provider.value,
            OpenBBGroups.obbject.value,
        ]


class ExtensionLoader(metaclass=SingletonMeta):
    """扩展加载器类

    作为单例模式实现，负责加载和管理所有 OpenBB 扩展。

    ExtensionLoader 通过 Python entry_points 机制发现和加载扩展，
    并提供统一的接口访问已加载的扩展对象。

    Attributes
    ----------
    on_command_output_callbacks : dict[str, list[Extension]]
        命令输出回调映射，路由路径到扩展列表
    obbject_entry_points : EntryPoints
        OBBject 扩展的入口点
    core_entry_points : EntryPoints
        核心扩展的入口点
    provider_entry_points : EntryPoints
        数据提供者扩展的入口点
    obbject_objects : dict[str, Extension]
        已加载的 OBBject 扩展对象
    core_objects : dict[str, Router]
        已加载的核心扩展路由器
    provider_objects : dict[str, Provider]
        已加载的数据提供者对象
    """

    def __init__(
        self,
    ) -> None:
        """初始化扩展加载器"""
        self._obbject_entry_points: EntryPoints = self._sorted_entry_points(
            group=OpenBBGroups.obbject.value
        )
        self._core_entry_points: EntryPoints = self._sorted_entry_points(
            group=OpenBBGroups.core.value
        )
        self._provider_entry_points: EntryPoints = self._sorted_entry_points(
            group=OpenBBGroups.provider.value
        )
        self._obbject_objects: dict[str, Extension] = {}
        self._core_objects: dict[str, Router] = {}
        self._provider_objects: dict[str, Provider] = {}
        self._on_command_output_callbacks: dict[str, list[Extension]] = {}
        self._register_command_output_callbacks()

    @property
    def on_command_output_callbacks(self) -> dict[str, list[Extension]]:
        """获取命令输出回调映射"""
        return self._on_command_output_callbacks

    def _register_command_output_callbacks(self) -> None:
        """注册作用于命令输出的扩展回调"""
        for ext in self.obbject_objects.values():
            if ext.on_command_output:
                paths = ext.command_output_paths or ["*"]
                for path in paths:
                    if path not in self._on_command_output_callbacks:
                        self._on_command_output_callbacks[path] = []
                    self._on_command_output_callbacks[path].append(ext)

    @property
    def obbject_entry_points(self) -> EntryPoints:
        """获取 OBBject 扩展入口点"""
        return self._obbject_entry_points

    @property
    def core_entry_points(self) -> EntryPoints:
        """获取核心扩展入口点"""
        return self._core_entry_points

    @property
    def provider_entry_points(self) -> EntryPoints:
        """获取数据提供者扩展入口点"""
        return self._provider_entry_points

    @property
    def entry_points(self) -> list[EntryPoints]:
        """获取所有入口点列表"""
        return [
            self._core_entry_points,
            self._provider_entry_points,
            self._obbject_entry_points,
        ]

    @staticmethod
    def _get_entry_point(
        entry_points_: EntryPoints, ext_name: str
    ) -> EntryPoint | None:
        """根据扩展名称获取对应的入口点

        Parameters
        ----------
        entry_points_ : EntryPoints
            入口点列表
        ext_name : str
            扩展名称

        Returns
        -------
        EntryPoint | None
            对应的入口点，如果未找到则返回 None
        """
        return next((ep for ep in entry_points_ if ep.name == ext_name), None)

    def get_obbject_entry_point(self, ext_name: str) -> EntryPoint | None:
        """获取 OBBject 扩展的入口点"""
        return self._get_entry_point(self._obbject_entry_points, ext_name)

    def get_core_entry_point(self, ext_name: str) -> EntryPoint | None:
        """获取核心扩展的入口点"""
        return self._get_entry_point(self._core_entry_points, ext_name)

    def get_provider_entry_point(self, ext_name: str) -> EntryPoint | None:
        """获取数据提供者扩展的入口点"""
        return self._get_entry_point(self._provider_entry_points, ext_name)

    @property
    @lru_cache
    def obbject_objects(self) -> dict[str, Extension]:
        """获取 OBBject 扩展对象字典"""
        self._obbject_objects = self._load_entry_points(
            self._obbject_entry_points, OpenBBGroups.obbject
        )
        return self._obbject_objects

    @property
    @lru_cache
    def core_objects(self) -> dict[str, "Router"]:
        """获取核心扩展对象字典"""
        self._core_objects = self._load_entry_points(
            self._core_entry_points, OpenBBGroups.core
        )
        return self._core_objects

    @property
    @lru_cache
    def provider_objects(self) -> dict[str, "Provider"]:
        """获取数据提供者对象字典"""
        self._provider_objects = self._load_entry_points(
            self._provider_entry_points, OpenBBGroups.provider
        )
        return self._provider_objects

    @staticmethod
    def _sorted_entry_points(group: str) -> EntryPoints:
        """获取排序后的入口点"""
        return sorted(entry_points(group=group))  # type: ignore

    def _load_entry_points(
        self, entry_points_: EntryPoints, group: OpenBBGroups
    ) -> dict[str, Any]:
        """加载入口点并返回对象字典

        Parameters
        ----------
        entry_points_ : EntryPoints
            入口点列表
        group : OpenBBGroups
            扩展组类型

        Returns
        -------
        dict[str, Any]
            扩展名称到对象的映射
        """

        def load_obbject(eps: EntryPoints) -> dict[str, Extension]:
            """加载 OBBject 扩展对象"""
            return {
                ep.name: entry
                for ep in eps
                if isinstance((entry := ep.load()), Extension)
            }

        def load_core(eps: EntryPoints) -> dict[str, "Router"]:
            """加载核心扩展对象"""
            # pylint: disable=import-outside-toplevel
            from openbb_core.app.router import Router

            entries: dict[str, Router] = {}
            for ep in eps:
                entry = ep.load()
                if isinstance(entry, Router):
                    entries[ep.name] = entry
                    continue
                if isinstance(entry, FastAPI):
                    entry = entry.router
                if isinstance(entry, APIRouter):
                    entries[ep.name] = Router.from_fastapi(entry)
            return entries

        def load_provider(eps: EntryPoints) -> dict[str, "Provider"]:
            """加载数据提供者对象"""
            # pylint: disable=import-outside-toplevel
            from openbb_core.provider.abstract.provider import Provider

            entries: dict = {}
            for ep in eps:
                try:
                    if isinstance((entry := ep.load()), Provider):
                        entries[ep.name] = entry
                except ModuleNotFoundError:
                    continue
            return entries

        func = {
            OpenBBGroups.obbject: load_obbject,
            OpenBBGroups.core: load_core,
            OpenBBGroups.provider: load_provider,
        }
        return func[group](entry_points_)  # type: ignore
