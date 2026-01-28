"""Registry for OBBjects."""

import json

from openbb_core.app.model.obbject import OBBject


class Registry:
    """OBBject 注册表类。

    存储和管理命令执行结果，支持按索引或键访问。
    """

    def __init__(self):
        """初始化注册表。"""
        self._obbjects: list[OBBject] = []

    @staticmethod
    def _contains_obbject(uuid: str, obbjects: list[OBBject]) -> bool:
        """检查注册表中是否包含指定 uuid 的 OBBject。"""
        return any(obbject.id == uuid for obbject in obbjects)

    def register(self, obbject: OBBject) -> bool:
        """将 OBBject 实例添加到注册表。"""
        if (
            isinstance(obbject, OBBject)
            and not self._contains_obbject(obbject.id, self._obbjects)
            and obbject.results
        ):
            self._obbjects.append(obbject)
            return True
        return False

    def get(self, arg: int | str) -> OBBject | None:
        """根据索引或键返回 OBBject。"""
        if isinstance(arg, int):
            return self._get_by_index(arg)
        if isinstance(arg, str):
            return self._get_by_key(arg)

        raise ValueError("Couldn't get the `OBBject` with the provided argument.")

    def _get_by_key(self, key: str) -> OBBject | None:
        """根据键返回 OBBject。"""
        for obbject in self._obbjects:
            if obbject.extra.get("register_key", "") == key:
                return obbject
        return None

    def _get_by_index(self, idx: int) -> OBBject | None:
        """根据索引返回 OBBject。"""
        # the list should work as a stack
        # i.e., the last element needs to be accessed by idx=0 and so on
        reversed_list = list(reversed(self._obbjects))

        # check if the index is out of bounds
        if idx >= len(reversed_list):
            return None

        return reversed_list[idx]

    def remove(self, idx: int = -1):
        """移除指定索引的 OBBject，默认移除最后一个元素。"""
        # the list should work as a stack
        # i.e., the last element needs to be accessed by idx=0 and so on
        reversed_list = list(reversed(self._obbjects))
        del reversed_list[idx]
        self._obbjects = list(reversed(reversed_list))

    @property
    def all(self) -> dict[int, dict]:
        """返回注册表中的所有 OBBject。"""

        def _handle_standard_params(obbject: OBBject) -> str:
            """处理 OBBject 的标准参数。"""
            standard_params_json = ""
            std_params = getattr(
                obbject, "_standard_params", {}
            )  # pylint: disable=protected-access
            if std_params:
                standard_params = {
                    k: str(v)[:30] for k, v in std_params.items() if v and k != "data"
                }
                standard_params_json = json.dumps(standard_params)

            return standard_params_json

        def _handle_data_repr(obbject: OBBject) -> str:
            """处理 OBBject 的数据表示。"""
            data_repr = ""
            if hasattr(obbject, "results") and obbject.results:
                data_schema = (
                    obbject.results[0].model_json_schema()
                    if obbject.results
                    and isinstance(obbject.results, list)
                    and hasattr(obbject.results[0], "model_json_schema")
                    else ""
                )
                if data_schema and "title" in data_schema:
                    data_repr = f"{data_schema['title']}"  # type: ignore
                if data_schema and "description" in data_schema:
                    data_repr += f" - {data_schema['description'].split('.')[0]}"  # type: ignore

            return data_repr

        obbjects = {}
        for i, obbject in enumerate(list(reversed(self._obbjects))):
            obbjects[i] = {
                "route": obbject._route,  # pylint: disable=protected-access
                "provider": obbject.provider,
                "standard params": _handle_standard_params(obbject),
                "data": _handle_data_repr(obbject),
                "command": obbject.extra.get("command", ""),
                "key": obbject.extra.get("register_key", ""),
            }

        return obbjects

    @property
    def obbjects(self) -> list[OBBject]:
        """返回注册表中的所有 OBBject 列表。"""
        return self._obbjects

    @property
    def obbject_keys(self) -> list[str]:
        """返回注册表中的所有 OBBject 键。"""
        return [
            obbject.extra["register_key"]
            for obbject in self._obbjects
            if "register_key" in obbject.extra
        ]
