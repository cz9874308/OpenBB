"""OpenBB 标准化查询参数模型

本模块定义了 QueryParams 类，用于承载查询输入参数。

核心概念
--------

QueryParams 是所有查询参数的基类，提供了参数验证、别名处理和 JSON Schema 扩展功能。
每个标准数据模型（如 EquityHistoricalQueryParams）都继承自此类。

设计理念
--------

1. **标准化输入**: 定义跨提供者通用的查询参数
2. **别名机制**: 支持不同命名约定之间的映射
3. **Schema 扩展**: 允许提供者添加特定的参数约束

使用方式
--------

```python
from openbb_core.provider.abstract.query_params import QueryParams
from pydantic import Field

class EquityHistoricalQueryParams(QueryParams):
    symbol: str = Field(description="股票代码")
    start_date: date | None = Field(default=None, description="开始日期")
    end_date: date | None = Field(default=None, description="结束日期")
```

别名示例
--------

```python
class MyProviderQueryParams(StandardQueryParams):
    __alias_dict__ = {
        "symbol": "ticker",  # 导出时 symbol 会变成 ticker
    }
```
"""

from typing import Any

from pydantic import BaseModel, ConfigDict


class QueryParams(BaseModel):
    """OpenBB 标准化查询参数模型

    QueryParams 类用于承载查询参数，由各数据提供者扩展使用，
    并在 Fetcher 发起数据请求时使用。

    核心特性
    --------

    **别名处理**

    使用别名机制保持与不同命名约定的兼容性。
    别名仅在运行 ``model_dump`` 时应用。

    **JSON Schema 扩展合并**

    可以合并不同提供者的 JSON Schema 扩展属性。

    示例::

        # FMP fetcher:
        __json_schema_extra__ = {"symbol": {"multiple_items_allowed": True}}

        # Intrinio fetcher:
        __json_schema_extra__ = {"symbol": {"multiple_items_allowed": False}}

        # 在 `symbol` 的 schema 中创建新字段:
        {
            "type": "string",
            "description": "获取数据的股票代码",
            "fmp": {"multiple_items_allowed": True},
            "intrinio": {"multiple_items_allowed": False}
        }

    多个字段可以使用相同或不同的属性标记::

        __json_schema_extra__ = {
            "<field_name_A>": {"foo": 123, "bar": 456},
            "<field_name_B>": {"foo": 789}
        }

    Attributes
    ----------
    __alias_dict__ : dict[str, str]
        字段名到别名的映射字典，用于支持不同的命名约定
    __json_schema_extra__ : dict[str, Any]
        要包含在 JSON schema extra 中的属性
    model_config : ConfigDict
        模型配置字典，定义模型行为，如接受额外字段、按名称填充等
    """

    __alias_dict__: dict[str, str] = {}
    __json_schema_extra__: dict[str, Any] = {}

    def __repr__(self):
        """返回 QueryParams 对象的字符串表示"""
        return f"{self.__class__.__name__}({', '.join([f'{k}={v}' for k, v in self.model_dump().items()])})"

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    def model_dump(self, *args, **kwargs):
        """导出模型数据

        如果定义了别名字典，将字段名转换为对应的别名。

        Returns
        -------
        dict
            模型数据字典，键可能已被别名替换
        """
        original = super().model_dump(*args, **kwargs)
        # 如果存在别名映射，应用别名转换
        if self.__alias_dict__:
            return {
                self.__alias_dict__.get(key, key): value
                for key, value in original.items()
            }
        return original
