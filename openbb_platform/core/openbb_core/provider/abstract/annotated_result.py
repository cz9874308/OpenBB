"""带注解的结果模块

本模块定义了 AnnotatedResult 类，允许 Fetcher 在返回数据的同时携带元数据信息。

使用场景
--------

当数据获取器需要返回额外的上下文信息（如分页信息、请求时间戳等）时，
可以使用 AnnotatedResult 包装返回结果，而不是只返回原始数据。

示例
----

```python
from openbb_core.provider.abstract.annotated_result import AnnotatedResult

# 在 Fetcher 的 transform_data 方法中
def transform_data(query, data, **kwargs):
    result = [MyData(**item) for item in data]
    metadata = {"total_count": len(result), "page": 1}
    return AnnotatedResult(result=result, metadata=metadata)
```
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class AnnotatedResult(BaseModel, Generic[T]):
    """带注解的结果容器

    允许 Fetcher 在返回数据的同时携带元数据信息。
    这在需要传递分页信息、请求统计等额外上下文时特别有用。

    Attributes
    ----------
    result : T | None
        可序列化的结果数据，类型由泛型参数 T 决定
    metadata : dict | None
        元数据字典，可包含任意键值对
    """

    result: T | None = Field(
        default=None,
        description="可序列化的结果数据",
    )
    metadata: dict | None = Field(
        default=None,
        description="元数据信息",
    )
