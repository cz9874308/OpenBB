"""单例模式元类实现

本模块提供单例模式的元类实现，用于确保类只有一个实例。
"""

from typing import Generic, TypeVar

T = TypeVar("T")


class SingletonMeta(type, Generic[T]):
    """单例模式元类

    使用此元类的类将自动实现单例模式，
    无论创建多少次实例，都会返回同一个对象。

    使用示例
    --------

    ```python
    class MySingleton(metaclass=SingletonMeta):
        def __init__(self, value):
            self.value = value

    # 两次创建都返回同一个实例
    a = MySingleton(1)
    b = MySingleton(2)
    assert a is b  # True
    ```

    注意
    ----
    当前实现不是线程安全的，在多线程环境中可能需要改进。
    """

    # TODO : 检查是否需要更新为线程安全版本
    _instances: dict[T, T] = {}

    def __call__(cls: "SingletonMeta", *args, **kwargs):
        """单例模式实现

        如果实例已存在，返回现有实例；
        否则创建新实例并缓存。
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance

        return cls._instances[cls]
