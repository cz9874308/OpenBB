"""OpenBB 数据提供者抽象类模块

本模块包含 OpenBB 数据提供者框架的核心抽象类定义。

核心概念
--------

- **Provider**: 数据提供者的入口点，负责注册和管理数据获取器
- **Fetcher**: 数据获取器，实现 TET (Transform-Extract-Transform) 模式
- **Data**: 标准化数据模型，所有输出数据的基类
- **QueryParams**: 查询参数模型，所有输入参数的基类
"""
