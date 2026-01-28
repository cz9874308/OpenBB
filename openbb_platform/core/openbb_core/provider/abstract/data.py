"""OpenBB 标准化数据模型

本模块定义了 OpenBB 平台的核心数据模型基类 Data。

核心概念
--------

Data 类是所有标准化数据输出的基类，提供了灵活的字段定义和自动验证功能。
所有从数据提供者返回的数据都应该继承自此类或其子类（如 EquityHistoricalData）。

设计理念
--------

1. **动态字段支持**: 允许处理未预定义的字段，适应不同数据源的结构差异
2. **别名机制**: 支持 CamelCase 和 snake_case 之间的自动转换
3. **类型验证**: 利用 Pydantic 的验证功能确保数据完整性
4. **可扩展性**: 通过继承创建特定领域的数据模型

使用方式
--------

```python
from openbb_core.provider.abstract.data import Data

# 直接实例化
data_record = Data(name="OpenBB", value=42)

# 从字典创建
data_dict = {"name": "OpenBB", "value": 42}
data_record = Data(**data_dict)

# 继承创建自定义数据模型
class MyData(Data):
    symbol: str
    price: float
```
"""

from typing import Annotated

from pydantic import (
    AliasGenerator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    alias_generators,
    model_validator,
)


def check_int(v: int) -> int:
    """检查并转换值为整数

    Parameters
    ----------
    v : int
        需要检查的值

    Returns
    -------
    int
        转换后的整数值

    Raises
    ------
    TypeError
        如果值无法转换为整数
    """
    try:
        return int(v)
    except ValueError as exc:
        raise TypeError("值必须是整数类型") from exc


# 强制整数类型注解，用于确保字段值为整数
ForceInt = Annotated[int, BeforeValidator(check_int)]


class Data(BaseModel):
    """OpenBB 标准化数据模型基类

    Data 类是一个灵活的 Pydantic 模型，专为 OpenBB 数据处理管道设计，
    支持动态字段定义，能够适应各种数据结构。

    该模型利用 Pydantic 强大的验证功能确保数据完整性，同时提供处理
    模式中未显式定义的额外字段的灵活性。这使得 Data 类非常适合处理
    结构多变或来自异构数据源的数据集。

    核心特性
    --------

    - **动态字段支持**: 可以动态处理未预定义的字段，在处理不同数据结构时具有极大灵活性
    - **别名处理**: 使用别名机制保持与不同命名约定的兼容性（如 CamelCase ↔ snake_case）

    使用示例
    --------

    ```python
    # 直接实例化
    data_record = Data(name="OpenBB", value=42)

    # 从字典转换
    data_dict = {"name": "OpenBB", "value": 42}
    data_record = Data(**data_dict)
    ```

    该类高度可扩展，可以通过继承创建更具体的模型，以适应特定数据集或领域，
    同时仍然受益于 Data 类提供的基础功能。

    Attributes
    ----------
    __alias_dict__ : dict[str, str]
        字段名到别名的映射字典，用于支持不同的命名约定
    model_config : ConfigDict
        模型配置字典，定义模型行为，如接受额外字段、按名称填充、别名生成等
    """

    __alias_dict__: dict[str, str] = {}

    def __repr__(self):
        """返回对象的字符串表示"""
        return f"{self.__class__.__name__}({', '.join([f'{k}={v}' for k, v in super().model_dump().items()])})"

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        strict=False,
        alias_generator=AliasGenerator(
            validation_alias=alias_generators.to_camel,
            serialization_alias=alias_generators.to_snake,
        ),
    )

    @model_validator(mode="before")
    @classmethod
    def _use_alias(cls, values):
        """应用别名映射

        在验证之前将原始字段名转换为别名，用于处理不同数据源的命名差异。
        """
        # 构建原始名称到别名的映射
        aliases = {orig: alias for alias, orig in cls.__alias_dict__.items()}
        if aliases and isinstance(values, dict):
            return {aliases.get(k, k): v for k, v in values.items()}

        return values
