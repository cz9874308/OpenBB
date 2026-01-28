# 第 5 课：数据获取实战

**⏱ 课时**：35 分钟  
**🎯 学习目标**：掌握获取股票、加密货币、经济数据的方法  
**📚 难度**：⭐⭐ 基础

---

## 📖 本课内容

- [5.1 股票数据](#51-股票数据)
- [5.2 加密货币数据](#52-加密货币数据)
- [5.3 经济数据](#53-经济数据)
- [5.4 切换数据源](#54-切换数据源)
- [5.5 处理错误](#55-处理错误)
- [💡 实践任务](#-实践任务)

---

## 5.1 股票数据

股票数据是 OpenBB 最常用的功能之一。让我们学习如何获取各种类型的股票数据。

### 历史价格

```python
from openbb import obb

# 基础用法：获取默认时间范围的历史价格
data = obb.equity.price.historical("AAPL", provider="yfinance")
df = data.to_dataframe()
print(df.head())
```

**输出示例**：

```
                  open        high         low       close     volume
date                                                                  
2024-01-02  187.150009  188.440002  183.889999  185.639999  82488700
2024-01-03  184.220001  185.880005  183.429993  184.250000  58414500
...
```

### 指定时间范围

```python
# 获取指定日期范围的数据
data = obb.equity.price.historical(
    symbol="AAPL",
    provider="yfinance",
    start_date="2024-01-01",
    end_date="2024-06-30"
)

df = data.to_dataframe()
print(f"获取了 {len(df)} 条数据")
print(f"时间范围: {df.index.min()} 到 {df.index.max()}")
```

### 不同时间间隔

```python
# 日线数据（默认）
daily = obb.equity.price.historical("AAPL", interval="1d")

# 周线数据
weekly = obb.equity.price.historical("AAPL", interval="1wk")

# 月线数据
monthly = obb.equity.price.historical("AAPL", interval="1mo")

# 小时数据（部分 provider 支持）
hourly = obb.equity.price.historical("AAPL", interval="1h")
```

**常用 interval 值**：

| 值 | 说明 |
|---|------|
| `1m` | 1 分钟 |
| `5m` | 5 分钟 |
| `15m` | 15 分钟 |
| `1h` | 1 小时 |
| `1d` | 1 天 |
| `1wk` | 1 周 |
| `1mo` | 1 月 |

### 实时报价

```python
# 获取实时/最新报价
quote = obb.equity.price.quote("AAPL", provider="yfinance")
df = quote.to_dataframe()
print(df)
```

**包含的信息**：
- 当前价格
- 开盘价、最高价、最低价
- 成交量
- 52 周高低点
- 市值等

### 多只股票

```python
# 同时获取多只股票的数据
symbols = ["AAPL", "MSFT", "GOOGL"]

for symbol in symbols:
    data = obb.equity.price.historical(symbol, provider="yfinance")
    df = data.to_dataframe()
    print(f"\n{symbol} 最近 5 天:")
    print(df.tail())
```

### 公司信息

```python
# 获取公司基本信息
profile = obb.equity.profile("AAPL", provider="yfinance")
df = profile.to_dataframe()
print(df.T)  # 转置以便阅读
```

### 财务报表

```python
# 收入表
income = obb.equity.fundamental.income("AAPL", provider="yfinance")
print(income.to_dataframe())

# 资产负债表
balance = obb.equity.fundamental.balance("AAPL", provider="yfinance")
print(balance.to_dataframe())

# 现金流量表
cash = obb.equity.fundamental.cash("AAPL", provider="yfinance")
print(cash.to_dataframe())
```

---

## 5.2 加密货币数据

OpenBB 也支持获取加密货币数据。

### 历史价格

```python
from openbb import obb

# 获取比特币历史价格
btc = obb.crypto.price.historical("BTC-USD", provider="yfinance")
df = btc.to_dataframe()
print(df.head())
```

### 常用加密货币代码

| 代码 | 加密货币 |
|------|---------|
| `BTC-USD` | 比特币 |
| `ETH-USD` | 以太坊 |
| `BNB-USD` | 币安币 |
| `SOL-USD` | Solana |
| `XRP-USD` | 瑞波币 |
| `ADA-USD` | Cardano |
| `DOGE-USD` | 狗狗币 |

### 指定时间范围

```python
# 获取以太坊 2024 年数据
eth = obb.crypto.price.historical(
    symbol="ETH-USD",
    provider="yfinance",
    start_date="2024-01-01",
    end_date="2024-12-31"
)

df = eth.to_dataframe()
print(f"数据条数: {len(df)}")
print(df.describe())
```

### 搜索加密货币

```python
# 搜索加密货币（部分 provider 支持）
# search = obb.crypto.search("bitcoin")
```

---

## 5.3 经济数据

经济数据对于宏观分析非常重要。

### GDP 数据

```python
from openbb import obb

# 获取美国 GDP 数据（需要 FRED provider）
# 注意：FRED 需要 API 密钥
try:
    gdp = obb.economy.gdp.nominal(
        country="united_states",
        provider="oecd"  # 使用 OECD 不需要密钥
    )
    df = gdp.to_dataframe()
    print(df.tail())
except Exception as e:
    print(f"获取 GDP 数据失败: {e}")
```

### CPI（消费者价格指数）

```python
# 获取 CPI 数据
try:
    cpi = obb.economy.cpi(
        country="united_states",
        provider="oecd"
    )
    df = cpi.to_dataframe()
    print(df.tail())
except Exception as e:
    print(f"获取 CPI 数据失败: {e}")
```

### 失业率

```python
# 获取失业率数据
try:
    unemployment = obb.economy.unemployment(
        country="united_states",
        provider="oecd"
    )
    df = unemployment.to_dataframe()
    print(df.tail())
except Exception as e:
    print(f"获取失业率数据失败: {e}")
```

### 经济日历

```python
# 获取经济事件日历
try:
    calendar = obb.economy.calendar(provider="nasdaq")
    df = calendar.to_dataframe()
    print(df.head(10))
except Exception as e:
    print(f"获取经济日历失败: {e}")
```

---

## 5.4 切换数据源

同一类型的数据可以从不同的数据源获取。

### 比较不同数据源

```python
from openbb import obb

symbol = "AAPL"

# 使用 yfinance
data_yf = obb.equity.price.historical(symbol, provider="yfinance")
df_yf = data_yf.to_dataframe()

print("=== yfinance 数据 ===")
print(df_yf.tail(3))
print(f"列名: {df_yf.columns.tolist()}")

# 如果有 FMP API 密钥
# data_fmp = obb.equity.price.historical(symbol, provider="fmp")
# df_fmp = data_fmp.to_dataframe()
# print("\n=== FMP 数据 ===")
# print(df_fmp.tail(3))
```

### 为什么要切换数据源？

| 原因 | 说明 |
|------|------|
| **数据覆盖** | 不同源覆盖的股票/市场不同 |
| **数据质量** | 免费源可能有延迟或数据缺失 |
| **额外字段** | 不同源可能提供额外的数据字段 |
| **速率限制** | 避免单一数据源的请求限制 |
| **备份** | 主数据源不可用时切换到备用 |

### 设置默认 Provider

```python
from openbb import obb

# 查看当前默认设置
print(obb.user.preferences)

# 可以在配置文件中设置默认 provider
# 或在每次调用时指定
```

---

## 5.5 处理错误

在实际使用中，你会遇到各种错误。学习如何正确处理它们。

### 常见错误类型

```
┌─────────────────────────────────────────────────────────────┐
│                    常见错误及处理                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   1. 无效的股票代码                                          │
│      错误: Empty results                                    │
│      处理: 检查代码是否正确                                  │
│                                                             │
│   2. 网络超时                                               │
│      错误: ConnectionTimeout                                │
│      处理: 重试或检查网络                                    │
│                                                             │
│   3. API 密钥无效                                           │
│      错误: AuthenticationError                              │
│      处理: 检查密钥配置                                      │
│                                                             │
│   4. 请求频率过高                                           │
│      错误: RateLimitError                                   │
│      处理: 添加延迟或减少请求                                │
│                                                             │
│   5. 数据源不可用                                           │
│      错误: ProviderError                                    │
│      处理: 切换到其他数据源                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 基础错误处理

```python
from openbb import obb

def safe_get_historical(symbol, provider="yfinance"):
    """安全地获取历史数据"""
    try:
        data = obb.equity.price.historical(symbol, provider=provider)
        
        # 检查是否有数据
        if not data.results:
            print(f"警告: {symbol} 没有返回数据")
            return None
            
        return data.to_dataframe()
        
    except Exception as e:
        print(f"获取 {symbol} 数据时出错: {e}")
        return None

# 使用示例
df = safe_get_historical("AAPL")
if df is not None:
    print(df.head())
```

### 带重试的错误处理

```python
import time
from openbb import obb

def get_data_with_retry(symbol, max_retries=3, delay=1):
    """带重试机制的数据获取"""
    for attempt in range(max_retries):
        try:
            data = obb.equity.price.historical(symbol, provider="yfinance")
            return data.to_dataframe()
            
        except Exception as e:
            print(f"第 {attempt + 1} 次尝试失败: {e}")
            
            if attempt < max_retries - 1:
                print(f"等待 {delay} 秒后重试...")
                time.sleep(delay)
                delay *= 2  # 指数退避
            else:
                print("所有重试都失败了")
                return None

# 使用示例
df = get_data_with_retry("AAPL")
```

### 数据源回退

```python
from openbb import obb

def get_data_with_fallback(symbol, providers=["yfinance", "fmp"]):
    """尝试多个数据源"""
    for provider in providers:
        try:
            print(f"尝试使用 {provider}...")
            data = obb.equity.price.historical(symbol, provider=provider)
            
            if data.results:
                print(f"成功从 {provider} 获取数据")
                return data.to_dataframe()
                
        except Exception as e:
            print(f"{provider} 失败: {e}")
            continue
    
    print("所有数据源都失败了")
    return None

# 使用示例
df = get_data_with_fallback("AAPL")
```

### 检查警告信息

```python
from openbb import obb

data = obb.equity.price.historical("AAPL", provider="yfinance")

# 检查是否有警告
if data.warnings:
    for warning in data.warnings:
        print(f"警告: {warning}")

# 数据可能不完整但仍然可用
df = data.to_dataframe()
print(df.head())
```

---

## 💡 实践任务

### 任务 1：获取科技股数据

获取 FAANG 股票（Facebook/Meta、Apple、Amazon、Netflix、Google）的最近数据：

```python
from openbb import obb

faang = ["META", "AAPL", "AMZN", "NFLX", "GOOGL"]

# 在这里编写代码
for symbol in faang:
    # 获取数据并打印最新收盘价
    pass
```

<details>
<summary>查看答案</summary>

```python
from openbb import obb

faang = ["META", "AAPL", "AMZN", "NFLX", "GOOGL"]

for symbol in faang:
    try:
        data = obb.equity.price.historical(symbol, provider="yfinance")
        df = data.to_dataframe()
        latest = df.iloc[-1]
        print(f"{symbol}: 收盘价 ${latest['close']:.2f}")
    except Exception as e:
        print(f"{symbol}: 获取失败 - {e}")
```
</details>

### 任务 2：获取加密货币数据

获取比特币和以太坊 2024 年的月度数据：

```python
from openbb import obb

cryptos = ["BTC-USD", "ETH-USD"]

# 在这里编写代码
```

<details>
<summary>查看答案</summary>

```python
from openbb import obb

cryptos = ["BTC-USD", "ETH-USD"]

for crypto in cryptos:
    try:
        data = obb.crypto.price.historical(
            symbol=crypto,
            provider="yfinance",
            start_date="2024-01-01",
            end_date="2024-12-31",
            interval="1mo"
        )
        df = data.to_dataframe()
        print(f"\n{crypto} 月度数据:")
        print(df[['open', 'high', 'low', 'close']])
    except Exception as e:
        print(f"{crypto}: 获取失败 - {e}")
```
</details>

### 任务 3：实现带错误处理的数据获取

编写一个函数，可以安全地获取任意股票的数据：

```python
def get_stock_data(symbol, start_date=None, end_date=None):
    """
    安全地获取股票数据
    
    参数:
        symbol: 股票代码
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
    
    返回:
        DataFrame 或 None（如果失败）
    """
    # 在这里实现
    pass

# 测试
df = get_stock_data("AAPL", "2024-01-01", "2024-06-30")
if df is not None:
    print(df.head())
```

<details>
<summary>查看答案</summary>

```python
from openbb import obb

def get_stock_data(symbol, start_date=None, end_date=None):
    """
    安全地获取股票数据
    """
    try:
        params = {"symbol": symbol, "provider": "yfinance"}
        
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
            
        data = obb.equity.price.historical(**params)
        
        if not data.results:
            print(f"警告: {symbol} 没有返回数据")
            return None
            
        if data.warnings:
            for w in data.warnings:
                print(f"警告: {w}")
                
        return data.to_dataframe()
        
    except Exception as e:
        print(f"错误: 获取 {symbol} 数据失败 - {e}")
        return None

# 测试
df = get_stock_data("AAPL", "2024-01-01", "2024-06-30")
if df is not None:
    print(f"获取了 {len(df)} 条数据")
    print(df.head())
```
</details>

---

## 📚 知识检查

1. **如何指定数据的时间范围？**
   <details>
   <summary>查看答案</summary>
   使用 start_date 和 end_date 参数，格式为 "YYYY-MM-DD"
   </details>

2. **interval 参数的作用是什么？**
   <details>
   <summary>查看答案</summary>
   指定数据的时间间隔，如 "1d"（日）、"1wk"（周）、"1mo"（月）
   </details>

3. **如何获取公司的财务报表？**
   <details>
   <summary>查看答案</summary>
   使用 obb.equity.fundamental 下的方法：income（收入表）、balance（资产负债表）、cash（现金流量表）
   </details>

4. **获取数据失败时应该怎么处理？**
   <details>
   <summary>查看答案</summary>
   使用 try-except 捕获异常，可以实现重试机制或数据源回退
   </details>

---

## ➡️ 下一课预告

在下一课中，我们将学习如何处理和转换获取到的数据：

- 数据导出（CSV、Excel、JSON）
- 数据可视化
- 与 Pandas 深度结合

👉 [**第 6 课：数据处理与转换 →**](./lesson-06-data-processing.md)

---

[← 上一课](./lesson-04-core-concepts.md) | [返回目录](./README.md) | [下一课 →](./lesson-06-data-processing.md)
