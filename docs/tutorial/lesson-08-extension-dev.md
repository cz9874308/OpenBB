# 第 8 课：自定义扩展开发

**⏱ 课时**：50 分钟  
**🎯 学习目标**：学会开发自己的 Provider 扩展  
**📚 难度**：⭐⭐⭐ 进阶

---

## 📖 本课内容

- [8.1 扩展开发概述](#81-扩展开发概述)
- [8.2 创建自定义 Provider](#82-创建自定义-provider)
- [8.3 实现 Fetcher](#83-实现-fetcher)
- [8.4 测试与调试](#84-测试与调试)
- [8.5 发布扩展](#85-发布扩展)
- [💡 实践任务](#-实践任务)

---

## 8.1 扩展开发概述

### 回顾扩展类型

```
┌─────────────────────────────────────────────────────────────┐
│                   OpenBB 扩展生态                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Provider Extension（本课重点）                            │
│   │                                                         │
│   │  作用：添加新的数据源                                    │
│   │  例子：连接新的 API、数据库、文件                        │
│   │                                                         │
│   │  核心组件：                                              │
│   │  ├── Provider 类   定义数据源元信息                      │
│   │  ├── Fetcher 类    实现数据获取逻辑                      │
│   │  └── 数据模型      定义输入参数和输出格式                 │
│   │                                                         │
│   └─────────────────────────────────────────────────────    │
│                                                             │
│   Router Extension                                          │
│   │  作用：添加新的命令路由                                  │
│   │  适用：添加全新的数据类别                                │
│   │                                                         │
│   └─────────────────────────────────────────────────────    │
│                                                             │
│   OBBject Extension                                         │
│   │  作用：扩展输出对象功能                                  │
│   │  例子：图表、技术分析、量化指标                          │
│   │                                                         │
│   └─────────────────────────────────────────────────────    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 开发流程

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  规划    │───▶│  编码    │───▶│  测试    │───▶│  发布    │
│          │    │          │    │          │    │          │
│ 确定数据 │    │ Provider │    │ 单元测试 │    │ 打包     │
│ 设计模型 │    │ Fetcher  │    │ 集成测试 │    │ 文档     │
│          │    │ 模型     │    │          │    │ 发布     │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

---

## 8.2 创建自定义 Provider

### 使用 Cookiecutter 模板

OpenBB 提供了项目模板，可以快速创建 Provider 项目：

```bash
# 安装 cookiecutter
pip install cookiecutter

# 使用 OpenBB Provider 模板
cookiecutter https://github.com/OpenBB-finance/openbb-cookiecutter
```

模板会提示你输入信息：

```
provider_name [my_provider]: my_data_source
author_name [Your Name]: 你的名字
author_email [your.email@example.com]: your@email.com
```

### 项目结构

生成的项目结构如下：

```
openbb_my_data_source/
├── openbb_my_data_source/
│   ├── __init__.py           # Provider 定义
│   ├── models/
│   │   ├── __init__.py
│   │   └── stock_price.py    # 数据模型和 Fetcher
│   └── utils/
│       └── helpers.py        # 辅助函数
├── tests/
│   └── test_stock_price.py   # 测试文件
├── pyproject.toml            # 项目配置
└── README.md
```

### 手动创建 Provider

如果你想手动创建，以下是完整的示例：

#### 1. 创建项目目录

```bash
mkdir -p openbb_my_provider/openbb_my_provider/models
cd openbb_my_provider
```

#### 2. 创建 Provider 定义

```python
# openbb_my_provider/__init__.py

"""My Custom Data Provider"""

from openbb_core.provider.abstract.provider import Provider

from openbb_my_provider.models.stock_price import MyStockPriceFetcher

my_provider = Provider(
    name="my_provider",
    description="我的自定义数据提供者",
    website="https://example.com",
    credentials=["my_provider_api_key"],  # 需要的凭证
    fetcher_dict={
        "EquityHistorical": MyStockPriceFetcher,  # 映射到标准命令
    },
)
```

### 关键概念说明

| 属性 | 说明 |
|------|------|
| `name` | Provider 的唯一标识符 |
| `description` | Provider 的描述 |
| `website` | 数据源官网 |
| `credentials` | 需要的 API 密钥列表 |
| `fetcher_dict` | 命令到 Fetcher 的映射 |

---

## 8.3 实现 Fetcher

### Fetcher 的结构

Fetcher 是数据获取的核心，需要实现 TET（Transform-Extract-Transform）模式：

```python
# openbb_my_provider/models/stock_price.py

"""股票价格 Fetcher 实现"""

from datetime import date
from typing import Any, Dict, List, Optional

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.abstract.data import Data
from pydantic import Field


# 步骤 1：定义查询参数模型
class MyStockPriceQueryParams(QueryParams):
    """股票价格查询参数"""
    
    symbol: str = Field(description="股票代码")
    start_date: Optional[date] = Field(
        default=None,
        description="开始日期"
    )
    end_date: Optional[date] = Field(
        default=None,
        description="结束日期"
    )


# 步骤 2：定义数据输出模型
class MyStockPriceData(Data):
    """股票价格数据"""
    
    date: date = Field(description="日期")
    open: float = Field(description="开盘价")
    high: float = Field(description="最高价")
    low: float = Field(description="最低价")
    close: float = Field(description="收盘价")
    volume: int = Field(description="成交量")
    
    # 可以添加自定义字段
    my_custom_field: Optional[str] = Field(
        default=None,
        description="自定义字段"
    )


# 步骤 3：实现 Fetcher 类
class MyStockPriceFetcher(
    Fetcher[MyStockPriceQueryParams, List[MyStockPriceData]]
):
    """股票价格数据获取器"""
    
    @staticmethod
    def transform_query(params: Dict[str, Any]) -> MyStockPriceQueryParams:
        """
        转换查询参数
        
        将用户输入的参数转换为 API 所需的格式
        """
        return MyStockPriceQueryParams(**params)
    
    @staticmethod
    async def aextract_data(
        query: MyStockPriceQueryParams,
        credentials: Optional[Dict[str, str]],
        **kwargs: Any,
    ) -> Dict:
        """
        提取数据（异步）
        
        调用外部 API 获取原始数据
        """
        import aiohttp
        
        # 获取 API 密钥
        api_key = credentials.get("my_provider_api_key") if credentials else None
        
        # 构建 API URL
        base_url = "https://api.example.com/v1/stock"
        url = f"{base_url}/{query.symbol}/historical"
        
        params = {}
        if query.start_date:
            params["start"] = query.start_date.isoformat()
        if query.end_date:
            params["end"] = query.end_date.isoformat()
        
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        
        # 发送请求
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API 错误: {response.status}")
    
    @staticmethod
    def transform_data(
        query: MyStockPriceQueryParams,
        data: Dict,
        **kwargs: Any,
    ) -> List[MyStockPriceData]:
        """
        转换数据
        
        将 API 返回的原始数据转换为标准格式
        """
        results = []
        
        for item in data.get("data", []):
            results.append(
                MyStockPriceData(
                    date=item["date"],
                    open=item["open"],
                    high=item["high"],
                    low=item["low"],
                    close=item["close"],
                    volume=item["volume"],
                    my_custom_field=item.get("extra_info"),
                )
            )
        
        return results
```

### TET 模式详解

```
┌─────────────────────────────────────────────────────────────┐
│                    TET 模式实现                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1️⃣ transform_query(params) -> QueryParams                  │
│     │                                                       │
│     │  输入: 用户参数字典 {"symbol": "AAPL", ...}           │
│     │  输出: QueryParams 对象                               │
│     │  作用: 参数验证和转换                                  │
│     │                                                       │
│     ▼                                                       │
│  2️⃣ aextract_data(query, credentials) -> Dict              │
│     │                                                       │
│     │  输入: QueryParams, API 凭证                          │
│     │  输出: 原始 API 响应                                   │
│     │  作用: 调用外部 API                                    │
│     │  注意: 是异步方法 (async)                              │
│     │                                                       │
│     ▼                                                       │
│  3️⃣ transform_data(query, data) -> List[Data]              │
│     │                                                       │
│     │  输入: QueryParams, 原始数据                          │
│     │  输出: 标准化的 Data 对象列表                          │
│     │  作用: 数据清洗和标准化                                │
│     │                                                       │
│     ▼                                                       │
│  📦 最终输出: OBBject(results=[...])                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 使用标准模型

如果你的数据符合 OpenBB 的标准模型，可以直接继承：

```python
from openbb_core.provider.standard_models.equity_historical import (
    EquityHistoricalQueryParams,
    EquityHistoricalData,
)

class MyStockPriceQueryParams(EquityHistoricalQueryParams):
    """继承标准查询参数，可添加额外字段"""
    my_extra_param: Optional[str] = Field(default=None)


class MyStockPriceData(EquityHistoricalData):
    """继承标准数据模型，可添加额外字段"""
    my_extra_field: Optional[float] = Field(default=None)
```

---

## 8.4 测试与调试

### 单元测试

```python
# tests/test_stock_price.py

import pytest
from openbb_my_provider.models.stock_price import (
    MyStockPriceFetcher,
    MyStockPriceQueryParams,
)


class TestMyStockPriceFetcher:
    """测试 MyStockPriceFetcher"""
    
    def test_transform_query(self):
        """测试参数转换"""
        params = {
            "symbol": "AAPL",
            "start_date": "2024-01-01",
            "end_date": "2024-06-30",
        }
        
        result = MyStockPriceFetcher.transform_query(params)
        
        assert isinstance(result, MyStockPriceQueryParams)
        assert result.symbol == "AAPL"
    
    def test_transform_data(self):
        """测试数据转换"""
        query = MyStockPriceQueryParams(symbol="AAPL")
        
        raw_data = {
            "data": [
                {
                    "date": "2024-01-02",
                    "open": 187.15,
                    "high": 188.44,
                    "low": 183.89,
                    "close": 185.64,
                    "volume": 82488700,
                }
            ]
        }
        
        result = MyStockPriceFetcher.transform_data(query, raw_data)
        
        assert len(result) == 1
        assert result[0].close == 185.64
    
    @pytest.mark.asyncio
    async def test_aextract_data(self):
        """测试数据提取（需要 mock）"""
        # 使用 pytest-asyncio 和 aioresponses 进行测试
        pass
```

### 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio

# 运行测试
pytest tests/ -v
```

### 本地调试

```python
# debug.py - 本地调试脚本

import asyncio
from openbb_my_provider.models.stock_price import MyStockPriceFetcher

async def test_fetcher():
    """本地测试 Fetcher"""
    
    # 1. 测试参数转换
    params = {"symbol": "AAPL", "start_date": "2024-01-01"}
    query = MyStockPriceFetcher.transform_query(params)
    print(f"Query: {query}")
    
    # 2. 测试数据提取（需要真实 API）
    # credentials = {"my_provider_api_key": "your_key"}
    # raw_data = await MyStockPriceFetcher.aextract_data(query, credentials)
    # print(f"Raw data: {raw_data}")
    
    # 3. 测试数据转换（使用模拟数据）
    mock_data = {
        "data": [
            {"date": "2024-01-02", "open": 187.15, "high": 188.44, 
             "low": 183.89, "close": 185.64, "volume": 82488700}
        ]
    }
    result = MyStockPriceFetcher.transform_data(query, mock_data)
    print(f"Transformed: {result}")

if __name__ == "__main__":
    asyncio.run(test_fetcher())
```

### 集成测试

安装你的 Provider 并在 OpenBB 中测试：

```bash
# 在开发模式安装
pip install -e .
```

```python
from openbb import obb

# 测试你的 Provider
data = obb.equity.price.historical("AAPL", provider="my_provider")
print(data)
```

---

## 8.5 发布扩展

### 项目配置

确保 `pyproject.toml` 配置正确：

```toml
[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"

[tool.poetry]
name = "openbb-my-provider"
version = "0.1.0"
description = "My custom OpenBB data provider"
authors = ["Your Name <your@email.com>"]
readme = "README.md"
packages = [{include = "openbb_my_provider"}]

[tool.poetry.dependencies]
python = "^3.9"
openbb-core = "^1.0.0"
aiohttp = "^3.8.0"

[tool.poetry.plugins."openbb_provider_extension"]
my_provider = "openbb_my_provider:my_provider"
```

### 入口点配置

关键是 `[tool.poetry.plugins."openbb_provider_extension"]` 部分，这让 OpenBB 能自动发现你的 Provider。

### 打包发布

```bash
# 构建包
poetry build

# 发布到 PyPI
poetry publish

# 或发布到测试 PyPI
poetry publish -r testpypi
```

### 贡献到官方仓库

如果你想将 Provider 贡献给 OpenBB 官方：

1. Fork OpenBB 仓库
2. 在 `openbb_platform/providers/` 下创建你的 Provider
3. 添加测试
4. 提交 Pull Request

### 文档

为你的 Provider 编写清晰的文档：

```markdown
# My Provider

## 安装

```bash
pip install openbb-my-provider
```

## 配置

需要设置 API 密钥：

```python
obb.user.credentials.my_provider_api_key = "your_key"
```

## 使用

```python
from openbb import obb

data = obb.equity.price.historical("AAPL", provider="my_provider")
```

## 支持的命令

- `equity.price.historical` - 股票历史价格
```

---

## 💡 实践任务

### 任务 1：理解 Fetcher 结构

阅读以下代码，回答问题：

```python
class SimpleFetcher(Fetcher[SimpleQueryParams, List[SimpleData]]):
    
    @staticmethod
    def transform_query(params: Dict[str, Any]) -> SimpleQueryParams:
        return SimpleQueryParams(**params)
    
    @staticmethod
    async def aextract_data(query, credentials, **kwargs) -> Dict:
        # 调用 API
        pass
    
    @staticmethod
    def transform_data(query, data, **kwargs) -> List[SimpleData]:
        # 转换数据
        pass
```

问题：
1. `transform_query` 的作用是什么？
2. 为什么 `aextract_data` 是异步方法？
3. `transform_data` 输出的是什么类型？

<details>
<summary>查看答案</summary>

1. `transform_query` 将用户传入的参数字典转换为类型安全的 QueryParams 对象，进行参数验证
2. 因为网络请求是 I/O 密集型操作，使用异步可以提高性能，允许并发处理多个请求
3. 输出是 `List[SimpleData]`，即标准化的数据对象列表
</details>

### 任务 2：实现一个简单的 Fetcher

实现一个从模拟数据返回股票价格的 Fetcher（不需要真实 API）：

```python
# 在这里实现

class MockStockFetcher(Fetcher):
    """模拟股票数据 Fetcher"""
    
    @staticmethod
    def transform_query(params):
        # 实现
        pass
    
    @staticmethod
    async def aextract_data(query, credentials, **kwargs):
        # 返回模拟数据
        pass
    
    @staticmethod
    def transform_data(query, data, **kwargs):
        # 转换数据
        pass
```

<details>
<summary>查看答案</summary>

```python
from datetime import date, timedelta
from typing import Any, Dict, List, Optional
import random

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.abstract.data import Data
from pydantic import Field


class MockQueryParams(QueryParams):
    symbol: str = Field(description="股票代码")
    days: int = Field(default=30, description="天数")


class MockStockData(Data):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int


class MockStockFetcher(Fetcher[MockQueryParams, List[MockStockData]]):
    
    @staticmethod
    def transform_query(params: Dict[str, Any]) -> MockQueryParams:
        return MockQueryParams(**params)
    
    @staticmethod
    async def aextract_data(
        query: MockQueryParams,
        credentials: Optional[Dict[str, str]],
        **kwargs: Any,
    ) -> Dict:
        # 生成模拟数据
        data = []
        base_price = 100.0
        
        for i in range(query.days):
            d = date.today() - timedelta(days=query.days - i)
            change = random.uniform(-5, 5)
            base_price += change
            
            data.append({
                "date": d.isoformat(),
                "open": round(base_price - random.uniform(0, 2), 2),
                "high": round(base_price + random.uniform(0, 3), 2),
                "low": round(base_price - random.uniform(0, 3), 2),
                "close": round(base_price, 2),
                "volume": random.randint(1000000, 10000000),
            })
        
        return {"symbol": query.symbol, "data": data}
    
    @staticmethod
    def transform_data(
        query: MockQueryParams,
        data: Dict,
        **kwargs: Any,
    ) -> List[MockStockData]:
        return [
            MockStockData(
                date=item["date"],
                open=item["open"],
                high=item["high"],
                low=item["low"],
                close=item["close"],
                volume=item["volume"],
            )
            for item in data["data"]
        ]


# 测试
import asyncio

async def test():
    params = {"symbol": "TEST", "days": 5}
    query = MockStockFetcher.transform_query(params)
    raw = await MockStockFetcher.aextract_data(query, None)
    result = MockStockFetcher.transform_data(query, raw)
    
    for item in result:
        print(f"{item.date}: {item.close}")

asyncio.run(test())
```
</details>

---

## 📚 知识检查

1. **Provider Extension 的主要组件有哪些？**
   <details>
   <summary>查看答案</summary>
   Provider 类、Fetcher 类、QueryParams 模型、Data 模型
   </details>

2. **TET 模式的三个步骤是什么？**
   <details>
   <summary>查看答案</summary>
   Transform Query（转换参数）、Extract Data（提取数据）、Transform Data（转换数据）
   </details>

3. **如何让 OpenBB 自动发现你的 Provider？**
   <details>
   <summary>查看答案</summary>
   在 pyproject.toml 中配置 `[tool.poetry.plugins."openbb_provider_extension"]`
   </details>

4. **为什么 `aextract_data` 是异步方法？**
   <details>
   <summary>查看答案</summary>
   因为网络请求是 I/O 密集型操作，异步可以提高性能和并发能力
   </details>

---

## ➡️ 下一课预告

在最后一课中，我们将通过一个完整的实战项目，综合运用所学知识：

- 构建股票组合分析工具
- 整合数据获取、处理、可视化
- 完成一个真实可用的应用

👉 [**第 9 课：实战项目案例 →**](./lesson-09-practical-project.md)

---

[← 上一课](./lesson-07-rest-api.md) | [返回目录](./README.md) | [下一课 →](./lesson-09-practical-project.md)
