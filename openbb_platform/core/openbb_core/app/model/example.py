"""端点示例模块

本模块定义了 API 端点示例的表示类。
"""

from abc import abstractmethod
from datetime import date, datetime, timedelta
from typing import Any, Literal, _GenericAlias  # type: ignore

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    model_validator,
)

# 需要引号的类型集合
QUOTE_TYPES = {str, date}


class Example(BaseModel):
    """示例模型基类

    所有示例类型的抽象基类。

    Attributes
    ----------
    scope : str
        示例作用域（如 "api" 或 "python"）
    """

    scope: str

    model_config = ConfigDict(validate_assignment=True)

    @abstractmethod
    def to_python(self, **kwargs) -> str:
        """返回示例的 Python 代码表示"""


class APIEx(Example):
    """API 示例模型

    用于定义 API 端点的示例调用。

    Attributes
    ----------
    scope : Literal["api"]
        作用域，固定为 "api"
    description : str | None
        描述（当参数超过 3 个时必填）
    parameters : dict
        示例参数
    provider : str | None
        数据提供者（计算属性）
    """

    scope: Literal["api"] = "api"
    description: str | None = Field(
        default=None, description="可选描述，当参数超过 3 个时必填"
    )
    parameters: dict[str, str | int | float | bool | list[str] | list[dict[str, Any]]]

    @computed_field  # type: ignore[misc]
    @property
    def provider(self) -> str | None:
        """从参数中获取提供者"""
        return self.parameters.get("provider")  # type: ignore

    @model_validator(mode="before")
    @classmethod
    def validate_model(cls, values: dict) -> dict:
        """验证模型"""
        parameters = values.get("parameters", {})
        provider = parameters.pop("provider", None)

        if provider and not isinstance(provider, str):
            raise ValueError("Provider must be a string.")

        if len(parameters) > 3 and not values.get("description"):
            raise ValueError(
                "Description is required when there are more than 3 parameters."
            )

        return values

    @staticmethod
    def _unpack_type(type_: type) -> set:
        """解包类型，例如 Union[List[str], int] -> {typing._GenericAlias, int}"""
        if (
            hasattr(type_, "__args__")
            and type(type_) is not _GenericAlias  # pylint: disable=C0123
        ):
            return set().union(*map(APIEx._unpack_type, type_.__args__))  # type: ignore
        return {type_} if isinstance(type_, type) else {type(type_)}

    @staticmethod
    def _shift(i: int) -> float:
        """返回整数的变换值"""
        return 2 * (i + 1) / (2 * i) % 1 + 1

    @staticmethod
    def mock_data(
        dataset: Literal["timeseries", "panel"],
        size: int = 5,
        sample: dict[str, Any] | None = None,
        multiindex: dict[str, Any] | None = None,
    ) -> list[dict]:
        """从样本生成模拟数据

        Parameters
        ----------
        dataset : str
            返回的数据类型：
            - 'timeseries': 时间序列数据
            - 'panel': 面板数据（多重索引）
        size : int
            返回数据的大小，默认为 5
        sample : dict[str, Any] | None, optional
            数据样本，默认为 None
        multiindex : dict[str, Any] | None, optional
            多重索引定义，默认为 None

        时间序列默认样本：
        {
            "date": "2023-01-01",
            "open": 110.0,
            "high": 120.0,
            "low": 100.0,
            "close": 115.0,
            "volume": 10000,
        }

        面板数据默认样本：
        {
            "portfolio_value": 100000,
            "risk_free_rate": 0.02,
        }
        multiindex: {"asset_manager": "AM", "time": 0}

        Returns
        -------
        list[dict]
            包含模拟数据的字典列表
        """
        if dataset == "timeseries":
            sample = sample or {
                "date": "2023-01-01",
                "open": 110.0,
                "high": 120.0,
                "low": 100.0,
                "close": 115.0,
                "volume": 10000,
            }
            result = []
            for i in range(1, size + 1):
                s = APIEx._shift(i)
                obs = {}
                for k, v in sample.items():
                    if k == "date":
                        obs[k] = (
                            datetime.strptime(v, "%Y-%m-%d") + timedelta(days=i)
                        ).strftime("%Y-%m-%d")
                    else:
                        obs[k] = round(v * s, 2)
                result.append(obs)
            return result
        if dataset == "panel":
            sample = sample or {
                "portfolio_value": 100000.0,
                "risk_free_rate": 0.02,
            }
            multiindex = multiindex or {"asset_manager": "AM", "time": 0}
            multiindex_names = list(multiindex.keys())
            idx_1 = multiindex_names[0]
            idx_2 = multiindex_names[1]
            items_per_idx = 2
            item: dict[str, Any] = {
                "is_multiindex": True,
                "multiindex_names": str(multiindex_names),
            }
            # Iterate over the number of items to create and add them to the result
            result = []
            for i in range(1, size + 1):
                item[idx_1] = f"{idx_1}_{i}"
                for j in range(items_per_idx):
                    item[idx_2] = j
                    for k, v in sample.items():
                        if isinstance(v, str):
                            item[k] = f"{v}_{j}"
                        else:
                            item[k] = round(v * APIEx._shift(i + j), 2)
                    result.append(item.copy())
            return result
        raise ValueError(f"Dataset '{dataset}' not found.")

    def to_python(self, **kwargs) -> str:
        """返回示例的 Python 代码表示"""
        indentation = kwargs.get("indentation", "")
        func_path = kwargs.get("func_path", ".func_router.func_name")
        param_types: dict[str, type] = kwargs.get("param_types", {})
        prompt = kwargs.get("prompt", "")

        eg = ""
        if self.description:
            eg += f"{indentation}{prompt}# {self.description}\n"

        eg += f"{indentation}{prompt}obb{func_path}("
        for k, v in self.parameters.items():
            if k in param_types and (type_ := param_types.get(k)):
                if QUOTE_TYPES.intersection(self._unpack_type(type_)):
                    eg += f"{k}='{v}', "
                else:
                    eg += f"{k}={v}, "
            else:
                eg += f"{k}={v}, "

        eg = indentation + eg.strip(", ") + ")\n"

        return eg


class PythonEx(Example):
    """Python 示例模型

    用于定义 Python SDK 的代码示例。

    Attributes
    ----------
    scope : Literal["python"]
        作用域，固定为 "python"
    description : str
        示例描述
    code : list[str]
        代码行列表
    """

    scope: Literal["python"] = "python"
    description: str
    code: list[str]

    def to_python(self, **kwargs) -> str:
        """返回示例的 Python 代码表示"""
        indentation = kwargs.get("indentation", "")
        prompt = kwargs.get("prompt", "")

        eg = ""
        if self.description:
            eg += f"{indentation}{prompt}# {self.description}\n"

        for line in self.code:
            eg += f"{indentation}{prompt}{line}\n"

        return eg


def filter_list(
    examples: list[Example],
    providers: list[str],
) -> list[Example]:
    """过滤示例列表

    根据提供者过滤 API 示例。

    Parameters
    ----------
    examples : list[Example]
        示例列表
    providers : list[str]
        可用提供者列表

    Returns
    -------
    list[Example]
        过滤后的示例列表
    """
    return [
        e
        for e in examples
        if (isinstance(e, APIEx) and (not e.provider or e.provider in providers))
        or e.scope != "api"
    ]
