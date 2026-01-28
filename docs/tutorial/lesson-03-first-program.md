# 第 3 课：第一个程序

**⏱ 课时**：25 分钟  
**🎯 学习目标**：编写第一个数据获取程序，理解输出结构  
**📚 难度**：⭐ 入门

---

## 📖 本课内容

- [3.1 Hello OpenBB](#31-hello-openbb)
- [3.2 理解输出结果](#32-理解输出结果)
- [3.3 探索更多命令](#33-探索更多命令)
- [3.4 获取帮助](#34-获取帮助)
- [💡 实践任务](#-实践任务)

---

## 3.1 Hello OpenBB

让我们编写第一个 OpenBB 程序！

### 完整代码

创建一个新文件 `hello_openbb.py`：

```python
# hello_openbb.py
# 我的第一个 OpenBB 程序

from openbb import obb

# 获取苹果公司最近的股票数据
data = obb.equity.price.historical(
    symbol="AAPL",
    provider="yfinance"
)

# 打印结果
print(data)
```

运行程序：

```bash
python hello_openbb.py
```

### 代码逐行解释

```python
from openbb import obb
```
- 从 `openbb` 包导入 `obb` 对象
- `obb` 是 OpenBB 的主入口，所有功能都通过它访问

```python
data = obb.equity.price.historical(
```
- `obb.equity` - 访问股票（equity）相关功能
- `.price` - 价格相关功能
- `.historical` - 获取历史数据
- 这种链式调用形成了清晰的命名空间

```python
    symbol="AAPL",
```
- `symbol` - 股票代码，这里是苹果公司（AAPL）

```python
    provider="yfinance"
```
- `provider` - 指定数据来源
- `yfinance` 是免费的 Yahoo Finance 数据

```python
print(data)
```
- 打印获取到的数据

### 命令结构图解

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenBB 命令结构                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   obb  .  equity  .  price  .  historical(...)              │
│    │        │         │           │                         │
│    │        │         │           └── 方法：获取历史数据     │
│    │        │         │                                     │
│    │        │         └────────── 子模块：价格相关          │
│    │        │                                               │
│    │        └──────────────────── 模块：股票相关            │
│    │                                                        │
│    └───────────────────────────── 主入口                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3.2 理解输出结果

### OBBject 是什么？

OpenBB 的所有命令都返回一个 `OBBject` 对象。这是一个标准化的输出容器：

```
┌─────────────────────────────────────────────────────────────┐
│                      OBBject 结构                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   OBBject                                                   │
│   │                                                         │
│   ├── id          唯一标识符（UUID）                        │
│   │                                                         │
│   ├── results     ⭐ 核心数据（列表形式）                    │
│   │                                                         │
│   ├── provider    数据来源（如 yfinance、fmp）              │
│   │                                                         │
│   ├── warnings    警告信息（如有）                          │
│   │                                                         │
│   ├── chart       图表对象（如已生成）                      │
│   │                                                         │
│   └── extra       额外元数据                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 访问数据的方法

```python
from openbb import obb

# 获取数据
data = obb.equity.price.historical("AAPL", provider="yfinance")

# 方法 1：直接访问 results（返回列表）
results = data.results
print(f"数据条数: {len(results)}")
print(f"第一条数据: {results[0]}")

# 方法 2：转换为 DataFrame（推荐）
df = data.to_dataframe()
print(df.head())

# 方法 3：转换为字典
dict_data = data.to_dict()

# 方法 4：转换为 JSON
json_data = data.to_json()
```

### 转换为 DataFrame

大多数情况下，你会希望用 Pandas DataFrame 来处理数据：

```python
from openbb import obb

# 获取数据
data = obb.equity.price.historical("AAPL", provider="yfinance")

# 转换为 DataFrame
df = data.to_dataframe()

# 查看前几行
print(df.head())

# 查看列名
print(df.columns.tolist())

# 基本统计
print(df.describe())
```

**输出示例**：

```
                  open        high         low       close     volume
date                                                                  
2024-01-02  187.150009  188.440002  183.889999  185.639999  82488700
2024-01-03  184.220001  185.880005  183.429993  184.250000  58414500
2024-01-04  182.149994  183.089996  180.880005  181.910004  71983600
2024-01-05  181.990005  182.759995  180.169998  181.179993  62303300
2024-01-08  182.089996  185.600006  181.500000  185.559998  59144500
```

### 查看元数据

```python
# 查看数据来源
print(f"数据来源: {data.provider}")

# 查看请求 ID
print(f"请求 ID: {data.id}")

# 查看额外信息
print(f"额外信息: {data.extra}")

# 查看是否有警告
if data.warnings:
    print(f"警告: {data.warnings}")
```

---

## 3.3 探索更多命令

OpenBB 提供了丰富的数据获取命令，按模块组织：

### 股票模块 (obb.equity)

```python
# 历史价格
obb.equity.price.historical("AAPL")

# 实时报价
obb.equity.price.quote("AAPL")

# 公司信息
obb.equity.profile("AAPL")

# 财务报表
obb.equity.fundamental.income("AAPL")          # 收入表
obb.equity.fundamental.balance("AAPL")         # 资产负债表
obb.equity.fundamental.cash("AAPL")            # 现金流量表
```

### 加密货币模块 (obb.crypto)

```python
# 比特币历史价格
obb.crypto.price.historical("BTC-USD")

# 搜索交易对
obb.crypto.search("ethereum")
```

### 经济数据模块 (obb.economy)

```python
# GDP 数据
obb.economy.gdp.nominal(country="united_states")

# 失业率
obb.economy.unemployment(country="united_states")

# CPI（消费者价格指数）
obb.economy.cpi(country="united_states")
```

### 新闻模块 (obb.news)

```python
# 公司新闻
obb.news.company(symbol="AAPL")

# 全球新闻
obb.news.world()
```

### ETF 模块 (obb.etf)

```python
# ETF 信息
obb.etf.info("SPY")

# ETF 持仓
obb.etf.holdings("SPY")
```

### 衍生品模块 (obb.derivatives)

```python
# 期权链
obb.derivatives.options.chains("AAPL")
```

### 模块总览图

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenBB 模块总览                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   obb                                                       │
│   │                                                         │
│   ├── equity          股票数据                              │
│   │   ├── price           价格                              │
│   │   ├── fundamental     基本面                            │
│   │   └── profile         公司信息                          │
│   │                                                         │
│   ├── crypto          加密货币                              │
│   │   ├── price           价格                              │
│   │   └── search          搜索                              │
│   │                                                         │
│   ├── economy         经济数据                              │
│   │   ├── gdp             GDP                               │
│   │   ├── cpi             CPI                               │
│   │   └── unemployment    失业率                            │
│   │                                                         │
│   ├── news            新闻                                  │
│   │   ├── company         公司新闻                          │
│   │   └── world           全球新闻                          │
│   │                                                         │
│   ├── etf             ETF                                   │
│   │   ├── info            信息                              │
│   │   └── holdings        持仓                              │
│   │                                                         │
│   ├── index           指数                                  │
│   │                                                         │
│   ├── currency        外汇                                  │
│   │                                                         │
│   ├── fixedincome     固定收益                              │
│   │                                                         │
│   └── derivatives     衍生品                                │
│       └── options         期权                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3.4 获取帮助

### 使用 help() 函数

Python 内置的 `help()` 函数可以查看任何命令的文档：

```python
from openbb import obb

# 查看 equity 模块的帮助
help(obb.equity)

# 查看 historical 命令的帮助
help(obb.equity.price.historical)
```

### 查看参数

```python
# 查看命令支持的参数
import inspect
sig = inspect.signature(obb.equity.price.historical)
print(sig)
```

### 使用 IDE 自动补全

在支持自动补全的 IDE（如 VS Code、PyCharm）中：

1. 输入 `obb.` 后按 Tab 或 Ctrl+Space
2. 会显示所有可用的模块
3. 继续输入 `obb.equity.` 会显示子模块
4. 这是探索 API 最方便的方式

### 常用参数说明

大多数数据获取命令支持以下常用参数：

| 参数 | 说明 | 示例 |
|------|------|------|
| `symbol` | 股票/资产代码 | `"AAPL"`, `"BTC-USD"` |
| `provider` | 数据来源 | `"yfinance"`, `"fmp"` |
| `start_date` | 开始日期 | `"2024-01-01"` |
| `end_date` | 结束日期 | `"2024-12-31"` |
| `interval` | 数据间隔 | `"1d"`, `"1h"`, `"1m"` |

### 示例：使用完整参数

```python
from openbb import obb

data = obb.equity.price.historical(
    symbol="AAPL",              # 股票代码
    provider="yfinance",        # 数据来源
    start_date="2024-01-01",    # 开始日期
    end_date="2024-06-30",      # 结束日期
    interval="1d"               # 日线数据
)

df = data.to_dataframe()
print(f"获取了 {len(df)} 条数据")
print(df.head())
```

---

## 💡 实践任务

完成以下任务，巩固你的学习：

### 任务 1：获取特斯拉股票数据

```python
# 补全代码，获取特斯拉（TSLA）最近一个月的数据
from openbb import obb

data = obb.equity.price.historical(
    symbol="____",           # 填入特斯拉代码
    provider="yfinance"
)

df = data.to_dataframe()
print(df.head())
```

<details>
<summary>查看答案</summary>

```python
from openbb import obb

data = obb.equity.price.historical(
    symbol="TSLA",
    provider="yfinance"
)

df = data.to_dataframe()
print(df.head())
```
</details>

### 任务 2：获取比特币价格

```python
# 获取比特币（BTC-USD）最近的价格数据
from openbb import obb

# 在这里写你的代码
```

<details>
<summary>查看答案</summary>

```python
from openbb import obb

data = obb.crypto.price.historical(
    symbol="BTC-USD",
    provider="yfinance"
)

df = data.to_dataframe()
print(df.head())
```
</details>

### 任务 3：探索 OBBject

```python
from openbb import obb

data = obb.equity.price.historical("MSFT", provider="yfinance")

# 任务：打印以下信息
# 1. 数据条数
# 2. 数据来源
# 3. 第一条数据的收盘价
```

<details>
<summary>查看答案</summary>

```python
from openbb import obb

data = obb.equity.price.historical("MSFT", provider="yfinance")

# 1. 数据条数
print(f"数据条数: {len(data.results)}")

# 2. 数据来源
print(f"数据来源: {data.provider}")

# 3. 第一条数据的收盘价
df = data.to_dataframe()
print(f"第一条收盘价: {df.iloc[0]['close']}")
```
</details>

---

## 📚 知识检查

1. **OpenBB 的主入口对象叫什么？**
   <details>
   <summary>查看答案</summary>
   obb（从 openbb 包导入）
   </details>

2. **所有 OpenBB 命令返回什么类型的对象？**
   <details>
   <summary>查看答案</summary>
   OBBject
   </details>

3. **如何将 OBBject 转换为 Pandas DataFrame？**
   <details>
   <summary>查看答案</summary>
   使用 .to_dataframe() 方法
   </details>

4. **OBBject 的 results 属性包含什么？**
   <details>
   <summary>查看答案</summary>
   核心数据，以列表形式存储
   </details>

---

## ➡️ 下一课预告

在下一课中，我们将深入学习 OpenBB 的核心概念：

- Provider（数据提供者）是什么
- Fetcher（数据获取器）如何工作
- Extension（扩展）有哪些类型

👉 [**第 4 课：核心概念理解 →**](./lesson-04-core-concepts.md)

---

[← 上一课](./lesson-02-installation.md) | [返回目录](./README.md) | [下一课 →](./lesson-04-core-concepts.md)
