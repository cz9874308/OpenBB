"""OpenBB 核心应用工具函数模块

本模块提供数据转换和通用工具函数。

核心功能
--------

- **数据转换**: BaseModel ↔ DataFrame ↔ list ↔ dict ↔ ndarray
- **列提取**: 从 DataFrame 中提取目标列
- **缓存目录**: 获取用户缓存目录
- **参数验证**: 检查单项参数

数据转换流程
------------

```
用户数据（多种格式）
        ↓
    convert_to_basemodel()
        ↓
    list[Data] 或 Data
        ↓
    basemodel_to_df()
        ↓
    DataFrame
```
"""

import ast
import json
from datetime import time
from typing import TYPE_CHECKING, Union

from openbb_core.app.model.abstract.error import OpenBBError
from openbb_core.app.model.preferences import Preferences
from openbb_core.app.model.system_settings import SystemSettings
from openbb_core.provider.abstract.data import Data
from pydantic import ValidationError

if TYPE_CHECKING:
    # pylint: disable=import-outside-toplevel
    from numpy import ndarray
    from pandas import DataFrame, Series


def basemodel_to_df(
    data: list[Data] | Data,
    index: str | None = None,
) -> "DataFrame":
    """将 BaseModel 列表转换为 Pandas DataFrame

    Parameters
    ----------
    data : list[Data] | Data
        要转换的数据，可以是单个 Data 对象或列表
    index : str | None, optional
        要设置为索引的列名，默认为 None

    Returns
    -------
    DataFrame
        转换后的 DataFrame
    """
    # pylint: disable=import-outside-toplevel
    from pandas import DataFrame, to_datetime

    if isinstance(data, list):
        df = DataFrame(
            [d.model_dump(exclude_none=True, exclude_unset=True) for d in data]
        )
    else:
        try:
            df = DataFrame(data.model_dump(exclude_none=True, exclude_unset=True))
        except ValueError:
            df = DataFrame(
                data.model_dump(exclude_none=True, exclude_unset=True), index=["values"]
            )

    if "is_multiindex" in df.columns:
        col_names = ast.literal_eval(df.multiindex_names.unique()[0])
        df = df.set_index(col_names)
        df = df.drop(["is_multiindex", "multiindex_names"], axis=1)

    # If the date column contains dates only, convert them to a date to avoid encoding time data.
    if "date" in df.columns:
        df["date"] = df["date"].apply(to_datetime)
        if all(t.time() == time(0, 0) for t in df["date"]):
            df["date"] = df["date"].apply(lambda x: x.date())

    if index and index in df.columns:
        if index == "date":
            df.set_index("date", inplace=True)
            df.sort_index(axis=0, inplace=True)
        else:
            df = df.set_index(index) if index and index in df.columns else df

    return df


def df_to_basemodel(
    df: Union["DataFrame", "Series"], index: bool = False
) -> list[Data]:
    """将 Pandas DataFrame 转换为 BaseModel 列表

    Parameters
    ----------
    df : DataFrame | Series
        要转换的 DataFrame 或 Series
    index : bool, optional
        是否将索引作为列包含在结果中，默认为 False

    Returns
    -------
    list[Data]
        转换后的 Data 对象列表
    """
    # pylint: disable=import-outside-toplevel
    from pandas import MultiIndex, Series, to_datetime

    is_multiindex = isinstance(df.index, MultiIndex)

    if not is_multiindex and (index or df.index.name):
        df = df.reset_index()
    if isinstance(df, Series):
        df = df.to_frame()

    # Check if df has multiindex.  If so, add the index names to the df and a boolean column
    if isinstance(df.index, MultiIndex):
        df["is_multiindex"] = True
        df["multiindex_names"] = str(df.index.names)
        df = df.reset_index()

    # Converting to JSON will add T00:00:00.000 to all dates with no time element unless we format it as a string first.
    if "date" in df.columns:
        df["date"] = df["date"].apply(to_datetime)
        if all(t.time() == time(0, 0) for t in df["date"]):
            df["date"] = df["date"].apply(lambda x: x.date().strftime("%Y-%m-%d"))

    return [
        Data(**d) for d in json.loads(df.to_json(orient="records", date_format="iso"))
    ]


def list_to_basemodel(data_list: list) -> list[Data]:
    """将列表转换为 BaseModel 列表

    支持多种元素类型：Data、dict、DataFrame、Series。

    Parameters
    ----------
    data_list : list
        要转换的列表

    Returns
    -------
    list[Data]
        转换后的 Data 对象列表

    Raises
    ------
    ValueError
        如果列表元素类型不支持
    """
    # pylint: disable=import-outside-toplevel
    from pandas import DataFrame, Series

    base_models = []
    for item in data_list:
        if isinstance(item, Data) or issubclass(type(item), Data):
            base_models.append(item)
        elif isinstance(item, dict):
            base_models.append(Data(**item))
        elif isinstance(item, (DataFrame, Series)):
            base_models.extend(df_to_basemodel(item))
        else:
            raise ValueError(f"Unsupported list item type: {type(item)}")
    return base_models


def dict_to_basemodel(data_dict: dict) -> Data:
    """将字典转换为 BaseModel

    Parameters
    ----------
    data_dict : dict
        要转换的字典

    Returns
    -------
    Data
        转换后的 Data 对象

    Raises
    ------
    ValueError
        如果验证失败
    """
    try:
        return Data(**data_dict)
    except ValidationError as e:
        raise ValueError(
            f"Validation error when converting dict to BaseModel: {e}"
        ) from e


def ndarray_to_basemodel(array: "ndarray") -> list[Data]:
    """将 NumPy 数组转换为 BaseModel 列表

    仅支持二维数组，行作为记录。

    Parameters
    ----------
    array : ndarray
        要转换的二维数组

    Returns
    -------
    list[Data]
        转换后的 Data 对象列表

    Raises
    ------
    ValueError
        如果数组不是二维的
    """
    # Assuming a 2D array where rows are records
    if array.ndim != 2:
        raise ValueError("Only 2D arrays are supported.")
    return [
        Data(**{f"column_{i}": value for i, value in enumerate(row)}) for row in array
    ]


def convert_to_basemodel(data) -> Data | list[Data]:
    """将不同类型转换为 BaseModel 的分发函数

    自动识别输入数据类型并调用相应的转换函数。

    Parameters
    ----------
    data : Any
        要转换的数据，支持 Data、list、dict、DataFrame、Series、ndarray

    Returns
    -------
    Data | list[Data]
        转换后的 Data 对象或列表

    Raises
    ------
    ValueError
        如果数据类型不支持
    """
    # pylint: disable=import-outside-toplevel
    from numpy import ndarray
    from pandas import DataFrame, Series

    if isinstance(data, Data) or issubclass(type(data), Data):
        return data
    if isinstance(data, list):
        return list_to_basemodel(data)
    if isinstance(data, dict):
        return dict_to_basemodel(data)
    if isinstance(data, (DataFrame, Series)):
        return df_to_basemodel(data)
    if isinstance(data, ndarray):
        return ndarray_to_basemodel(data)
    raise ValueError(f"Unsupported data type: {type(data)}")


def get_target_column(df: "DataFrame", target: str) -> "Series":
    """从时间序列数据中获取目标列

    Parameters
    ----------
    df : DataFrame
        数据 DataFrame
    target : str
        目标列名

    Returns
    -------
    Series
        目标列数据

    Raises
    ------
    ValueError
        如果目标列不存在
    """
    if target not in df.columns:
        choices = ", ".join(df.columns)
        raise ValueError(
            f"Target column '{target}' not found in data. Choose from {choices}"
        )
    return df[target]


def get_target_columns(df: "DataFrame", target_columns: list[str]) -> "DataFrame":
    """从时间序列数据中获取多个目标列

    Parameters
    ----------
    df : DataFrame
        数据 DataFrame
    target_columns : list[str]
        目标列名列表

    Returns
    -------
    DataFrame
        仅包含目标列的 DataFrame
    """
    # pylint: disable=import-outside-toplevel
    from pandas import DataFrame

    df_result = DataFrame()
    for target in target_columns:
        df_result[target] = get_target_column(df, target).to_frame()
    return df_result


def get_user_cache_directory() -> str:
    """获取用户缓存目录

    从用户设置文件中读取缓存目录配置，
    如果未配置则使用默认值。

    Returns
    -------
    str
        缓存目录路径
    """
    file = SystemSettings().model_dump()["user_settings_path"]

    with open(file) as settings_file:
        contents = settings_file.read()

    try:
        settings = json.loads(contents)["preferences"]
    except KeyError:
        settings = None
    cache_dir = (
        settings["cache_directory"]
        if settings and "cache_directory" in settings
        else Preferences().cache_directory
    )
    return cache_dir


def check_single_item(value: str | None, message: str | None = None) -> str | None:
    """检查字符串是否只包含单个项目

    如果字符串包含逗号或分号分隔符，则抛出错误。

    Parameters
    ----------
    value : str | None
        要检查的字符串
    message : str | None, optional
        自定义错误消息，默认为 None

    Returns
    -------
    str | None
        原始值（如果验证通过）

    Raises
    ------
    OpenBBError
        如果字符串包含多个项目
    """
    if value and isinstance(value, str) and ("," in value or ";" in value):
        raise OpenBBError(message if message else "multiple items not allowed")
    return value
