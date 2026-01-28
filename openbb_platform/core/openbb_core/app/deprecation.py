"""OpenBB 废弃警告模块

本模块提供 OpenBB 特定的废弃警告实现。

设计说明
--------

此实现受 Pydantic 的特定警告启发，并根据 OpenBB 的需求进行了修改。
废弃警告用于通知用户某些功能即将在未来版本中移除。
"""

from openbb_core.app.version import VERSION, get_major_minor


class DeprecationSummary(str):
    """废弃摘要字符串

    一个可以存储废弃元数据的字符串子类。
    用于在 API 文档中显示废弃信息。

    Attributes
    ----------
    metadata : DeprecationWarning
        关联的废弃警告对象
    """

    def __new__(cls, value: str, metadata: DeprecationWarning):
        """创建新实例"""
        obj = str.__new__(cls, value)
        setattr(obj, "metadata", metadata)
        return obj


class OpenBBDeprecationWarning(DeprecationWarning):
    """OpenBB 特定的废弃警告

    当使用 OpenBB 中已废弃的功能时会抛出此警告。
    它提供了关于废弃时间和预计移除版本的信息。

    设计说明
    --------

    选择使用类变量是基于未来扩展的考虑。
    例如：当发布 Platform V5 时，可以创建一个名为 OpenBBDeprecatedSinceV4 的子类，
    继承自 OpenBBDeprecationWarning，并设置 since=4.X 和 expected_removal=5.0。
    将这些值定义在类级别而不是实例级别，可以确保平台废弃警告的一致性和清晰度。

    Attributes
    ----------
    message : str
        警告描述消息
    since : tuple[int, int]
        引入废弃的版本号 (主版本, 次版本)
    expected_removal : tuple[int, int]
        预计移除的版本号 (主版本, 次版本)
    long_message : str
        包含完整版本信息的详细消息
    """

    message: str
    since: tuple[int, int]
    expected_removal: tuple[int, int]

    def __init__(
        self,
        message: str,
        *args: object,
        since: tuple[int, int] | None = None,
        expected_removal: tuple[int, int] | None = None,
    ) -> None:
        """初始化废弃警告

        Parameters
        ----------
        message : str
            警告消息
        *args : object
            传递给父类的额外参数
        since : tuple[int, int] | None, optional
            引入废弃的版本，默认使用当前版本
        expected_removal : tuple[int, int] | None, optional
            预计移除的版本，默认为下一个主版本
        """
        super().__init__(message, *args)
        self.message = message.rstrip(".")
        self.since = since or get_major_minor(VERSION)
        self.expected_removal = expected_removal or (self.since[0] + 1, 0)
        self.long_message = (
            f"{self.message}. 在 OpenBB Platform V{self.since[0]}.{self.since[1]} 中废弃，"
            f"将在 V{self.expected_removal[0]}.{self.expected_removal[1]} 中移除。"
        )

    def __str__(self) -> str:
        """返回警告消息"""
        return self.long_message
