"""命令运行器模块

本模块定义了 OpenBB 命令执行的核心组件。

核心组件
--------

- **ExecutionContext**: 执行上下文，封装命令执行所需的所有环境信息
- **ParametersBuilder**: 参数构建器，负责参数合并、验证和类型转换
- **StaticCommandRunner**: 静态命令运行器，执行命令并处理结果
- **CommandRunner**: 命令运行器，提供高级接口供外部调用

执行流程
--------

```
CommandRunner.run(route, **kwargs)
         ↓
    ExecutionContext
         ↓
    ParametersBuilder.build()
         ↓
    StaticCommandRunner._execute_func()
         ↓
    func(**kwargs) → OBBject
         ↓
    后处理（图表、日志、回调）
         ↓
    返回 OBBject
```
"""

# pylint: disable=R0903
from collections.abc import Callable
from copy import deepcopy
from dataclasses import asdict, is_dataclass
from datetime import datetime
from inspect import Parameter, iscoroutinefunction, signature
from sys import exc_info
from time import perf_counter_ns
from typing import TYPE_CHECKING, Any, Optional
from warnings import catch_warnings, showwarning, warn

from fastapi.encoders import jsonable_encoder
from openbb_core.app.extension_loader import ExtensionLoader
from openbb_core.app.model.abstract.error import OpenBBError
from openbb_core.app.model.abstract.warning import OpenBBWarning, cast_warning
from openbb_core.app.model.extension import CachedAccessor
from openbb_core.app.model.metadata import Metadata
from openbb_core.app.model.obbject import OBBject
from openbb_core.app.provider_interface import ExtraParams
from openbb_core.app.static.package_builder import PathHandler
from openbb_core.env import Env
from openbb_core.provider.utils.helpers import maybe_coroutine, run_async, to_snake_case
from pydantic import BaseModel, ConfigDict, create_model

if TYPE_CHECKING:
    from fastapi.routing import APIRoute
    from openbb_core.app.model.system_settings import SystemSettings
    from openbb_core.app.model.user_settings import UserSettings
    from openbb_core.app.router import CommandMap


class ExecutionContext:
    """执行上下文

    封装命令执行所需的所有环境信息，包括命令映射、路由、
    系统设置和用户设置。

    Attributes
    ----------
    command_map : CommandMap
        命令映射实例
    route : str
        当前执行的路由路径
    system_settings : SystemSettings
        系统设置
    user_settings : UserSettings
        用户设置
    """

    # 用于检查命令是否在 API Route 中指定了 no_validate
    _route_map = PathHandler.build_route_map()

    def __init__(
        self,
        command_map: "CommandMap",
        route: str,
        system_settings: "SystemSettings",
        user_settings: "UserSettings",
    ) -> None:
        """初始化执行上下文

        Parameters
        ----------
        command_map : CommandMap
            命令映射实例
        route : str
            要执行的路由路径
        system_settings : SystemSettings
            系统设置
        user_settings : UserSettings
            用户设置
        """
        self.command_map = command_map
        self.route = route
        self.system_settings = system_settings
        self.user_settings = user_settings

    @property
    def api_route(self) -> "APIRoute":
        """获取 API 路由定义"""
        return self._route_map[self.route]  # type: ignore


class ParametersBuilder:
    """参数构建器

    负责函数参数的合并、验证和类型转换。

    ParametersBuilder 处理从用户输入到函数调用的参数转换：
    - 合并位置参数和关键字参数
    - 注入命令上下文
    - 验证参数类型
    - 处理默认值
    """

    @staticmethod
    def get_polished_parameter_list(func: Callable) -> list[Parameter]:
        """获取函数签名参数列表

        Parameters
        ----------
        func : Callable
            目标函数

        Returns
        -------
        list[Parameter]
            参数列表
        """
        sig = signature(func)
        parameter_list = list(sig.parameters.values())

        return parameter_list

    @staticmethod
    def get_polished_func(func: Callable) -> Callable:
        """从函数签名和注解中移除 __authenticated_user_settings

        Parameters
        ----------
        func : Callable
            目标函数

        Returns
        -------
        Callable
            处理后的函数副本
        """
        func = deepcopy(func)
        sig = signature(func)
        parameter_map = dict(sig.parameters)

        if "__authenticated_user_settings" in parameter_map:
            parameter_map.pop("__authenticated_user_settings")

        parameter_list = list(parameter_map.values())
        new_signature = signature(func).replace(parameters=parameter_list)

        func.__signature__ = new_signature  # type: ignore
        func.__annotations__ = parameter_map

        return func

    @classmethod
    def merge_args_and_kwargs(
        cls,
        func: Callable,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        """合并位置参数和关键字参数

        将 args 和 kwargs 合并为单一的参数字典。

        Parameters
        ----------
        func : Callable
            目标函数
        args : tuple[Any, ...]
            位置参数
        kwargs : dict[str, Any]
            关键字参数

        Returns
        -------
        dict[str, Any]
            合并后的参数字典
        """
        args = deepcopy(args)
        kwargs_copy = deepcopy(kwargs)
        parameter_list = cls.get_polished_parameter_list(func=func)
        parameter_map = {}

        for index, parameter in enumerate(parameter_list):
            if index < len(args):
                parameter_map[parameter.name] = args[index]
            elif parameter.name in kwargs:
                parameter_map[parameter.name] = kwargs[parameter.name]
            elif parameter.default is not parameter.empty:
                parameter_map[parameter.name] = parameter.default
            else:
                parameter_map[parameter.name] = None

        if "kwargs" in parameter_map:
            merged_kwargs = parameter_map.get("kwargs") or {}
            if not isinstance(merged_kwargs, dict):
                merged_kwargs = dict(merged_kwargs)

            for key, value in kwargs_copy.items():
                if key in {"filter_query", "kwargs"} or key in parameter_map:
                    continue
                merged_kwargs[key] = value

            parameter_map.update(merged_kwargs)
            parameter_map.pop("kwargs", None)

        return parameter_map

    @staticmethod
    def update_command_context(
        func: Callable,
        kwargs: dict[str, Any],
        system_settings: "SystemSettings",
        user_settings: "UserSettings",
    ) -> dict[str, Any]:
        """更新命令上下文

        如果函数签名中包含 'cc' 参数，则注入 CommandContext 实例。

        Parameters
        ----------
        func : Callable
            目标函数
        kwargs : dict[str, Any]
            参数字典
        system_settings : SystemSettings
            系统设置
        user_settings : UserSettings
            用户设置

        Returns
        -------
        dict[str, Any]
            更新后的参数字典
        """
        # pylint: disable=import-outside-toplevel
        from openbb_core.app.model.command_context import CommandContext

        argcount = func.__code__.co_argcount
        if "cc" in func.__code__.co_varnames[:argcount]:
            kwargs["cc"] = CommandContext(
                user_settings=user_settings,
                system_settings=system_settings,
            )

        return kwargs

    @staticmethod
    def _warn_kwargs(
        extra_params: dict[str, Any],
        model: type[BaseModel],
    ) -> None:
        """警告被忽略的参数

        如果传入的参数不在验证模型中，则发出警告。
        """
        # 只检查 extra_params 注解，因为被忽略的字段总是会在那里
        annotation = getattr(
            model.model_fields.get("extra_params", None), "annotation", None
        )
        if is_dataclass(annotation) and any(
            t is ExtraParams for t in getattr(annotation, "__bases__", [])
        ):
            valid = asdict(annotation())  # type: ignore
            for p in extra_params:
                if "chart_params" in p:
                    continue
                if p not in valid:
                    warn(
                        message=f"参数 '{p}' 未找到。",
                        category=OpenBBWarning,
                    )

    @staticmethod
    def _as_dict(obj: Any) -> dict[str, Any]:
        """安全地将对象转换为字典"""
        try:
            if isinstance(obj, dict):
                return obj
            return asdict(obj) if is_dataclass(obj) else dict(obj)  # type: ignore
        except Exception:
            return {}

    @staticmethod
    def validate_kwargs(
        func: Callable,
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        """验证并转换参数类型

        使用 Pydantic 模型验证参数，并在可能的情况下强制转换为正确的类型。

        Parameters
        ----------
        func : Callable
            目标函数
        kwargs : dict[str, Any]
            参数字典

        Returns
        -------
        dict[str, Any]
            验证并转换后的参数字典
        """
        sig = signature(func)
        fields: dict[str, tuple[Any, Any]] = {}
        for name, param in sig.parameters.items():
            if param.kind is Parameter.VAR_KEYWORD:
                continue
            annotation = (
                Any if param.annotation is Parameter.empty else param.annotation
            )
            default = ... if param.default is Parameter.empty else param.default
            fields[name] = (annotation, default)
        # We allow extra fields to return with model with 'cc: CommandContext'
        config = ConfigDict(extra="allow", arbitrary_types_allowed=True)
        # pylint: disable=C0103
        ValidationModel = create_model(func.__name__, __config__=config, **fields)  # type: ignore
        # Validate and coerce
        model = ValidationModel(**kwargs)
        ParametersBuilder._warn_kwargs(
            ParametersBuilder._as_dict(kwargs.get("extra_params", {})),
            ValidationModel,
        )
        return dict(model)

    # pylint: disable=R0913
    @classmethod
    def build(
        cls,
        args: tuple[Any, ...],
        execution_context: ExecutionContext,
        func: Callable,
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        """构建函数参数

        执行完整的参数处理流程：合并、上下文注入、验证。

        Parameters
        ----------
        args : tuple[Any, ...]
            位置参数
        execution_context : ExecutionContext
            执行上下文
        func : Callable
            目标函数
        kwargs : dict[str, Any]
            关键字参数

        Returns
        -------
        dict[str, Any]
            构建完成的参数字典
        """
        func = cls.get_polished_func(func=func)
        system_settings = execution_context.system_settings
        user_settings = execution_context.user_settings
        kwargs = cls.merge_args_and_kwargs(
            func=func,
            args=args,
            kwargs=kwargs,
        )
        kwargs = cls.update_command_context(
            func=func,
            kwargs=kwargs,
            system_settings=system_settings,
            user_settings=user_settings,
        )
        kwargs = cls.validate_kwargs(
            func=func,
            kwargs=kwargs,
        )
        return kwargs


# pylint: disable=too-few-public-methods
class StaticCommandRunner:
    """静态命令运行器

    提供命令执行的核心逻辑，包括命令调用、图表生成、
    日志记录和扩展回调触发。
    """

    @classmethod
    async def _command(
        cls,
        func: Callable,
        kwargs: dict[str, Any],
        show_warnings: bool = True,  # pylint: disable=unused-argument   # type: ignore
    ) -> OBBject:
        """执行命令并返回结果

        Parameters
        ----------
        func : Callable
            命令函数
        kwargs : dict[str, Any]
            参数字典
        show_warnings : bool, optional
            是否显示警告，默认为 True

        Returns
        -------
        OBBject
            命令执行结果
        """
        obbject = await maybe_coroutine(func, **kwargs)
        if isinstance(obbject, OBBject):
            obbject.provider = getattr(
                kwargs.get("provider_choices"),
                "provider",
                getattr(obbject, "provider", None),
            )
        return obbject

    @classmethod
    def _chart(
        cls,
        obbject: OBBject,
        **kwargs,
    ) -> None:
        """从命令输出创建图表

        Parameters
        ----------
        obbject : OBBject
            命令输出对象
        **kwargs
            传递给图表生成器的额外参数
        """
        try:
            if "charting" not in obbject.accessors:
                raise OpenBBError(
                    "Charting is not installed. Please install `openbb-charting`."
                )
            # Here we will pop the chart_params kwargs and flatten them into the kwargs.
            chart_params = {}
            extra_params = getattr(obbject, "_extra_params", {})

            if extra_params and "chart_params" in extra_params:
                chart_params = extra_params.get("chart_params", {})

            if kwargs.get("chart_params"):
                chart_params.update(kwargs.pop("chart_params", {}))
            # Verify that kwargs is not nested as kwargs so we don't miss any chart params.
            if (
                "kwargs" in kwargs
                and "chart_params" in kwargs["kwargs"]
                and kwargs["kwargs"].get("chart_params")
            ):
                chart_params.update(kwargs.pop("kwargs", {}).get("chart_params", {}))

            if chart_params:
                kwargs.update(chart_params)

            obbject.charting.show(render=False, **kwargs)  # type: ignore[attr-defined]
        except Exception as e:  # pylint: disable=broad-exception-caught
            if Env().DEBUG_MODE:
                raise OpenBBError(e) from e
            warn(str(e), OpenBBWarning)

    @classmethod
    def _extract_params(cls, kwargs, key) -> dict:
        """从 kwargs 中提取参数模型并转换为字典

        Parameters
        ----------
        kwargs : dict
            参数字典
        key : str
            要提取的键名

        Returns
        -------
        dict
            提取的参数字典
        """
        params = kwargs.get(key, {})
        if hasattr(params, "__dict__"):
            return params.__dict__
        return params

    # pylint: disable=R0913, R0914
    @classmethod
    async def _execute_func(  # pylint: disable=too-many-positional-arguments
        cls,
        route: str,
        args: tuple[Any, ...],
        execution_context: ExecutionContext,
        func: Callable,
        kwargs: dict[str, Any],
    ) -> OBBject:
        """执行函数并返回输出

        执行完整的命令处理流程，包括参数构建、命令执行、
        图表生成、警告处理和日志记录。

        Parameters
        ----------
        route : str
            路由路径
        args : tuple[Any, ...]
            位置参数
        execution_context : ExecutionContext
            执行上下文
        func : Callable
            命令函数
        kwargs : dict[str, Any]
            关键字参数

        Returns
        -------
        OBBject
            命令执行结果
        """
        user_settings = execution_context.user_settings
        system_settings = execution_context.system_settings
        raised_warnings: list = []
        custom_headers: dict[str, Any] | None = None

        try:
            with catch_warnings(record=True) as warning_list:
                # If we're on Jupyter we need to pop here because we will lose "chart" after
                # ParametersBuilder.build. This needs to be fixed in a way that chart is
                # added to the function signature and shared for jupyter and api
                # We can check in the router decorator if the given function has a chart
                # in the charting extension then we add it there. This way we can remove
                # the chart parameter from the commands.py and package_builder, it will be
                # added to the function signature in the router decorator
                # If the ProviderInterface is not in use, we need to pass a copy of the
                # kwargs dictionary before it is validated, otherwise we lose those items.
                kwargs_copy = deepcopy(kwargs)
                chart = kwargs.pop("chart", False)
                kwargs_copy = deepcopy(kwargs)
                kwargs = ParametersBuilder.build(
                    args=args,
                    execution_context=execution_context,
                    func=func,
                    kwargs=kwargs,
                )
                kwargs = kwargs if kwargs is not None else {}
                # If **kwargs is in the function signature, we need to make sure to pass
                # All kwargs to the function so dependency injection happens
                # and kwargs are actually made available as locals within the function.
                if "kwargs" in kwargs_copy:
                    for k, v in kwargs_copy["kwargs"].items():
                        if k not in kwargs:
                            kwargs[k] = v
                # If we're on the api we need to remove "chart" here because the parameter is added on
                # commands.py and the function signature does not expect "chart"
                kwargs.pop("chart", None)
                # We also pop custom headers
                model_headers = system_settings.api_settings.custom_headers or {}
                custom_headers = {
                    name: kwargs.pop(name.replace("-", "_"), default)
                    for name, default in model_headers.items() or {}
                } or None

                obbject = await cls._command(func, kwargs)
                # The output might be from a router command with 'no_validate=True'
                # It might be of a different type than OBBject.
                # In this case, we avoid accessing those attributes.
                if isinstance(obbject, OBBject):
                    # This section prepares the obbject to pass to the charting service.
                    obbject._route = route  # pylint: disable=protected-access
                    std_params = cls._extract_params(kwargs, "standard_params") or (
                        kwargs if "data" in kwargs else {}
                    )
                    extra_params = cls._extract_params(kwargs, "extra_params") or kwargs
                    obbject._standard_params = (  # pylint: disable=protected-access
                        std_params
                    )
                    obbject._extra_params = (  # pylint: disable=protected-access
                        extra_params
                    )
                    if chart and obbject.results:
                        if "extra_params" not in kwargs_copy:
                            kwargs_copy["extra_params"] = {}
                        # Restore any kwargs passed that were removed by the ParametersBuilder
                        for k in kwargs_copy.copy():
                            if k == "chart":
                                kwargs_copy.pop("chart", None)
                                continue
                            if (
                                not extra_params or k not in extra_params
                            ) and k != "extra_params":
                                kwargs_copy["extra_params"][k] = kwargs_copy.pop(
                                    k, None
                                )

                        cls._chart(obbject, **kwargs_copy)

                raised_warnings = warning_list if warning_list else []
        finally:
            if raised_warnings:
                if isinstance(obbject, OBBject):
                    obbject.warnings = []
                for w in raised_warnings:
                    if isinstance(obbject, OBBject):
                        obbject.warnings.append(cast_warning(w))  # type: ignore
                    if user_settings.preferences.show_warnings:
                        showwarning(
                            message=w.message,
                            category=w.category,
                            filename=w.filename,
                            lineno=w.lineno,
                            file=w.file,
                            line=w.line,
                        )

            if system_settings.logging_suppress is False:
                # pylint: disable=import-outside-toplevel
                from openbb_core.app.logs.logging_service import LoggingService

                ls = LoggingService(system_settings, user_settings)
                ls.log(
                    user_settings=user_settings,
                    system_settings=system_settings,
                    route=route,
                    func=func,
                    kwargs=kwargs,
                    exec_info=exc_info(),
                    custom_headers=custom_headers,
                )

        return obbject

    # pylint: disable=W0718
    @classmethod
    async def run(
        cls,
        execution_context: ExecutionContext,
        /,
        *args,
        **kwargs,
    ) -> OBBject:
        """运行命令并返回 OBBject

        这是 StaticCommandRunner 的主入口方法，执行完整的命令流程
        并添加元数据。

        Parameters
        ----------
        execution_context : ExecutionContext
            执行上下文
        *args
            位置参数
        **kwargs
            关键字参数

        Returns
        -------
        OBBject
            命令执行结果

        Raises
        ------
        AttributeError
            如果路由无效
        """
        timestamp = datetime.now()
        start_ns = perf_counter_ns()

        command_map = execution_context.command_map
        route = execution_context.route

        if func := command_map.get_command(route=route):
            obbject = await cls._execute_func(
                route=route,
                args=args,  # type: ignore
                execution_context=execution_context,
                func=func,
                kwargs=kwargs,
            )
        else:
            raise AttributeError(f"Invalid command : route={route}")

        duration = perf_counter_ns() - start_ns

        if execution_context.user_settings.preferences.metadata and isinstance(
            obbject, OBBject
        ):
            try:
                obbject.extra["metadata"] = Metadata(
                    arguments=kwargs,
                    duration=duration,
                    route=route,
                    timestamp=timestamp,
                )
            except Exception as e:
                if Env().DEBUG_MODE:
                    raise OpenBBError(e) from e
                warn(str(e), OpenBBWarning)

            # Remove the dependency injection objects embedded in the kwargs
            deps = execution_context.api_route.dependencies
            dependency_param_names: set[str] = set()
            if deps:
                for dep in deps:
                    dep_name = getattr(dep.dependency, "__name__", "")
                    dep_name = to_snake_case(dep_name).replace("get_", "")
                    dependency_param_names.add(dep_name)

                for dep_key in dependency_param_names:
                    _ = obbject._extra_params.pop(  # type:ignore  # pylint: disable=W0212
                        dep_key, None
                    )

            meta = getattr(obbject.extra.get("metadata"), "arguments", {})

            # Non-provider endpoints need to have execution info added because it might have been discarded.
            if meta and (
                not meta.get("provider_choices", {})
                and not meta.get("standard_params", {})
                and not meta.get("extra_params", {})
            ):
                for k, v in kwargs.items():
                    if k == "kwargs":
                        for key, value in kwargs["kwargs"].items():
                            if key not in dependency_param_names and value:
                                obbject.extra["metadata"].arguments["extra_params"][
                                    key
                                ] = value
                        continue
                    if k not in dependency_param_names and v:
                        obbject.extra["metadata"].arguments["standard_params"][k] = v

        if isinstance(obbject, OBBject):
            try:
                cls._trigger_command_output_callbacks(route, obbject)
            except Exception as e:
                if Env().DEBUG_MODE:
                    raise OpenBBError(e) from e
                warn(str(e), OpenBBWarning)
            # We need to remove callables that were added to
            # kwargs representing dependency injections
            metadata = obbject.extra.get("metadata")
            if metadata:
                arguments = obbject.extra["metadata"].arguments

                for section in ("standard_params", "extra_params", "provider_choices"):
                    params = arguments.get(section)

                    if not isinstance(params, dict):
                        continue

                    for key, value in params.copy().items():
                        if callable(value) or not value:
                            del obbject.extra["metadata"].arguments[section][key]
                            continue
                        try:
                            jsonable_encoder(value)
                        except (TypeError, ValueError):
                            del obbject.extra["metadata"].arguments[section][key]
                            continue

        return obbject

    @classmethod
    def _trigger_command_output_callbacks(cls, route: str, obbject: OBBject) -> None:
        """触发扩展的命令输出回调

        遍历所有注册了输出回调的扩展，调用它们的访问器方法。

        Parameters
        ----------
        route : str
            命令路由路径
        obbject : OBBject
            命令输出对象
        """
        loader = ExtensionLoader()
        callbacks = loader.on_command_output_callbacks
        if not callbacks:
            return

        # For each extension registered for all routes or the specific route,
        # we call its accessor on the OBBject.
        # We check if the accessor is immutable or not to decide whether to pass
        # a copy of the OBBject or the original one.
        # We set the _extension_modified attribute to True if any extension
        # mutates the OBBject so we can pass this information to the interface.
        # We also set the _results_only attribute to True if any extension
        # indicates that only results should be returned.
        results_only = False
        executed_keys: set[str] = set()
        ordered_extensions: list = []
        all_on_command_output_exts: list = []

        def _extension_key(ext) -> str:
            if key := getattr(ext, "identifier", None):
                return str(key)
            if path := getattr(ext, "import_path", None):
                return f"{path}:{getattr(ext, 'name', id(ext))}"
            return str(getattr(ext, "name", id(ext)))

        def _clone_for_immutable(source: OBBject) -> OBBject | None:
            try:
                new_source = source.model_copy()
                new_source = OBBject.model_validate(source.model_dump())
                return source.model_validate(new_source)
            except Exception as e:
                warn(
                    "Skipped immutable callback because the OBBject "
                    f"could not be duplicated. {e}",
                    OpenBBWarning,
                )
                return None

        for ext_list in callbacks.values():
            all_on_command_output_exts.extend(ext_list)

        for ext in callbacks.get("*", []):
            key = _extension_key(ext)
            if key not in executed_keys:
                executed_keys.add(key)
                ordered_extensions.append(ext)

        for ext in callbacks.get(route, []):
            key = _extension_key(ext)
            if key not in executed_keys:
                executed_keys.add(key)
                ordered_extensions.append(ext)

        try:
            for ext in ordered_extensions:
                if ext.results_only is True:
                    results_only = True

                if ext.command_output_paths and route not in ext.command_output_paths:
                    continue

                accessors: set = getattr(type(obbject), "accessors", set())
                if ext.name not in accessors:
                    continue

                descriptor = type(obbject).__dict__.get(ext.name)
                if not isinstance(descriptor, CachedAccessor):
                    continue

                factory = descriptor._accessor  # type: ignore  # pylint: disable=W0212

                target = _clone_for_immutable(obbject) if ext.immutable else obbject

                if target is None:
                    continue

                if iscoroutinefunction(factory):
                    run_async(factory, target)
                else:
                    result = factory(target)
                    if callable(result):
                        result()

                if ext.immutable is False:
                    object.__setattr__(obbject, "_extension_modified", True)

            if results_only is True:
                object.__setattr__(obbject, "_results_only", True)
                object.__setattr__(obbject, "_extension_modified", True)

        except Exception as e:
            raise OpenBBError(e) from e

        for ext in all_on_command_output_exts:
            if ext.name in type(obbject).__dict__:
                object.__setattr__(
                    obbject,
                    ext.name,
                    "Accessor is not callable outside of function execution.",
                )


class CommandRunner:
    """命令运行器

    提供高级接口用于执行 OpenBB 命令。

    CommandRunner 封装了命令执行的完整流程，包括：
    - 命令映射管理
    - 系统和用户设置管理
    - 日志服务初始化
    - 同步和异步执行支持

    Attributes
    ----------
    command_map : CommandMap
        命令映射实例
    system_settings : SystemSettings
        系统设置
    user_settings : UserSettings
        用户设置
    """

    def __init__(
        self,
        command_map: Optional["CommandMap"] = None,
        system_settings: Optional["SystemSettings"] = None,
        user_settings: Optional["UserSettings"] = None,
    ) -> None:
        """初始化命令运行器

        Parameters
        ----------
        command_map : CommandMap | None, optional
            命令映射实例，默认创建新实例
        system_settings : SystemSettings | None, optional
            系统设置，默认从 SystemService 获取
        user_settings : UserSettings | None, optional
            用户设置，默认从文件读取
        """
        # pylint: disable=import-outside-toplevel
        from openbb_core.app.router import CommandMap
        from openbb_core.app.service.system_service import SystemService
        from openbb_core.app.service.user_service import UserService

        self._command_map = command_map or CommandMap()
        self._system_settings = system_settings or SystemService().system_settings
        self._user_settings = user_settings or UserService.read_from_file()

    def init_logging_service(self) -> None:
        """初始化日志服务"""
        # pylint: disable=import-outside-toplevel
        from openbb_core.app.logs.logging_service import LoggingService

        _ = LoggingService(
            system_settings=self._system_settings, user_settings=self._user_settings
        )

    @property
    def command_map(self) -> "CommandMap":
        """获取命令映射"""
        return self._command_map

    @property
    def system_settings(self) -> "SystemSettings":
        """获取系统设置"""
        return self._system_settings

    @property
    def user_settings(self) -> "UserSettings":
        """获取用户设置"""
        return self._user_settings

    @user_settings.setter
    def user_settings(self, user_settings: "UserSettings") -> None:
        """设置用户设置"""
        self._user_settings = user_settings

    # pylint: disable=W1113
    async def run(
        self,
        route: str,
        user_settings: Optional["UserSettings"] = None,
        /,
        *args,
        **kwargs,
    ) -> OBBject:
        """异步运行命令

        Parameters
        ----------
        route : str
            命令路由路径
        user_settings : UserSettings | None, optional
            用户设置覆盖，默认使用实例设置
        *args
            位置参数
        **kwargs
            关键字参数

        Returns
        -------
        OBBject
            命令执行结果
        """
        # pylint: disable=import-outside-toplevel

        self._user_settings = user_settings or self._user_settings

        execution_context = ExecutionContext(
            command_map=self._command_map,
            route=route,
            system_settings=self._system_settings,
            user_settings=self._user_settings,
        )

        return await StaticCommandRunner.run(execution_context, *args, **kwargs)

    # pylint: disable=W1113
    def sync_run(
        self,
        route: str,
        user_settings: Optional["UserSettings"] = None,
        /,
        *args,
        **kwargs,
    ) -> OBBject:
        """同步运行命令

        Parameters
        ----------
        route : str
            命令路由路径
        user_settings : UserSettings | None, optional
            用户设置覆盖，默认使用实例设置
        *args
            位置参数
        **kwargs
            关键字参数

        Returns
        -------
        OBBject
            命令执行结果
        """
        return run_async(self.run, route, user_settings, *args, **kwargs)
