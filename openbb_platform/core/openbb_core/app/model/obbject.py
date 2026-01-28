"""OBBject 输出对象模块

本模块定义了 OBBject 类，作为所有 OpenBB 命令的标准输出格式。

核心概念
--------

OBBject 是 OpenBB 平台的核心输出容器，提供：

1. **统一的输出格式**: 所有命令返回相同结构的对象
2. **多格式转换**: 支持转换为 DataFrame、dict、numpy、polars 等
3. **扩展访问器**: 通过 accessors 机制支持扩展功能（如 charting）
4. **元数据支持**: 携带提供者信息、警告、图表等元数据

数据转换方法
------------

- ``to_dataframe()``: 转换为 Pandas DataFrame
- ``to_df()``: to_dataframe 的别名
- ``to_dict()``: 转换为字典
- ``to_polars()``: 转换为 Polars DataFrame
- ``to_numpy()``: 转换为 NumPy 数组
- ``to_llm()``: 转换为 LLM 友好的 JSON 格式

示例
----

```python
from openbb import obb

# 获取数据
result = obb.equity.price.historical(symbol="AAPL")

# 转换格式
df = result.to_dataframe()
data_dict = result.to_dict()

# 显示图表（如果有）
result.show()
```
"""

# pylint: disable=too-many-branches, too-many-locals, too-many-statements

from collections.abc import Callable, Hashable
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    Literal,
    TypeVar,
)

from openbb_core.app.model.abstract.error import OpenBBError
from openbb_core.app.model.abstract.tagged import Tagged
from openbb_core.app.model.abstract.warning import Warning_
from openbb_core.app.model.charts.chart import Chart
from openbb_core.provider.abstract.annotated_result import AnnotatedResult
from openbb_core.provider.abstract.data import Data
from pydantic import BaseModel, Field, PrivateAttr

if TYPE_CHECKING:
    from numpy import ndarray  # noqa
    from pandas import DataFrame  # noqa
    from openbb_core.app.query import Query  # noqa

    try:
        from polars import DataFrame as PolarsDataFrame  # type: ignore
    except ImportError:
        PolarsDataFrame = None

# 结果类型变量
T = TypeVar("T")


class OBBject(Tagged, Generic[T]):
    """OpenBB 标准输出对象

    所有 OpenBB 命令的标准返回类型，提供统一的数据访问接口。

    OBBject 是一个泛型类，T 表示 results 字段的类型。
    它支持通过 accessors 机制动态添加扩展功能。

    Attributes
    ----------
    results : T | None
        可序列化的结果数据
    provider : str | None
        数据提供者名称
    warnings : list[Warning_] | None
        警告列表
    chart : Chart | None
        图表对象（需要 openbb-charting 扩展）
    extra : dict[str, Any]
        额外信息（如元数据）

    类属性
    ------
    accessors : ClassVar[set[str]]
        已注册的访问器名称集合
    _user_settings : ClassVar[BaseModel | None]
        用户设置缓存
    _system_settings : ClassVar[BaseModel | None]
        系统设置缓存
    """

    accessors: ClassVar[set[str]] = set()
    _user_settings: ClassVar[BaseModel | None] = None
    _system_settings: ClassVar[BaseModel | None] = None

    results: T | None = Field(
        default=None,
        description="可序列化的结果数据",
    )
    provider: str | None = Field(  # type: ignore
        default=None,
        description="数据提供者名称",
    )
    warnings: list[Warning_] | None = Field(
        default=None,
        description="警告列表",
    )
    chart: Chart | None = Field(
        default=None,
        description="图表对象",
    )
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="额外信息",
    )
    _route: str | None = PrivateAttr(
        default=None,
    )
    _standard_params: dict[str, Any] | None = PrivateAttr(
        default_factory=dict,
    )
    _extra_params: dict[str, Any] | None = PrivateAttr(
        default_factory=dict,
    )

    def __repr__(self) -> str:
        """返回对象的可读字符串表示"""
        items = [
            f"{k}: {v}"[:83] + ("..." if len(f"{k}: {v}") > 83 else "")
            for k, v in self.model_dump().items()
        ]
        return f"{self.__class__.__name__}\n\n" + "\n".join(items)

    def to_df(
        self,
        index: str | None | None = "date",
        sort_by: str | None = None,
        ascending: bool | None = None,
    ) -> "DataFrame":
        """转换为 DataFrame（to_dataframe 的别名）

        支持从以下可序列化数据格式创建 Pandas DataFrame：

        - List[BaseModel]
        - List[Dict]
        - List[List]
        - List[str]
        - List[int]
        - List[float]
        - Dict[str, Dict]
        - Dict[str, List]
        - Dict[str, BaseModel]

        其他支持的格式：
        - str

        Parameters
        ----------
        index : str | None, optional
            用作索引的列名，默认为 "date"
        sort_by : str | None, optional
            排序依据的列名
        ascending : bool | None, optional
            是否升序排序

        Returns
        -------
        DataFrame
            Pandas DataFrame
        """
        return self.to_dataframe(index=index, sort_by=sort_by, ascending=ascending)

    def to_dataframe(  # noqa: PLR0912
        self,
        index: str | None | None = "date",
        sort_by: str | None = None,
        ascending: bool | None = None,
    ) -> "DataFrame":
        """将结果转换为 Pandas DataFrame

        支持从以下可序列化数据格式创建 Pandas DataFrame：

        - List[BaseModel]
        - List[Dict]
        - List[List]
        - List[str]
        - List[int]
        - List[float]
        - Dict[str, Dict]
        - Dict[str, List]
        - Dict[str, BaseModel]

        其他支持的格式：
        - str

        Parameters
        ----------
        index : str | None, optional
            用作索引的列名，默认为 "date"
        sort_by : str | None, optional
            排序依据的列名
        ascending : bool | None, optional
            是否升序排序

        Returns
        -------
        DataFrame
            Pandas DataFrame

        Raises
        ------
        OpenBBError
            如果结果为空或数据格式不支持
        """
        # pylint: disable=import-outside-toplevel
        from pandas import DataFrame, Series, concat  # noqa
        from openbb_core.app.utils import basemodel_to_df  # noqa

        def is_list_of_basemodel(items: list[T] | T) -> bool:
            return isinstance(items, list) and all(
                isinstance(item, BaseModel) for item in items
            )

        if self.results is None or not self.results:
            raise OpenBBError("Results not found.")

        if isinstance(self.results, DataFrame):
            return self.results

        try:
            res = self.results
            df = None
            sort_columns = True

            # BaseModel
            if isinstance(res, BaseModel):
                res_dict = res.model_dump(  # pylint: disable=no-member
                    exclude_unset=True, exclude_none=True
                )
                # Model is serialized as a dict[str, list] or list[dict]
                if (
                    (
                        isinstance(res_dict, dict)
                        and res_dict
                        and all(isinstance(v, list) for v in res_dict.values())
                    )
                    or isinstance(res_dict, list)
                    and all(isinstance(item, dict) for item in res_dict)
                ):
                    df = DataFrame(res_dict)
                    sort_columns = False
                else:
                    series = Series(res_dict, name=res.__class__.__name__)
                    df = series.to_frame().reset_index()
                    sort_columns = False

            # Dict[str, Any]
            elif isinstance(res, dict):
                try:
                    df = DataFrame.from_dict(res).T
                except ValueError:
                    try:
                        df = DataFrame.from_dict(res, orient="index")
                    except ValueError:
                        series = Series(res, name="values")
                        df = series.to_frame().reset_index()
                sort_columns = False

            # List[Dict]
            elif isinstance(res, list) and len(res) == 1 and isinstance(res[0], dict):
                r = res[0]
                dict_of_df = {}

                for k, v in r.items():
                    # Dict[str, List[BaseModel]]
                    if is_list_of_basemodel(v):
                        dict_of_df[k] = basemodel_to_df(v, index)
                        sort_columns = False
                    # Dict[str, Any]
                    else:
                        dict_of_df[k] = DataFrame(v)

                df = concat(dict_of_df, axis=1)

            # List[BaseModel]
            elif is_list_of_basemodel(res):
                dt: list[Data] | Data = res  # type: ignore
                r = dt[0] if isinstance(dt, list) and len(dt) == 1 else None  # type: ignore
                if r and all(
                    prop.get("type") == "array" for prop in r.model_json_schema()["properties"].values()  # type: ignore
                ):
                    sort_columns = False
                    df = DataFrame(r.model_dump(exclude_unset=True, exclude_none=True))  # type: ignore
                else:
                    df = basemodel_to_df(dt, index)
                    sort_columns = False
            # str
            elif isinstance(res, str):
                df = DataFrame([res])
            # List[List | str | int | float] | Dict[str, Dict | List | BaseModel]
            else:
                try:
                    df = DataFrame(res)  # type: ignore[call-overload]
                except ValueError:
                    if isinstance(res, dict):
                        df = DataFrame([res])

            if df is None:
                raise OpenBBError("Unsupported data format.")

            # Set index, if any
            if index is not None and index in df.columns:
                df.set_index(index, inplace=True)

            # Drop columns that are all NaN, but don't rearrange columns
            if sort_columns:
                df.sort_index(axis=1, inplace=True)
            df = df.dropna(axis=1, how="all")

            # Sort by specified column
            if sort_by:
                df.sort_values(
                    by=sort_by,
                    ascending=ascending if ascending is not None else True,
                    inplace=True,
                )

        except OpenBBError as e:
            raise e
        except ValueError as ve:
            raise OpenBBError(
                f"ValueError: {ve}. Ensure the data format matches the expected format."
            ) from ve
        except TypeError as te:
            raise OpenBBError(
                f"TypeError: {te}. Check the data types in your results."
            ) from te
        except Exception as ex:
            raise OpenBBError(f"An unexpected error occurred: {ex}") from ex

        return df

    def to_polars(self) -> "PolarsDataFrame":  # type: ignore
        """将结果转换为 Polars DataFrame

        Returns
        -------
        PolarsDataFrame
            Polars DataFrame

        Raises
        ------
        ImportError
            如果未安装 polars
        """
        try:
            from polars import from_pandas  # type: ignore # pylint: disable=import-outside-toplevel
        except ImportError as exc:
            raise ImportError(
                "Please install polars: `pip install polars pyarrow`  to use this method."
            ) from exc

        return from_pandas(self.to_dataframe(index=None))

    def to_numpy(self) -> "ndarray":
        """将结果转换为 NumPy 数组

        Returns
        -------
        ndarray
            NumPy 数组
        """
        return self.to_dataframe(index=None).to_numpy()

    def to_dict(
        self,
        orient: Literal[
            "dict", "list", "series", "split", "tight", "records", "index"
        ] = "list",
    ) -> dict[Hashable, Any] | list[dict[Hashable, Any]]:
        """将结果转换为字典

        使用 Pandas 的 to_dict 方法支持的任意格式。

        Parameters
        ----------
        orient : Literal["dict", "list", "series", "split", "tight", "records", "index"]
            传递给 .to_dict() 方法的格式参数，默认为 "list"

        Returns
        -------
        dict[Hashable, Any] | list[dict[Hashable, Any]]
            字典列表或字典的字典（取决于 orient 参数）
        """
        df = self.to_dataframe(index=None)
        if (
            orient == "list"
            and isinstance(self.results, dict)
            and all(
                isinstance(value, dict)
                for value in self.results.values()  # pylint: disable=no-member
            )
        ):
            df = df.T
        results: dict | list = df.to_dict(orient=orient)

        if isinstance(results, dict) and orient == "list" and "index" in results:
            del results["index"]

        return results

    def to_llm(self) -> dict[Hashable, Any] | list[dict[Hashable, Any]]:
        """将结果转换为 LLM 兼容的输出格式

        生成 JSON 格式的输出，适合传递给大语言模型。

        Returns
        -------
        dict[Hashable, Any] | list[dict[Hashable, Any]]
            JSON 格式的数据
        """
        df = self.to_dataframe(index=None)

        results = df.to_json(
            orient="records",
            date_format="iso",
            date_unit="s",
        )

        return results  # type: ignore

    def show(self, **kwargs: Any) -> None:
        """显示图表

        显示关联的图表对象（需要 openbb-charting 扩展）。

        Parameters
        ----------
        **kwargs : Any
            传递给图表 show 方法的参数

        Raises
        ------
        OpenBBError
            如果图表未找到
        """
        # pylint: disable=no-member
        if not self.chart or not self.chart.fig:
            raise OpenBBError("未找到图表。")
        show_function: Callable = getattr(self.chart.fig, "show")
        show_function(**kwargs)

    @classmethod
    async def from_query(cls, query: "Query") -> "OBBject":
        """从查询创建 OBBject

        执行查询并将结果封装为 OBBject。

        Parameters
        ----------
        query : Query
            已初始化的查询对象

        Returns
        -------
        OBBject[ResultsType]
            包含结果的 OBBject
        """
        results = await query.execute()
        if isinstance(results, AnnotatedResult):
            return cls(
                results=results.result, extra={"results_metadata": results.metadata}
            )
        return cls(results=results)
