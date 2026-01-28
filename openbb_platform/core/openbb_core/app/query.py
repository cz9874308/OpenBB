"""查询类模块

本模块定义了 Query 类，负责封装和执行数据查询请求。

核心概念
--------

Query 是连接用户请求和数据提供者的桥梁，它：

1. 接收用户的查询参数（标准参数 + 扩展参数）
2. 根据选择的提供者过滤参数
3. 调用 ProviderInterface 执行实际的数据获取

工作流程
--------

```
CommandContext + ProviderChoices + StandardParams + ExtraParams
                              ↓
                           Query
                              ↓
                    filter_extra_params()
                              ↓
                    ProviderInterface.execute()
                              ↓
                         返回结果
```
"""

import warnings
from dataclasses import asdict
from typing import Any

from openbb_core.app.model.abstract.warning import OpenBBWarning
from openbb_core.app.model.command_context import CommandContext
from openbb_core.app.provider_interface import (
    ExtraParams,
    ProviderChoices,
    ProviderInterface,
    StandardParams,
)


class Query:
    """查询类

    封装数据查询的所有必要信息，并提供执行查询的方法。

    Query 类是命令执行流程中的关键组件，它将用户输入的参数
    与选定的数据提供者结合，通过 ProviderInterface 获取数据。

    Attributes
    ----------
    cc : CommandContext
        命令上下文，包含用户设置和系统设置
    provider : str
        选择的数据提供者名称
    standard_params : StandardParams
        标准查询参数（跨提供者通用）
    extra_params : ExtraParams
        扩展查询参数（提供者特定）
    name : str
        查询参数类的名称
    provider_interface : ProviderInterface
        提供者接口实例
    """

    def __init__(
        self,
        cc: CommandContext,
        provider_choices: ProviderChoices,
        standard_params: StandardParams,
        extra_params: ExtraParams,
    ) -> None:
        """初始化查询类

        Parameters
        ----------
        cc : CommandContext
            命令上下文，包含用户和系统设置
        provider_choices : ProviderChoices
            提供者选择，包含选定的提供者名称
        standard_params : StandardParams
            标准查询参数
        extra_params : ExtraParams
            扩展查询参数
        """
        self.cc = cc
        original = asdict(provider_choices)
        self.provider = original.get("provider")
        self.standard_params = standard_params
        self.extra_params = extra_params
        self.name = self.standard_params.__class__.__name__
        self.provider_interface = ProviderInterface()

    def filter_extra_params(
        self,
        extra_params: ExtraParams,
        provider_name: str,
    ) -> dict[str, Any]:
        """根据提供者过滤扩展参数

        检查每个扩展参数是否被指定的提供者支持，
        如果参数不被支持且值不是默认值，则发出警告。

        Parameters
        ----------
        extra_params : ExtraParams
            扩展参数对象
        provider_name : str
            提供者名称

        Returns
        -------
        dict[str, Any]
            过滤后的参数字典，只包含被提供者支持的参数
        """
        original = asdict(extra_params)
        filtered = {}

        query = extra_params.__class__.__name__
        fields = asdict(self.provider_interface.params[query]["extra"]())  # type: ignore

        for k, v in original.items():
            f = fields[k]
            providers = f.title.split(",") if hasattr(f, "title") else []

            # 只有当值不是默认值时才过滤/警告，因为 FastAPI 的 Depends
            # 总是会发送默认值，即使请求中没有该参数
            if v != f.default:
                if provider_name in providers:
                    filtered[k] = v
                else:
                    available = ", ".join(providers)
                    warnings.warn(
                        message=f"参数 '{k}' 不被 {provider_name} 支持。可用于: {available}。",
                        category=OpenBBWarning,
                    )

        return filtered

    async def execute(self) -> Any:
        """执行查询

        将标准参数和过滤后的扩展参数合并，
        通过 ProviderInterface 执行数据查询。

        Returns
        -------
        Any
            查询结果，通常是标准化的数据对象
        """
        # 将标准参数转换为字典
        standard_dict = asdict(self.standard_params)
        # 过滤扩展参数，只保留当前提供者支持的参数
        extra_dict = (
            self.filter_extra_params(self.extra_params, self.provider) if self.extra_params else {}  # type: ignore
        )
        # 创建查询执行器
        query_executor = self.provider_interface.create_executor()

        # 执行查询
        return await query_executor.execute(
            provider_name=self.provider,
            model_name=self.name,
            params={**standard_dict, **extra_dict},
            credentials=self.cc.user_settings.credentials.model_dump(),
            preferences=self.cc.user_settings.preferences.model_dump(),
        )
