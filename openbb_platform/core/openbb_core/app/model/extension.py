"""OBBject 扩展模块

本模块定义了 OBBject 扩展的入口点类。

扩展机制
--------

OBBject 扩展允许向 OBBject 添加自定义访问器方法，
类似于 Pandas 的扩展机制。

示例
----

```python
# 在扩展包中定义
from openbb_core.app.model.extension import Extension

ext = Extension(name="my_extension")

@ext.obbject_accessor
class MyExtension:
    def __init__(self, obbject):
        self._obbject = obbject

    def my_method(self):
        # 使用 self._obbject 访问数据
        pass

# 使用扩展
result = obb.equity.price.historical("AAPL")
result.my_extension.my_method()
```

更多信息请参阅：https://docs.openbb.co/developer/extension_types/obbject
"""

import warnings
from collections.abc import Callable


class Extension:
    """OBBject 扩展入口点

    每个 OBBject 扩展包必须创建此类的实例。
    扩展可以向 OBBject 添加自定义访问器方法。

    Attributes
    ----------
    name : str
        扩展名称
    credentials : list[str]
        所需凭证列表
    description : str | None
        扩展描述
    on_command_output : bool
        是否在命令输出时触发
    command_output_paths : list[str]
        扩展作用的端点路径列表
    immutable : bool
        函数输出是否不可变
    results_only : bool
        是否只返回结果而不是 OBBject
    """

    # pylint: disable=R0917
    def __init__(
        self,
        name: str,
        credentials: list[str] | None = None,
        description: str | None = None,
        on_command_output: bool = False,
        command_output_paths: list[str] | None = None,
        immutable: bool = True,
        results_only: bool = False,
    ) -> None:
        """初始化扩展

        Parameters
        ----------
        name : str
            扩展名称
        credentials : list[str] | None, optional
            所需凭证列表，默认为 None
        description : str | None, optional
            扩展描述，默认为 None
        on_command_output : bool, optional
            是否在命令输出时触发，默认为 False
        command_output_paths : list[str] | None, optional
            扩展作用的端点路径列表（None 表示所有），默认为 None
        immutable : bool, optional
            函数输出是否不可变，默认为 True
        results_only : bool, optional
            是否只返回结果而不是 OBBject，默认为 False

        Raises
        ------
        ValueError
            如果设置了 command_output_paths 等参数但 on_command_output 为 False
        RuntimeError
            如果扩展需要但未启用相应的系统设置
        """
        # pylint: disable=import-outside-toplevel
        from openbb_core.app.service.system_service import SystemService

        self.name = name
        self.credentials = credentials or []
        self.description = description
        self.on_command_output = on_command_output
        self.command_output_paths = command_output_paths or []
        self.immutable = immutable
        self.results_only = results_only

        # This must be explicitly enabled.
        if self.on_command_output is False and (
            self.command_output_paths
            or self.results_only is True
            or self.immutable is False
        ):
            raise ValueError(
                "OBBject Extension Error -> 'on_command_output' must be set as True when"
                + " 'command_output_paths', 'results_only' or 'immutable' is set.",
            )

        # The user must explicitly enable OBBject extensions that act on command output.
        if (
            self.on_command_output
            and not SystemService().system_settings.allow_on_command_output
        ):
            raise RuntimeError(
                "OBBject Extension Error -> \n\n"
                + "An OBBject extension that acts on command output is installed "
                + "but has not been enabled in `system_settings.json`.\n\n"
                + "Set `allow_on_command_output` to True to enable it.\n"
                + "Or, set the environment variable `OPENBB_ALLOW_ON_COMMAND_OUTPUT` to True."
                + "\n\nProceed with caution as this may have security implications.\n\n"
                + "Ensure the extension is installed from a trusted source.\n\n",
            )

        # The user must explicitly enable OBBject extensions that modify output.
        if (
            self.on_command_output
            and self.immutable is False
            and not SystemService().system_settings.allow_mutable_extensions
        ):
            raise RuntimeError(
                "OBBject Extension Error -> \n\n"
                + "An OBBject extension that modifies the output is installed "
                + "but has not been enabled in `system_settings.json`.\n\n"
                + "Set `allow_mutable_extensions` to True to enable it.\n"
                + "Or, set the environment variable `OPENBB_ALLOW_MUTABLE_EXTENSIONS` to True."
                + "\n\nProceed with caution as this may have security implications.\n\n"
                + "Ensure the extension is installed from a trusted source.\n\n",
            )

    @property
    def obbject_accessor(self) -> Callable:
        """OBBject 访问器装饰器

        受 Pandas 启发的扩展机制。

        Returns
        -------
        Callable
            访问器注册装饰器
        """
        # pylint: disable=import-outside-toplevel

        from openbb_core.app.model.obbject import OBBject

        return self.register_accessor(self.name, OBBject)

    @staticmethod
    def register_accessor(name, cls) -> Callable:
        """注册自定义访问器

        Parameters
        ----------
        name : str
            访问器名称
        cls : type
            要扩展的类

        Returns
        -------
        Callable
            装饰器函数
        """

        def decorator(accessor):
            if hasattr(cls, name):
                warnings.warn(
                    f"在类型 '{repr(cls)}' 上以名称 '{repr(name)}' 注册访问器 "
                    f"'{repr(accessor)}' 将覆盖同名的现有属性。",
                    UserWarning,
                )
            setattr(cls, name, CachedAccessor(name, accessor))
            cls.accessors.add(name)

            return accessor

        return decorator


class CachedAccessor:
    """缓存访问器

    实现延迟加载和缓存的描述符。
    首次访问时创建访问器实例并缓存，后续访问直接返回缓存的实例。
    """

    def __init__(self, name: str, accessor) -> None:
        """初始化缓存访问器

        Parameters
        ----------
        name : str
            访问器名称
        accessor : type
            访问器类
        """
        self._name = name
        self._accessor = accessor

    def __get__(self, obj, cls):
        """获取缓存的访问器实例

        Parameters
        ----------
        obj : object | None
            宿主对象实例
        cls : type
            宿主类

        Returns
        -------
        object
            访问器实例或访问器类（如果 obj 为 None）
        """
        if obj is None:
            return self._accessor
        # 创建访问器实例并缓存到宿主对象上
        accessor_obj = self._accessor(obj)
        object.__setattr__(obj, self._name, accessor_obj)
        return accessor_obj
