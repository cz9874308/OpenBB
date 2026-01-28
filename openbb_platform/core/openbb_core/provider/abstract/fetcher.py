"""数据获取器抽象基类模块

本模块定义了 OpenBB 数据获取框架的核心组件 Fetcher 类。

核心概念
--------

Fetcher（数据获取器）是 OpenBB 数据标准化框架的核心，实现了 TET 模式：

1. **Transform (转换查询)**: 将用户输入参数转换为提供者特定的查询格式
2. **Extract (提取数据)**: 从数据提供者 API 获取原始数据
3. **Transform (转换数据)**: 将原始数据转换为标准化的 Data 模型

工作原理
--------

```
用户请求参数 → transform_query() → 提供者查询对象
                                         ↓
                                   extract_data()
                                         ↓
                               原始 API 响应数据
                                         ↓
                               transform_data()
                                         ↓
                              标准化 Data 对象列表
```

使用方式
--------

每个数据提供者需要继承 Fetcher 并实现三个核心方法：

```python
class MyProviderEquityHistoricalFetcher(
    Fetcher[MyProviderEquityHistoricalQueryParams, list[MyProviderEquityHistoricalData]]
):
    @staticmethod
    def transform_query(params: dict[str, Any]) -> MyProviderEquityHistoricalQueryParams:
        # 转换查询参数
        return MyProviderEquityHistoricalQueryParams(**params)

    @staticmethod
    async def aextract_data(query, credentials, **kwargs) -> dict:
        # 从 API 提取数据
        return await make_api_request(query, credentials)

    @staticmethod
    def transform_data(query, data, **kwargs) -> list[MyProviderEquityHistoricalData]:
        # 转换为标准格式
        return [MyProviderEquityHistoricalData.model_validate(d) for d in data]
```
"""

# ruff: noqa: S101, E501
# pylint: disable=E1101, C0301

from typing import (
    Any,
    Generic,
    TypeVar,
    get_args,
    get_origin,
)

from openbb_core.provider.abstract.annotated_result import AnnotatedResult
from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.utils.helpers import maybe_coroutine, run_async

# 泛型类型变量定义
Q = TypeVar("Q", bound=QueryParams)  # 查询参数类型
D = TypeVar("D", bound=Data)  # 数据类型
R = TypeVar("R")  # 返回类型，通常是 List[D]，但也可以是单个 D


class classproperty:
    """类属性装饰器

    允许定义可以通过类直接访问的属性，而不需要实例化。
    """

    def __init__(self, f):
        """初始化装饰器

        Parameters
        ----------
        f : callable
            被装饰的方法
        """
        self.f = f

    def __get__(self, obj, owner):
        """获取属性值

        Parameters
        ----------
        obj : object
            实例对象（可能为 None）
        owner : type
            类对象

        Returns
        -------
        Any
            属性值
        """
        return self.f(owner)


class Fetcher(Generic[Q, R]):
    """数据获取器抽象基类

    Fetcher 是 OpenBB 数据提供者框架的核心组件，定义了从外部数据源
    获取和转换数据的标准接口。所有数据提供者的获取器都必须继承此类。

    TET 模式
    --------

    Fetcher 实现了 Transform-Extract-Transform (TET) 模式：

    1. ``transform_query``: 将通用参数转换为提供者特定的查询格式
    2. ``extract_data``: 从数据提供者 API 提取原始数据
    3. ``transform_data``: 将原始数据转换为标准化的 Data 模型

    实现要求
    --------

    子类必须实现以下方法：

    - ``transform_query``: 必须实现
    - ``extract_data`` 或 ``aextract_data``: 必须实现其一
    - ``transform_data``: 必须实现

    Attributes
    ----------
    require_credentials : bool
        是否需要凭证，默认为 True，子类可以覆盖
    """

    # 告诉查询执行器是否需要凭证，子类可以覆盖此属性
    require_credentials = True

    @staticmethod
    def transform_query(params: dict[str, Any]) -> Q:
        """将参数转换为提供者特定的查询对象

        这是 TET 模式的第一步（T），负责将用户输入的通用参数
        转换为特定数据提供者所需的查询格式。

        Parameters
        ----------
        params : dict[str, Any]
            用户输入的查询参数字典

        Returns
        -------
        Q
            转换后的查询参数对象

        Raises
        ------
        NotImplementedError
            子类必须实现此方法
        """
        raise NotImplementedError

    @staticmethod
    async def aextract_data(query: Q, credentials: dict[str, str] | None) -> Any:
        """异步从数据提供者提取数据

        这是 TET 模式的第二步（E）的异步版本，负责从外部 API 获取原始数据。

        Parameters
        ----------
        query : Q
            查询参数对象
        credentials : dict[str, str] | None
            API 凭证字典

        Returns
        -------
        Any
            从提供者获取的原始数据
        """

    @staticmethod
    def extract_data(query: Q, credentials: dict[str, str] | None) -> Any:
        """从数据提供者提取数据

        这是 TET 模式的第二步（E），负责从外部 API 获取原始数据。

        Parameters
        ----------
        query : Q
            查询参数对象
        credentials : dict[str, str] | None
            API 凭证字典

        Returns
        -------
        Any
            从提供者获取的原始数据
        """

    @staticmethod
    def transform_data(query: Q, data: Any, **kwargs) -> R | AnnotatedResult[R]:
        """将提供者数据转换为标准格式

        这是 TET 模式的第三步（T），负责将原始 API 响应数据
        转换为标准化的 Data 模型对象。

        Parameters
        ----------
        query : Q
            查询参数对象（可能用于数据过滤或转换）
        data : Any
            从 extract_data 获取的原始数据
        **kwargs
            额外的关键字参数

        Returns
        -------
        R | AnnotatedResult[R]
            转换后的标准数据，或带注解的结果

        Raises
        ------
        NotImplementedError
            子类必须实现此方法
        """
        raise NotImplementedError

    def __init_subclass__(cls, *args, **kwargs):
        """初始化子类

        在子类定义时自动调用，用于验证子类是否正确实现了必需的方法。
        如果同时实现了 extract_data 和 aextract_data，将优先使用异步版本。
        """
        super().__init_subclass__(*args, **kwargs)

        # 如果实现了异步版本，将其设为默认的 extract_data
        if cls.aextract_data != Fetcher.aextract_data:
            cls.extract_data = cls.aextract_data  # type: ignore[method-assign]
        elif cls.extract_data == Fetcher.extract_data:
            raise NotImplementedError(
                "Fetcher 子类必须实现 extract_data 或 aextract_data 方法。"
                "如果两者都实现了，aextract_data 将作为默认方法使用。"
            )

    @classmethod
    async def fetch_data(
        cls,
        params: dict[str, Any],
        credentials: dict[str, str] | None = None,
        **kwargs,
    ) -> R | AnnotatedResult[R]:
        """从数据提供者获取数据

        这是 Fetcher 的主入口方法，按顺序执行完整的 TET 流程。

        Parameters
        ----------
        params : dict[str, Any]
            查询参数字典
        credentials : dict[str, str] | None, optional
            API 凭证字典，默认为 None
        **kwargs
            传递给各步骤的额外参数

        Returns
        -------
        R | AnnotatedResult[R]
            标准化的数据结果
        """
        # T: 转换查询参数
        query = cls.transform_query(params=params)
        # E: 提取原始数据
        data = await maybe_coroutine(
            cls.extract_data, query=query, credentials=credentials, **kwargs
        )
        # T: 转换为标准格式
        return cls.transform_data(query=query, data=data, **kwargs)

    @classproperty
    def query_params_type(self) -> Q:
        """获取查询参数类型

        Returns
        -------
        Q
            查询参数的类型
        """
        # pylint: disable=E1101
        return self.__orig_bases__[0].__args__[0]  # type: ignore

    @classproperty
    def return_type(self) -> R:
        """获取返回值类型

        Returns
        -------
        R
            返回值的类型
        """
        # pylint: disable=E1101
        return_type = self.__orig_bases__[0].__args__[1]  # type: ignore
        if get_origin(return_type) is AnnotatedResult:
            return_type = get_args(return_type)[0]
        return return_type

    @classproperty
    def data_type(self) -> D:  # type: ignore
        """获取数据类型

        Returns
        -------
        D
            数据模型的类型
        """
        # pylint: disable=E1101
        return self._get_data_type(self.__orig_bases__[0].__args__[1])  # type: ignore

    @staticmethod
    def _get_data_type(data: Any) -> D:  # type: ignore
        """从返回类型中提取数据类型

        如果返回类型是 List[D]，则提取内部的 D 类型。

        Parameters
        ----------
        data : Any
            返回类型

        Returns
        -------
        D
            数据模型类型
        """
        if get_origin(data) is list:
            data = get_args(data)[0]
        return data

    @classmethod
    def test(
        cls,
        params: dict[str, Any],
        credentials: dict[str, str] | None = None,
        **kwargs,
    ) -> None:
        """测试数据获取器

        此方法会测试 Fetcher 的 TET 流程的每个阶段，确保实现正确。

        测试内容
        --------

        1. 验证 require_credentials 是否为布尔值
        2. 验证 transform_query 返回正确类型的查询对象
        3. 验证 extract_data 返回非空数据
        4. 验证 transform_data 返回正确类型的数据对象

        Parameters
        ----------
        params : dict[str, Any]
            测试用的查询参数
        credentials : dict[str, str] | None, optional
            测试用的凭证，默认为 None

        Raises
        ------
        AssertionError
            如果任何测试失败
        """
        # pylint: disable=import-outside-toplevel
        from pandas import DataFrame

        # 执行 TET 流程
        query = cls.transform_query(params=params)
        data = run_async(
            cls.extract_data, query=query, credentials=credentials, **kwargs
        )
        result = cls.transform_data(query=query, data=data, **kwargs)

        # 类属性断言
        assert isinstance(
            cls.require_credentials, bool
        ), "require_credentials 必须是布尔值"

        # 查询对象断言
        assert query, "查询对象不能为 None"
        assert issubclass(
            type(query), cls.query_params_type
        ), f"查询类型不匹配。期望: {cls.query_params_type} 实际: {type(query)}"
        assert all(
            getattr(query, key) == value for key, value in params.items()
        ), f"查询参数值不正确。期望: {params} 实际: {query.__dict__}"

        # 原始数据断言
        if not isinstance(data, DataFrame):
            assert data, "数据不能为 None"
        else:
            assert not data.empty, "数据不能为空"
        is_list = isinstance(data, list)
        if is_list:
            assert all(
                field in data[0]
                for field in cls.data_type.model_fields
                if field in data[0]
            ), f"数据必须包含正确的字段。期望: {cls.data_type.model_fields} 实际: {data[0].__dict__}"
            # 确保数据尚未转换，以验证管道实现正确
            # 如果需要放宽限制，可以移除此断言
            assert (
                issubclass(type(data[0]), cls.data_type) is False
            ), f"数据不应该已经被转换。期望: {cls.data_type} 实际: {type(data[0])}"
        else:
            assert all(
                field in data for field in cls.data_type.model_fields if field in data
            ), f"数据必须包含正确的字段。期望: {cls.data_type.model_fields} 实际: {data.__dict__}"
            assert (
                issubclass(type(data), cls.data_type) is False
            ), f"数据不应该已经被转换。期望: {cls.data_type} 实际: {type(data)}"

        assert len(data) > 0, "数据不能为空"

        # 转换后数据断言
        transformed_data = (
            result.result if isinstance(result, AnnotatedResult) else result
        )

        assert transformed_data, "转换后的数据不能为 None"

        if isinstance(transformed_data, list):
            return_type_args = cls.return_type.__args__[0]
            return_type_is_dict = (
                hasattr(return_type_args, "__origin__")
                and return_type_args.__origin__ is dict
            )
            if return_type_is_dict:
                return_type_fields = (
                    return_type_args.__args__[1].__args__[0].model_fields
                )
                return_type = return_type_args.__args__[1].__args__[0]
            else:
                return_type_fields = return_type_args.model_fields
                return_type = return_type_args

            assert len(transformed_data) > 0, "转换后的数据不能为空"  # type: ignore
            assert all(
                field in transformed_data[0].__dict__ for field in return_type_fields  # type: ignore
            ), f"转换后的数据必须包含正确的字段。期望: {return_type_fields} 实际: {transformed_data[0].__dict__}"  # type: ignore
            assert issubclass(
                type(transformed_data[0]),
                cls.data_type,  # type: ignore
            ), f"转换后的数据必须是正确的类型。期望: {cls.data_type} 实际: {type(transformed_data[0])}"  # type: ignore
            assert issubclass(  # type: ignore
                type(transformed_data[0]),  # type: ignore
                return_type,
            ), f"转换后的数据必须是正确的类型。期望: {return_type} 实际: {type(transformed_data[0])}"  # type: ignore
        else:
            assert all(
                field in transformed_data.__dict__
                for field in cls.return_type.model_fields
            ), f"转换后的数据必须包含正确的字段。期望: {cls.return_type.model_fields} 实际: {transformed_data.__dict__}"
            assert issubclass(
                type(transformed_data), cls.data_type
            ), f"转换后的数据必须是正确的类型。期望: {cls.data_type} 实际: {type(transformed_data)}"
            assert issubclass(
                type(transformed_data), cls.return_type
            ), f"转换后的数据必须是正确的类型。期望: {cls.return_type} 实际: {type(transformed_data)}"
