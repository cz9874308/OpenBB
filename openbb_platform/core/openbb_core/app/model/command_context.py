"""命令上下文模块

本模块定义了 CommandContext 类，用于封装命令执行的上下文环境。

用途
----

CommandContext 作为 'cc' 参数注入到命令函数中，
提供对用户设置和系统设置的访问。

示例
----

```python
def my_command(cc: CommandContext, symbol: str):
    # 访问用户凭证
    api_key = cc.user_settings.credentials.my_provider_api_key
    # 访问用户偏好设置
    output_type = cc.user_settings.preferences.output_type
    return results
```
"""

from openbb_core.app.model.system_settings import SystemSettings
from openbb_core.app.model.user_settings import UserSettings
from pydantic import BaseModel, Field


class CommandContext(BaseModel):
    """命令上下文

    封装命令执行所需的用户设置和系统设置。
    在命令执行时作为 'cc' 参数自动注入。

    Attributes
    ----------
    user_settings : UserSettings
        用户设置，包括凭证、偏好等
    system_settings : SystemSettings
        系统设置，包括日志配置、API 设置等
    """

    user_settings: UserSettings = Field(default_factory=UserSettings)
    system_settings: SystemSettings = Field(default_factory=SystemSettings)
