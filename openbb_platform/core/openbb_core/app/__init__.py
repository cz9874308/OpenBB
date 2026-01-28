"""OpenBB 核心应用模块

本模块是 OpenBB 平台的核心应用层，负责协调路由、命令执行和数据处理。

核心组件
--------

- **Router**: 路由系统，将 API 端点映射到命令处理函数
- **CommandRunner**: 命令执行器，负责执行数据查询命令
- **Query**: 查询类，封装查询参数和执行逻辑
- **OBBject**: 标准化输出对象，统一所有命令的返回格式

架构概览
--------

```
用户请求 → Router → CommandRunner → Query → Fetcher → OBBject
```
"""
