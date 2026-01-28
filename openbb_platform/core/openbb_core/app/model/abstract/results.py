"""结果类型定义

本模块定义了结果类型的基类。
"""

from pydantic import BaseModel

# Results 类型别名，等同于 BaseModel
# 用于类型注解，表示任何有效的结果类型
Results = BaseModel
