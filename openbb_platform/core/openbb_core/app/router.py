"""OpenBB 路由模块

本模块定义了 OpenBB 平台的路由系统，负责将 API 端点映射到命令处理函数。

核心组件
--------

- **Router**: 路由器类，封装 FastAPI 的 APIRouter，提供命令注册功能
- **SignatureInspector**: 签名检查器，用于验证和完善函数签名
- **CommandMap**: 命令映射，维护路由路径到命令函数的映射关系
- **RouterLoader**: 路由加载器，从扩展模块加载路由

工作原理
--------

```
扩展模块 → RouterLoader → Router → CommandMap → API 端点
                                      ↓
                              SignatureInspector
                                      ↓
                              依赖注入 + 类型验证
```

路由注册流程
------------

1. 扩展模块定义路由函数并使用 @router.command 装饰
2. SignatureInspector 验证函数签名，注入依赖
3. RouterLoader 加载所有扩展路由
4. CommandMap 建立路由到函数的映射
"""

import traceback
import warnings
from collections.abc import Callable
from functools import lru_cache
from inspect import isclass
from typing import (
    Annotated,
    Any,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

from fastapi import APIRouter, Depends
from openbb_core.app.deprecation import DeprecationSummary, OpenBBDeprecationWarning
from openbb_core.app.extension_loader import ExtensionLoader
from openbb_core.app.model.abstract.warning import OpenBBWarning
from openbb_core.app.model.example import filter_list
from openbb_core.app.model.obbject import OBBject
from openbb_core.app.provider_interface import (
    ExtraParams,
    ProviderChoices,
    ProviderInterface,
    StandardParams,
)
from openbb_core.env import Env
from pydantic import BaseModel
from typing_extensions import ParamSpec

# 参数规格类型变量，用于泛型函数签名
P = ParamSpec("P")


class OpenBBErrorResponse(BaseModel):
    """OpenBB 错误响应模型

    用于 API 错误响应的标准格式。

    Attributes
    ----------
    detail : str
        错误详情描述
    error_kind : str
        错误类型标识
    """

    detail: str
    error_kind: str


class Router:
    """OpenBB 路由器类

    封装 FastAPI 的 APIRouter，提供命令注册和路由管理功能。

    Router 是 OpenBB 路由系统的核心类，支持：
    - 使用 @command 装饰器注册命令
    - 嵌套子路由器
    - 与 ProviderInterface 集成的依赖注入

    Attributes
    ----------
    api_router : APIRouter
        底层的 FastAPI APIRouter 实例
    prefix : str
        路由前缀
    description : str | None
        路由描述
    routers : dict[str, Router]
        嵌套的子路由器字典
    """

    @property
    def api_router(self) -> APIRouter:
        """获取底层 API 路由器"""
        return self._api_router

    @property
    def prefix(self) -> str:
        """获取路由前缀"""
        return self._api_router.prefix

    @property
    def description(self) -> str | None:
        """获取路由描述"""
        return self._description

    @property
    def routers(self) -> dict[str, "Router"]:
        """获取嵌套的子路由器"""
        return self._routers

    def __init__(
        self,
        prefix: str = "",
        description: str | None = None,
    ) -> None:
        """初始化路由器

        Parameters
        ----------
        prefix : str, optional
            路由前缀，默认为空字符串
        description : str | None, optional
            路由描述，默认为 None
        """
        self._api_router = APIRouter(
            prefix=prefix,
            responses={404: {"description": "Not found"}},
        )
        self._description = description
        self._routers: dict[str, Router] = {}

    @overload
    def command(self, func: Callable[P, OBBject] | None) -> Callable[P, OBBject]:
        pass

    @overload
    def command(self, **kwargs) -> Callable:
        pass

    def command(
        self,
        func: Callable[P, OBBject] | None = None,
        **kwargs,
    ) -> Callable | None:
        """命令装饰器

        将函数注册为 API 路由端点。支持自动签名完善、
        依赖注入和 OpenAPI 文档生成。

        Parameters
        ----------
        func : Callable[P, OBBject] | None, optional
            要注册的命令函数
        **kwargs
            传递给 FastAPI 路由的额外参数，包括：
            - model: 数据模型名称
            - no_validate: 是否跳过响应验证
            - widget_config: 小部件配置
            - mcp_config: MCP 配置
            - deprecated: 是否已废弃
            - deprecation: 废弃警告对象

        Returns
        -------
        Callable | None
            注册后的函数，或 None（如果模型未找到）
        """
        if func is None:
            return lambda f: self.command(f, **kwargs)

        api_router = self._api_router
        model = kwargs.pop("model", "")
        no_validate = kwargs.pop("no_validate", None)
        openapi_extra = kwargs.get("openapi_extra") or {}
        kwargs["openapi_extra"] = openapi_extra

        if widget_config := kwargs.pop("widget_config", None):
            openapi_extra["widget_config"] = widget_config

        if mcp_config := kwargs.pop("mcp_config", None):
            openapi_extra["mcp_config"] = mcp_config

        if no_validate is True:
            func.__annotations__["return"] = None

        if func := SignatureInspector.complete(func, model):
            kwargs["response_model_exclude_unset"] = True
            openapi_extra["model"] = model
            openapi_extra["examples"] = filter_list(
                examples=kwargs.pop("examples", []),
                providers=ProviderInterface().available_providers,
            )
            openapi_extra["no_validate"] = no_validate
            kwargs["operation_id"] = kwargs.get(
                "operation_id", SignatureInspector.get_operation_id(func)
            )
            kwargs["path"] = kwargs.get("path", f"/{func.__name__}")
            kwargs["endpoint"] = func
            kwargs["methods"] = kwargs.get("methods", ["GET"])
            kwargs["response_model"] = (
                kwargs.get(
                    "response_model",
                    func.__annotations__["return"],  # type: ignore
                )
                if not no_validate
                else func.__annotations__["return"]
            )
            kwargs["response_model_by_alias"] = kwargs.get(
                "response_model_by_alias", False
            )
            kwargs["description"] = SignatureInspector.get_description(func)
            kwargs["responses"] = kwargs.get(
                "responses",
                {
                    204: {
                        "description": "Empty response",
                    },
                    400: {
                        "model": OpenBBErrorResponse,
                        "description": "No Results Found",
                    },
                    404: {"description": "Not found"},
                    500: {
                        "model": OpenBBErrorResponse,
                        "description": "Internal Error",
                    },
                    502: {
                        "model": OpenBBErrorResponse,
                        "description": "Unauthorized",
                    },
                },
            )

            # For custom deprecation
            if kwargs.get("deprecated", False):
                deprecation: OpenBBDeprecationWarning = kwargs.pop("deprecation")

                kwargs["summary"] = DeprecationSummary(
                    deprecation.long_message, deprecation
                )

            kwargs["openapi_extra"] = openapi_extra

            api_router.add_api_route(**kwargs)

        return func

    def include_router(
        self,
        router: "Router",
        prefix: str = "",
    ):
        """包含子路由器

        将另一个路由器作为子路由器包含进来。

        Parameters
        ----------
        router : Router
            要包含的子路由器
        prefix : str, optional
            子路由器的路径前缀，默认为空字符串
        """
        tags = [prefix.strip("/")] if prefix else None
        self._api_router.include_router(
            router=router.api_router,
            prefix=prefix,
            tags=tags,  # type: ignore
        )
        name = prefix if prefix else router.prefix
        self._routers[name.strip("/")] = router

    def get_attr(self, path: str, attr: str) -> Any:
        """从路径获取路由器属性

        Parameters
        ----------
        path : str
            路由器或嵌套路由器的路径，例如 "/equity" 或 "/equity/price"
        attr : str
            要获取的属性名称

        Returns
        -------
        Any
            属性值
        """
        return self._search_attr(self, path, attr)

    @staticmethod
    def _search_attr(router: "Router", path: str, attr: str) -> Any:
        """递归搜索路由器属性"""
        path = path.strip("/")
        first = path.split("/")[0]
        if first in router.routers:
            return Router._search_attr(
                router.routers[first], "/".join(path.split("/")[1:]), attr
            )
        return getattr(router, attr, None)

    @classmethod
    def from_fastapi(cls, api_router: APIRouter) -> "Router":
        """从 FastAPI APIRouter 创建 OpenBB Router

        Parameters
        ----------
        api_router : APIRouter
            FastAPI APIRouter 实例

        Returns
        -------
        Router
            新创建的 OpenBB Router 实例
        """
        description = getattr(api_router, "description", None)
        instance = cls(prefix=api_router.prefix, description=description)
        instance._api_router = api_router  # type: ignore[attr-defined]

        return instance


class SignatureInspector:
    """函数签名检查器

    用于验证和完善命令函数的签名，包括：
    - 验证必需的参数（provider_choices, standard_params, extra_params）
    - 注入依赖（通过 FastAPI 的 Depends）
    - 设置返回类型注解
    """

    @classmethod
    def complete(
        cls, func: Callable[P, OBBject], model: str
    ) -> Callable[P, OBBject] | None:
        """完善函数签名

        根据指定的数据模型，为函数注入 ProviderInterface 依赖。

        Parameters
        ----------
        func : Callable[P, OBBject]
            要完善的命令函数
        model : str
            数据模型名称

        Returns
        -------
        Callable[P, OBBject] | None
            完善后的函数，如果模型未找到则返回 None
        """
        if isclass(return_type := func.__annotations__["return"]) and not issubclass(
            return_type, OBBject
        ):
            return func

        provider_interface = ProviderInterface()

        if model:
            if model not in provider_interface.models:
                if Env().DEBUG_MODE:
                    warnings.warn(
                        message=f"\nSkipping api route '/{func.__name__}'.\n"
                        f"Model '{model}' not found.\n\n"
                        "Check available models in ProviderInterface().models",
                        category=OpenBBWarning,
                    )
                return None
            cls.validate_signature(
                func,
                {
                    "provider_choices": ProviderChoices,
                    "standard_params": StandardParams,
                    "extra_params": ExtraParams,
                },
            )

            func = cls.inject_dependency(
                func=func,
                arg="provider_choices",
                callable_=provider_interface.model_providers[model],
            )

            func = cls.inject_dependency(
                func=func,
                arg="standard_params",
                callable_=provider_interface.params[model]["standard"],
            )

            func = cls.inject_dependency(
                func=func,
                arg="extra_params",
                callable_=provider_interface.params[model]["extra"],
            )

            func = cls.inject_return_annotation(
                func=func,
                annotation=provider_interface.return_annotations[model],
            )

        else:
            func = cls.polish_return_schema(func)
            if (
                "provider_choices" in func.__annotations__
                and func.__annotations__["provider_choices"] == ProviderChoices
            ):
                func = cls.inject_dependency(
                    func=func,
                    arg="provider_choices",
                    callable_=provider_interface.provider_choices,
                )

        return func

    @staticmethod
    def polish_return_schema(func: Callable[P, OBBject]) -> Callable[P, OBBject]:
        """完善 API schema

        填充返回类型的 __doc__ 和 __name__ 属性，用于 OpenAPI 文档生成。
        """
        return_type = func.__annotations__["return"]
        is_list = False

        if return_type == OBBject:
            results_type = get_type_hints(return_type)["results"]
            results_type_args = get_args(results_type)
            if not isinstance(results_type, type(None)):
                results_type = results_type_args[0]

            is_list = isinstance(get_origin(results_type), list)
            inner_type = (
                results_type_args[0] if is_list and results_type_args else results_type
            )
            inner_type_name = getattr(inner_type, "__name__", inner_type)

            func.__annotations__["return"].__doc__ = "OBBject"
            func.__annotations__["return"].__name__ = f"OBBject[{inner_type_name}]"

        return func

    @staticmethod
    def validate_signature(
        func: Callable[P, OBBject], expected: dict[str, type]
    ) -> None:
        """验证函数签名

        在绑定到模型之前验证函数是否具有预期的参数。

        Parameters
        ----------
        func : Callable[P, OBBject]
            要验证的函数
        expected : dict[str, type]
            预期的参数名称和类型映射

        Raises
        ------
        AttributeError
            如果缺少必需的参数
        TypeError
            如果参数类型不匹配
        """
        for k, v in expected.items():
            if k not in func.__annotations__:
                raise AttributeError(
                    f"Invalid signature: '{func.__name__}'. Missing '{k}' parameter."
                )

            if func.__annotations__[k] != v:
                raise TypeError(
                    f"Invalid signature: '{func.__name__}'. '{k}' parameter must be of type '{v.__name__}'."
                )

    @staticmethod
    def inject_dependency(
        func: Callable[P, OBBject], arg: str, callable_: Any
    ) -> Callable[P, OBBject]:
        """注入依赖

        使用 FastAPI 的 Depends 机制为函数参数添加依赖注入注解。

        Parameters
        ----------
        func : Callable[P, OBBject]
            目标函数
        arg : str
            参数名称
        callable_ : Any
            依赖的可调用对象

        Returns
        -------
        Callable[P, OBBject]
            添加依赖注解后的函数
        """
        func.__annotations__[arg] = Annotated[callable_, Depends()]  # type: ignore
        return func

    @staticmethod
    def inject_return_annotation(
        func: Callable[P, OBBject], annotation: type[OBBject]
    ) -> Callable[P, OBBject]:
        """注入返回类型注解

        Parameters
        ----------
        func : Callable[P, OBBject]
            目标函数
        annotation : type[OBBject]
            返回类型注解

        Returns
        -------
        Callable[P, OBBject]
            添加返回类型注解后的函数
        """
        func.__annotations__["return"] = annotation
        return func

    @staticmethod
    def get_description(func: Callable) -> str:
        """从 docstring 获取描述

        提取 docstring 的第一部分作为函数描述，
        排除 Parameters、Returns、Examples 等部分。

        Parameters
        ----------
        func : Callable
            目标函数

        Returns
        -------
        str
            函数描述文本
        """
        doc = func.__doc__
        if doc:
            description = doc.split("    Parameters\n    ----------")[0]
            description = description.split("    Returns\n    -------")[0]
            description = description.split("    Examples\n    -------")[0]
            description = "\n".join([line.strip() for line in description.split("\n")])

            return description
        return ""

    @staticmethod
    def get_operation_id(func: Callable, sep: str = "_") -> str:
        """获取操作 ID

        从函数的模块路径和名称生成唯一的操作 ID。

        Parameters
        ----------
        func : Callable
            目标函数
        sep : str, optional
            分隔符，默认为 "_"

        Returns
        -------
        str
            操作 ID
        """
        operation_id = [
            t.replace("_router", "").replace("openbb_", "")
            for t in func.__module__.split(".") + [func.__name__]
        ]
        cleaned_id = sep.join({c: "" for c in operation_id if c}.keys())
        return cleaned_id


class CommandMap:
    """命令映射类

    维护路由路径到命令函数的映射关系，并提供覆盖率统计功能。

    CommandMap 用于：
    - 建立路由路径到处理函数的映射
    - 统计各数据提供者的命令覆盖率
    - 统计各命令支持的数据提供者

    Attributes
    ----------
    map : dict[str, Callable]
        路由路径到命令函数的映射
    provider_coverage : dict[str, list[str]]
        提供者到其支持的命令列表的映射
    command_coverage : dict[str, list[str]]
        命令到其支持的提供者列表的映射
    commands_model : dict[str, str]
        命令到其数据模型名称的映射
    """

    def __init__(
        self, router: Router | None = None, coverage_sep: str | None = None
    ) -> None:
        """初始化命令映射

        Parameters
        ----------
        router : Router | None, optional
            路由器实例，默认从扩展加载
        coverage_sep : str | None, optional
            覆盖率路径的分隔符，默认为 None
        """
        self._router = router or RouterLoader.from_extensions()
        self._map = self.get_command_map(router=self._router)
        self._provider_coverage: dict[str, list[str]] = {}
        self._command_coverage: dict[str, list[str]] = {}
        self._commands_model: dict[str, str] = {}
        self._coverage_sep = coverage_sep

    @property
    def map(self) -> dict[str, Callable]:
        """获取命令映射字典"""
        return self._map

    @property
    def provider_coverage(self) -> dict[str, list[str]]:
        """获取提供者覆盖率"""
        if not self._provider_coverage:
            self._provider_coverage = self.get_provider_coverage(
                router=self._router, sep=self._coverage_sep
            )
        return self._provider_coverage

    @property
    def command_coverage(self) -> dict[str, list[str]]:
        """获取命令覆盖率"""
        if not self._command_coverage:
            self._command_coverage = self.get_command_coverage(
                router=self._router, sep=self._coverage_sep
            )
        return self._command_coverage

    @property
    def commands_model(self) -> dict[str, str]:
        """获取命令到模型的映射"""
        if not self._commands_model:
            self._commands_model = self.get_commands_model(
                router=self._router, sep=self._coverage_sep
            )
        return self._commands_model

    @staticmethod
    def get_command_map(
        router: Router,
    ) -> dict[str, Callable]:
        """获取命令映射

        Parameters
        ----------
        router : Router
            路由器实例

        Returns
        -------
        dict[str, Callable]
            路由路径到命令函数的映射
        """
        api_router = router.api_router
        command_map = {route.path: route.endpoint for route in api_router.routes}  # type: ignore
        return command_map

    @staticmethod
    def get_provider_coverage(
        router: Router, sep: str | None = None
    ) -> dict[str, list[str]]:
        """获取提供者覆盖率

        统计每个数据提供者支持的命令列表。

        Parameters
        ----------
        router : Router
            路由器实例
        sep : str | None, optional
            路径分隔符替换字符，默认为 None

        Returns
        -------
        dict[str, list[str]]
            提供者名称到命令路径列表的映射
        """
        api_router = router.api_router

        mapping = ProviderInterface().map

        coverage_map: dict[Any, Any] = {}
        for route in api_router.routes:
            openapi_extra = getattr(route, "openapi_extra", None)
            if openapi_extra:
                model = openapi_extra.get("model", None)
                if model:
                    providers = list(mapping[model].keys())
                    if "openbb" in providers:
                        providers.remove("openbb")
                    for provider in providers:
                        if provider not in coverage_map:
                            coverage_map[provider] = []
                        if hasattr(route, "path"):
                            rp = (
                                route.path  # type: ignore
                                if sep is None
                                else route.path.replace("/", sep)  # type: ignore
                            )
                            coverage_map[provider].append(rp)

        return coverage_map

    @staticmethod
    def get_command_coverage(
        router: Router, sep: str | None = None
    ) -> dict[str, list[str]]:
        """获取命令覆盖率

        统计每个命令支持的数据提供者列表。

        Parameters
        ----------
        router : Router
            路由器实例
        sep : str | None, optional
            路径分隔符替换字符，默认为 None

        Returns
        -------
        dict[str, list[str]]
            命令路径到提供者名称列表的映射
        """
        api_router = router.api_router

        mapping = ProviderInterface().map

        coverage_map: dict[Any, Any] = {}
        for route in api_router.routes:
            openapi_extra = getattr(route, "openapi_extra")
            if openapi_extra:
                model = openapi_extra.get("model", None)
                if model:
                    providers = list(mapping[model].keys())
                    if "openbb" in providers:
                        providers.remove("openbb")

                    if hasattr(route, "path"):
                        rp = route.path if sep is None else route.path.replace("/", sep)  # type: ignore
                        if route.path not in coverage_map:  # type: ignore
                            coverage_map[rp] = []
                        coverage_map[rp] = providers
        return coverage_map

    @staticmethod
    def get_commands_model(router: Router, sep: str | None = None) -> dict[str, str]:
        """获取命令到模型的映射

        Parameters
        ----------
        router : Router
            路由器实例
        sep : str | None, optional
            路径分隔符替换字符，默认为 None

        Returns
        -------
        dict[str, str]
            命令路径到模型名称的映射
        """
        api_router = router.api_router

        coverage_map: dict[Any, Any] = {}
        for route in api_router.routes:
            openapi_extra = getattr(route, "openapi_extra")
            if openapi_extra:
                model = openapi_extra.get("model", None)
                if model and hasattr(route, "path"):
                    rp = route.path if sep is None else route.path.replace("/", sep)  # type: ignore
                    if route.path not in coverage_map:  # type: ignore
                        coverage_map[rp] = []
                    coverage_map[rp] = model
        return coverage_map

    def get_command(self, route: str) -> Callable | None:
        """根据路由获取命令函数

        Parameters
        ----------
        route : str
            路由路径

        Returns
        -------
        Callable | None
            命令函数，如果未找到则返回 None
        """
        return self._map.get(route, None)


class LoadingError(Exception):
    """扩展加载错误

    当扩展模块加载失败时抛出此异常。
    """


class RouterLoader:
    """路由加载器

    负责从扩展模块加载路由并组装成完整的路由器。
    """

    @staticmethod
    @lru_cache
    def from_extensions() -> Router:
        """从扩展加载路由

        扫描所有已注册的扩展模块，加载它们的路由器
        并组装成一个完整的路由器树。

        Returns
        -------
        Router
            包含所有扩展路由的主路由器

        Raises
        ------
        LoadingError
            如果在调试模式下扩展加载失败
        """
        router = Router()

        for name, entry in ExtensionLoader().core_objects.items():  # type: ignore[attr-defined]
            try:
                router.include_router(router=entry, prefix=f"/{name}")
            except Exception as e:
                msg = f"Error loading extension: {name}\n"
                if Env().DEBUG_MODE:
                    traceback.print_exception(type(e), e, e.__traceback__)
                    raise LoadingError(msg + f"\033[91m{e}\033[0m") from e
                warnings.warn(
                    message=msg,
                    category=OpenBBWarning,
                )

        return router
