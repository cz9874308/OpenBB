"""数据提供者接口模块

本模块定义了 ProviderInterface 类，作为 OpenBB 数据提供者的统一接口层。

核心概念
--------

ProviderInterface 是连接路由系统和数据提供者的桥梁：

1. **参数标准化**: 将各提供者的参数统一为 StandardParams 和 ExtraParams
2. **数据标准化**: 将各提供者的数据统一为 StandardData 和 ExtraData
3. **动态类型生成**: 为 FastAPI 依赖注入动态生成 dataclass 和 Pydantic 模型
4. **查询执行**: 通过 QueryExecutor 执行实际的数据查询

架构概览
--------

```
用户请求
    ↓
ProviderChoices (选择提供者)
    ↓
StandardParams + ExtraParams (参数)
    ↓
QueryExecutor.execute()
    ↓
StandardData + ExtraData (数据)
    ↓
OBBject (响应)
```
"""

from collections.abc import Callable
from dataclasses import dataclass, make_dataclass
from difflib import SequenceMatcher
from typing import (
    Annotated,
    Any,
    Literal,
    Optional,
    Union,
    get_args,
    get_origin,
)

from fastapi import Body, Query
from openbb_core.app.model.abstract.singleton import SingletonMeta
from openbb_core.app.model.obbject import OBBject
from openbb_core.provider.query_executor import QueryExecutor
from openbb_core.provider.registry_map import MapType, RegistryMap
from openbb_core.provider.utils.helpers import to_snake_case
from pydantic import (
    BaseModel,
    ConfigDict,
    Discriminator,
    Field,
    SerializeAsAny,
    Tag,
    create_model,
)
from pydantic.fields import FieldInfo

# 字段类型元组：(名称, 类型注解, 默认值)
TupleFieldType = tuple[str, type | None, Any | None]


@dataclass
class DataclassField:
    """数据类字段

    用于构建动态 dataclass 的字段信息。

    Attributes
    ----------
    name : str
        字段名称
    annotation : type | None
        类型注解
    default : Any | None
        默认值
    """

    name: str
    annotation: type | None
    default: Any | None


@dataclass
class StandardParams:
    """标准参数数据类

    所有标准查询参数 dataclass 的基类。
    标准参数是跨提供者通用的参数。
    """


@dataclass
class ExtraParams:
    """扩展参数数据类

    所有扩展查询参数 dataclass 的基类。
    扩展参数是特定提供者独有的参数。
    """


class StandardData(BaseModel):
    """标准数据模型

    所有标准数据模型的基类。
    标准数据字段是跨提供者通用的字段。
    """


class ExtraData(BaseModel):
    """扩展数据模型

    所有扩展数据模型的基类。
    扩展数据字段是特定提供者独有的字段。
    """


@dataclass
class ProviderChoices:
    """提供者选择数据类

    用于 FastAPI 依赖注入的提供者选择。

    Attributes
    ----------
    provider : Literal
        可选的提供者名称字面量类型
    """

    provider: Literal  # type: ignore


class ProviderInterface(metaclass=SingletonMeta):
    """数据提供者接口类

    作为单例模式实现，提供统一的接口访问所有已注册的数据提供者。

    ProviderInterface 负责：
    - 管理提供者注册表映射
    - 为每个数据模型生成参数和数据的 dataclass
    - 创建查询执行器
    - 生成 FastAPI 依赖注入所需的类型

    Attributes
    ----------
    map : MapType
        提供者信息字典
    credentials : dict[str, list[str]]
        提供者到凭证的映射
    model_providers : dict[str, ProviderChoices]
        模型到提供者选择的映射
    params : dict[str, dict[str, StandardParams | ExtraParams]]
        模型到参数的映射
    data : dict[str, dict[str, StandardData | ExtraData]]
        模型到数据的映射
    return_schema : dict[str, type[BaseModel]]
        模型到返回 schema 的映射
    available_providers : list[str]
        可用提供者列表
    provider_choices : type
        提供者名称字面量的 dataclass
    models : list[str]
        模型名称列表
    return_annotations : dict[str, type[OBBject]]
        返回类型注解映射
    """

    def __init__(
        self,
        registry_map: RegistryMap | None = None,
        query_executor: QueryExecutor | None = None,
    ) -> None:
        """初始化提供者接口

        Parameters
        ----------
        registry_map : RegistryMap | None, optional
            注册表映射，默认创建新实例
        query_executor : QueryExecutor | None, optional
            查询执行器类，默认使用 QueryExecutor
        """
        self._registry_map = registry_map or RegistryMap()
        self._query_executor = query_executor or QueryExecutor

        self._map = self._registry_map.standard_extra
        # TODO: Try these 4 methods in a single iteration
        self._model_providers_map = self._generate_model_providers_dc(self._map)
        self._params = self._generate_params_dc(self._map)
        self._data = self._generate_data_dc(self._map)
        self._return_schema = self._generate_return_schema(self._data)
        self._return_annotations = self._generate_return_annotations(
            self._registry_map.original_models
        )

        self._available_providers = self._registry_map.available_providers
        self._provider_choices = self._get_provider_choices(self._available_providers)

    @property
    def map(self) -> MapType:
        """获取提供者信息字典"""
        return self._map

    @property
    def credentials(self) -> dict[str, list[str]]:
        """获取提供者到凭证的映射"""
        return self._registry_map.credentials

    @property
    def model_providers(self) -> dict[str, ProviderChoices]:
        """获取模型到提供者选择的映射"""
        return self._model_providers_map

    @property
    def params(self) -> dict[str, dict[str, StandardParams | ExtraParams]]:
        """获取模型到参数的映射"""
        return self._params

    @property
    def data(self) -> dict[str, dict[str, StandardData | ExtraData]]:
        """获取模型到数据的映射"""
        return self._data

    @property
    def return_schema(self) -> dict[str, type[BaseModel]]:
        """获取合并后的数据 schema 字典"""
        return self._return_schema

    @property
    def available_providers(self) -> list[str]:
        """获取可用提供者列表"""
        return self._available_providers

    @property
    def provider_choices(self) -> type:
        """获取提供者名称字面量的 dataclass"""
        return self._provider_choices

    @property
    def models(self) -> list[str]:
        """获取模型名称列表"""
        return self._registry_map.models

    @property
    def return_annotations(self) -> dict[str, type[OBBject]]:
        """获取返回类型注解映射"""
        return self._return_annotations

    def create_executor(self) -> QueryExecutor:
        """创建查询执行器

        Returns
        -------
        QueryExecutor
            查询执行器实例
        """
        return self._query_executor(self._registry_map.registry)  # type: ignore[operator]

    @staticmethod
    def _merge_fields(
        current: DataclassField, incoming: DataclassField, query: bool = False
    ) -> DataclassField:
        """合并两个 dataclass 字段

        当多个提供者定义相同字段时，合并它们的描述和类型。

        Parameters
        ----------
        current : DataclassField
            当前字段
        incoming : DataclassField
            要合并的字段
        query : bool, optional
            是否为查询参数，默认为 False

        Returns
        -------
        DataclassField
            合并后的字段
        """
        curr_name = current.name
        curr_type: type | None = current.annotation
        curr_desc = getattr(current.default, "description", "")
        curr_json_schema_extra = getattr(current.default, "json_schema_extra", {})

        inc_type: type | None = incoming.annotation
        inc_desc = getattr(incoming.default, "description", "")
        inc_json_schema_extra = getattr(incoming.default, "json_schema_extra", {})

        def split_desc(desc: str) -> str:
            """分割字段描述，移除提供者标签和多项文本"""
            item = desc.split(" (provider: ")
            detail = item[0] if item else ""
            # Also remove "Multiple comma separated items allowed." for comparison
            detail = detail.replace(" Multiple comma separated items allowed.", "")
            detail = detail.replace("Multiple comma separated items allowed.", "")
            return detail.strip()

        def merge_json_schema_extra(curr: dict, inc: dict) -> dict:
            """合并 JSON schema extra 属性"""
            for key in curr.keys() & inc.keys():
                # Merge keys that are in both dictionaries if both are lists
                curr_value = curr[key]
                inc_value = inc[key]
                if isinstance(curr_value, list) and isinstance(inc_value, list):
                    curr[key] = list(set(curr.get(key, []) + inc.get(key, [])))
                    inc.pop(key)

            # Add any remaining keys from inc to curr
            curr.update(inc)
            return curr

        json_schema_extra: dict = merge_json_schema_extra(
            curr=curr_json_schema_extra or {}, inc=inc_json_schema_extra or {}
        )

        curr_detail = split_desc(curr_desc)
        inc_detail = split_desc(inc_desc)

        curr_title = getattr(current.default, "title", "") or ""
        inc_title = getattr(incoming.default, "title", "") or ""
        # Filter out empty titles and join
        provider_list = [t for t in [curr_title, inc_title] if t]
        providers = ",".join(provider_list)
        formatted_prov = ", ".join(provider_list)

        if SequenceMatcher(None, curr_detail, inc_detail).ratio() > 0.8:
            new_desc = f"{curr_detail} (provider: {formatted_prov})"
        else:
            new_desc = f"{curr_desc};\n    {inc_desc}"

        QF: Callable = Query if query else FieldInfo  # type: ignore[assignment]
        merged_default = QF(
            default=getattr(current.default, "default", None),
            title=providers,
            description=new_desc,
            json_schema_extra=json_schema_extra,
        )

        merged_type: type | None = (
            Union[curr_type, inc_type] if curr_type != inc_type else curr_type  # type: ignore[assignment]  # noqa
        )

        return DataclassField(curr_name, merged_type, merged_default)

    @staticmethod
    def _create_field(
        name: str,
        field: FieldInfo,
        provider_name: str | None = None,
        query: bool = False,
        force_optional: bool = False,
    ) -> DataclassField:
        new_name = name.replace(".", "_")
        annotation = field.annotation

        additional_description = ""
        choices: dict = {}
        if extra := field.json_schema_extra:
            providers: list = []
            for p, v in extra.items():  # type: ignore
                if isinstance(v, dict) and v.get("multiple_items_allowed"):
                    providers.append(p)
                    choices[p] = {"multiple_items_allowed": True, "choices": v.get("choices")}  # type: ignore
                elif isinstance(v, list) and "multiple_items_allowed" in v:
                    # For backwards compatibility, before this was a list
                    providers.append(p)
                    choices[p] = {"multiple_items_allowed": True, "choices": None}  # type: ignore
                elif isinstance(v, dict) and v.get("choices"):
                    choices[p] = {
                        "multiple_items_allowed": False,
                        "choices": v.get("choices"),
                    }

                if isinstance(v, dict) and v.get("x-widget_config"):
                    if p not in choices:
                        choices[p] = {"x-widget_config": v.get("x-widget_config")}
                    else:
                        choices[p]["x-widget_config"] = v.get("x-widget_config")

            if providers:
                if provider_name:
                    additional_description += " Multiple comma separated items allowed."
                else:
                    additional_description += (
                        " Multiple comma separated items allowed for provider(s): "
                        + ", ".join(providers)  # type: ignore[arg-type]
                        + "."
                    )
        provider_field = (
            f"(provider: {provider_name})" if provider_name != "openbb" else ""
        )
        description = (
            f"{field.description}{additional_description} {provider_field}"
            if provider_name and field.description
            else f"{field.description}{additional_description}"
        )

        if field.is_required():
            if force_optional:
                annotation = Optional[annotation]  # type: ignore  # noqa
                default = None
            else:
                default = ...
        else:
            default = field.default

        if (
            hasattr(annotation, "__name__")
            and annotation.__name__ in ["Dict", "dict", "Data"]  # type: ignore
            or field.kw_only is True
        ):
            return DataclassField(
                new_name,
                annotation,
                Body(
                    default=default,
                    title=provider_name,
                    description=description,
                    alias=field.alias or None,
                    json_schema_extra=choices,
                ),
            )

        if query:
            # We need to use query if we want the field description to show
            # up in the swagger, it's a fastapi limitation
            return DataclassField(
                new_name,
                annotation,
                Query(
                    default=default,
                    title=provider_name,
                    description=description,
                    alias=field.alias or None,
                    json_schema_extra=choices,
                ),
            )
        if provider_name:
            return DataclassField(
                new_name,
                annotation,
                Field(
                    default=default or None,
                    title=provider_name,
                    description=description,
                    json_schema_extra=choices,
                ),
            )

        return DataclassField(new_name, annotation, default)

    @classmethod
    def _extract_params(
        cls,
        providers: Any,
    ) -> tuple[dict[str, TupleFieldType], dict[str, TupleFieldType]]:
        """从映射中提取参数

        将提供者的参数分离为标准参数和扩展参数。

        Parameters
        ----------
        providers : Any
            提供者信息字典

        Returns
        -------
        tuple[dict[str, TupleFieldType], dict[str, TupleFieldType]]
            标准参数字典和扩展参数字典的元组
        """
        standard: dict[str, TupleFieldType] = {}
        extra: dict[str, TupleFieldType] = {}
        standard_fields = (
            providers.get("openbb", {}).get("QueryParams", {}).get("fields", {})
        )

        for provider_name, model_details in providers.items():
            if provider_name == "openbb":
                for name, field in model_details["QueryParams"]["fields"].items():
                    incoming = cls._create_field(name, field, query=True)

                    standard[incoming.name] = (
                        incoming.name,
                        incoming.annotation,
                        incoming.default,
                    )
            else:
                for name, field in model_details["QueryParams"]["fields"].items():
                    s_name = to_snake_case(name)

                    if name in standard_fields:
                        # Provider redefines a standard field - merge descriptions
                        # Check if descriptions differ before merging
                        standard_desc = standard_fields[name].description or ""
                        provider_desc = field.description or ""

                        if provider_desc and provider_desc != standard_desc:
                            # Create a field with provider-specific description
                            incoming = cls._create_field(
                                s_name,
                                field,
                                provider_name,
                                query=True,
                                force_optional=False,
                            )
                            # Merge into the standard field
                            if s_name in standard:
                                current = DataclassField(*standard[s_name])
                                updated = cls._merge_fields(
                                    current, incoming, query=True
                                )
                                standard[s_name] = (
                                    updated.name,
                                    updated.annotation,
                                    updated.default,
                                )
                    else:
                        # Extra field not in standard - add to extra params
                        incoming = cls._create_field(
                            s_name,
                            field,
                            provider_name,
                            query=True,
                            force_optional=True,
                        )

                        if incoming.name in extra:
                            current = DataclassField(*extra[incoming.name])
                            updated = cls._merge_fields(current, incoming, query=True)
                        else:
                            updated = incoming

                        extra[updated.name] = (
                            updated.name,
                            updated.annotation,
                            updated.default,
                        )

        return standard, extra

    @classmethod
    def _extract_data(
        cls,
        providers: Any,
    ) -> tuple[dict[str, TupleFieldType], dict[str, TupleFieldType]]:
        """从映射中提取数据字段

        将提供者的数据字段分离为标准字段和扩展字段。

        Parameters
        ----------
        providers : Any
            提供者信息字典

        Returns
        -------
        tuple[dict[str, TupleFieldType], dict[str, TupleFieldType]]
            标准数据字段字典和扩展数据字段字典的元组
        """
        standard: dict[str, TupleFieldType] = {}
        extra: dict[str, TupleFieldType] = {}

        for provider_name, model_details in providers.items():
            if provider_name == "openbb":
                for name, field in model_details["Data"]["fields"].items():
                    if (
                        name == "provider"
                        and field.description == "The data provider for the data."
                    ):  # noqa
                        continue
                    incoming = cls._create_field(name, field, "openbb")

                    standard[incoming.name] = (
                        incoming.name,
                        incoming.annotation,
                        incoming.default,
                    )
            else:
                for name, field in model_details["Data"]["fields"].items():
                    if name not in providers["openbb"]["Data"]["fields"]:
                        if (
                            name == "provider"
                            and field.description == "The data provider for the data."
                        ):  # noqa
                            continue
                        incoming = cls._create_field(
                            to_snake_case(name),
                            field,
                            provider_name,
                            force_optional=True,
                        )

                        if incoming.name in extra:
                            current = DataclassField(*extra[incoming.name])
                            updated = cls._merge_fields(current, incoming)
                        else:
                            updated = incoming

                        extra[updated.name] = (
                            updated.name,
                            updated.annotation,
                            updated.default,
                        )

        return standard, extra

    def _generate_params_dc(
        self, map_: MapType
    ) -> dict[str, dict[str, StandardParams | ExtraParams]]:
        """生成参数 dataclass

        创建可作为 FastAPI 依赖注入的 dataclass 字典。

        示例
        ----

        ```python
        @dataclass
        class CompanyNews(StandardParams):
            symbols: str = Query(...)
            page: int = Query(default=1)

        @dataclass
        class CompanyNews(ExtraParams):
            pageSize: int = Query(default=15, title="benzinga")
            displayOutput: int = Query(default="headline", title="benzinga")
            sort: str = Query(default=None, title="benzinga,polygon")
        ```

        Parameters
        ----------
        map_ : MapType
            提供者映射

        Returns
        -------
        dict[str, dict[str, StandardParams | ExtraParams]]
            模型名称到参数 dataclass 的映射
        """
        result: dict = {}

        for model_name, providers in map_.items():
            standard: dict
            extra: dict
            standard, extra = self._extract_params(providers)

            result[model_name] = {
                "standard": make_dataclass(
                    cls_name=model_name,
                    fields=list(standard.values()),  # type: ignore[arg-type]
                    bases=(StandardParams,),
                ),
                "extra": make_dataclass(
                    cls_name=model_name,
                    fields=list(extra.values()),  # type: ignore[arg-type]
                    bases=(ExtraParams,),
                ),
            }
        return result

    def _generate_model_providers_dc(self, map_: MapType) -> dict[str, ProviderChoices]:
        """生成按模型的提供者选择 dataclass

        创建模型名称到 dataclass 的映射，可作为 FastAPI 依赖注入。

        示例
        ----

        ```python
        @dataclass
        class CompanyNews(ProviderChoices):
            provider: Literal["provider_a", "provider_b"]
        ```

        Parameters
        ----------
        map_ : MapType
            提供者映射

        Returns
        -------
        dict[str, ProviderChoices]
            模型名称到提供者选择 dataclass 的映射
        """
        result: dict = {}

        for model_name, providers in map_.items():
            choices = sorted(list(providers.keys()))
            if "openbb" in choices:
                choices.remove("openbb")

            result[model_name] = make_dataclass(  # type: ignore
                cls_name=model_name,
                fields=[
                    (
                        "provider",
                        Literal[tuple(choices)],  # type: ignore
                        ... if len(choices) > 1 else choices[0],
                    )
                ],
                bases=(ProviderChoices,),
            )

        return result

    def _generate_data_dc(
        self, map_: MapType
    ) -> dict[str, dict[str, StandardData | ExtraData]]:
        """生成数据 dataclass

        创建数据模型的 dataclass 字典。

        示例
        ----

        ```python
        class EquityHistoricalData(StandardData):
            date: date
            open: PositiveFloat
            high: PositiveFloat
            low: PositiveFloat
            close: PositiveFloat
            adj_close: Optional[PositiveFloat]
            volume: PositiveFloat
        ```

        Parameters
        ----------
        map_ : MapType
            提供者映射

        Returns
        -------
        dict[str, dict[str, StandardData | ExtraData]]
            模型名称到数据 dataclass 的映射
        """
        result: dict = {}

        for model_name, providers in map_.items():
            standard: dict
            extra: dict
            standard, extra = self._extract_data(providers)
            result[model_name] = {
                "standard": make_dataclass(
                    cls_name=model_name,
                    fields=list(standard.values()),  # type: ignore[arg-type]
                    bases=(StandardData,),
                ),
                "extra": make_dataclass(
                    cls_name=model_name,
                    fields=list(extra.values()),  # type: ignore[arg-type]
                    bases=(ExtraData,),
                ),
            }

        return result

    def _generate_return_schema(
        self,
        data: dict[str, dict[str, StandardData | ExtraData]],
    ) -> dict[str, type[BaseModel]]:
        """生成返回 schema

        将标准数据和扩展数据合并为单个 BaseModel，
        作为 FastAPI 依赖注入使用。

        Parameters
        ----------
        data : dict[str, dict[str, StandardData | ExtraData]]
            数据 dataclass 字典

        Returns
        -------
        dict[str, type[BaseModel]]
            模型名称到 Pydantic 模型的映射
        """
        result: dict = {}
        for model_name, dataclasses in data.items():
            standard = dataclasses["standard"]
            extra = dataclasses["extra"]

            fields = standard.model_fields.copy()
            fields.update(extra.model_fields)

            fields_dict: dict[str, tuple[Any, Any]] = {}

            for name, field in fields.items():
                fields_dict[name] = (
                    field.annotation,
                    Field(
                        default=field.default,
                        title=field.title,
                        description=field.description,
                        alias=field.alias,
                        json_schema_extra=field.json_schema_extra,
                    ),
                )

            model_config = ConfigDict(extra="allow", populate_by_name=True)

            result[model_name] = create_model(  # type: ignore
                model_name,
                __config__=model_config,
                **fields_dict,  # type: ignore
            )

        return result

    def _get_provider_choices(self, available_providers: list[str]) -> type:
        return make_dataclass(
            cls_name="ProviderChoices",
            fields=[("provider", Literal[tuple(available_providers)])],  # type: ignore
            bases=(ProviderChoices,),
        )

    def _get_annotated_union(self, models: dict[str, Any]) -> Any:
        """获取带注解的 Union 类型

        为多个提供者的数据模型创建带区分器的 Union 类型。

        Parameters
        ----------
        models : dict[str, Any]
            提供者到模型的映射

        Returns
        -------
        Any
            带 Discriminator 注解的 Union 类型
        """

        def get_provider(v: type[BaseModel]):
            """获取模型的提供者名称，用于类型区分"""
            return getattr(v, "_provider", None)

        args = set()
        for provider, model in models.items():
            data = model["data"]
            # We set the provider to use it in discriminator function
            setattr(data, "_provider", provider)
            if get_origin(data) is Annotated:
                metadata = data.__metadata__ + (Tag(provider),)
                annotated_args = (get_args(data)[0],) + metadata
                args.add(Annotated[annotated_args])
            else:
                args.add(Annotated[data, Tag(provider)])
        meta = Discriminator(get_provider) if len(args) > 1 else None
        return SerializeAsAny[Annotated[Union[tuple(args)], meta]]  # type: ignore  # noqa

    def _generate_return_annotations(
        self, original_models: dict[str, dict[str, Any]]
    ) -> dict[str, type[OBBject]]:
        """生成 FastAPI 返回类型注解

        为每个数据模型生成带有提供者区分的 OBBject 类型。

        示例
        ----

        ```python
        class Data(BaseModel):
            ...

        class EquityData(Data):
            price: float

        class YFEquityData(EquityData):
            yf_field: str

        class AVEquityData(EquityData):
            av_field: str

        class OBBject(BaseModel):
            results: List[
                SerializeAsAny[
                    Annotated[
                        Union[
                            Annotated[YFEquityData, Tag("yf")],
                            Annotated[AVEquityData, Tag("av")],
                        ],
                        Discriminator(get_provider),
                    ]
                ]
            ]
        ```

        Parameters
        ----------
        original_models : dict[str, dict[str, Any]]
            原始模型字典

        Returns
        -------
        dict[str, type[OBBject]]
            模型名称到 OBBject 类型的映射
        """
        annotations = {}
        for name, models in original_models.items():
            outer = {model["results_type"] for model in models.values()}
            inner = self._get_annotated_union(models)
            full = Union[tuple((o[inner] if o else inner) for o in outer)]  # type: ignore  # noqa
            annotations[name] = create_model(
                f"OBBject_{name}",
                __base__=OBBject[full],  # type: ignore
                __doc__=f"OBBject with results of type {name}",
            )
        return annotations
