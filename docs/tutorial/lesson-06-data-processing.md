# 第 6 课：数据处理与转换

**⏱ 课时**：30 分钟  
**🎯 学习目标**：掌握数据导出、可视化和 Pandas 操作  
**📚 难度**：⭐⭐ 基础

---

## 📖 本课内容

- [6.1 转换为 DataFrame](#61-转换为-dataframe)
- [6.2 导出数据](#62-导出数据)
- [6.3 数据可视化](#63-数据可视化)
- [6.4 与 Pandas 结合](#64-与-pandas-结合)
- [💡 实践任务](#-实践任务)

---

## 6.1 转换为 DataFrame

### 基础转换

```python
from openbb import obb

# 获取数据
data = obb.equity.price.historical("AAPL", provider="yfinance")

# 转换为 DataFrame
df = data.to_dataframe()

# 查看数据
print(df.head())
print(f"\n数据形状: {df.shape}")
print(f"列名: {df.columns.tolist()}")
```

### 设置索引

```python
# 默认情况下，日期可能是列或索引
# 可以明确指定索引列
df = data.to_dataframe(index="date")

# 查看索引
print(f"索引类型: {type(df.index)}")
print(f"索引范围: {df.index.min()} 到 {df.index.max()}")
```

### 查看数据信息

```python
# 查看数据类型
print(df.dtypes)

# 查看基本统计
print(df.describe())

# 查看数据信息
print(df.info())

# 检查缺失值
print(df.isnull().sum())
```

### 其他转换方法

```python
# 转换为字典
dict_data = data.to_dict()
print(type(dict_data))

# 转换为 JSON 字符串
json_str = data.to_json()
print(json_str[:200])  # 打印前 200 字符

# 转换为 Polars DataFrame（如果安装了 polars）
# pl_df = data.to_polars()
```

---

## 6.2 导出数据

将获取的数据保存到文件中。

### 导出为 CSV

```python
from openbb import obb

# 获取数据
data = obb.equity.price.historical("AAPL", provider="yfinance")
df = data.to_dataframe()

# 导出为 CSV
df.to_csv("aapl_data.csv")
print("数据已保存到 aapl_data.csv")

# 不包含索引
df.to_csv("aapl_data_no_index.csv", index=False)

# 指定编码（处理中文）
df.to_csv("aapl_data_utf8.csv", encoding="utf-8-sig")
```

### 导出为 Excel

```python
# 需要安装 openpyxl: pip install openpyxl

# 基础导出
df.to_excel("aapl_data.xlsx", index=False)

# 导出多个工作表
with pd.ExcelWriter("stock_data.xlsx") as writer:
    # 获取多只股票数据
    for symbol in ["AAPL", "MSFT", "GOOGL"]:
        data = obb.equity.price.historical(symbol, provider="yfinance")
        df = data.to_dataframe()
        df.to_excel(writer, sheet_name=symbol, index=False)

print("数据已保存到 stock_data.xlsx")
```

### 导出为 JSON

```python
# 使用 OBBject 的方法
json_str = data.to_json()
with open("aapl_data.json", "w") as f:
    f.write(json_str)

# 或使用 DataFrame 的方法
df.to_json("aapl_df.json", orient="records", date_format="iso")
```

### 导出为 Parquet（高效存储）

```python
# Parquet 格式适合大数据集
# 需要安装: pip install pyarrow

df.to_parquet("aapl_data.parquet")
print("数据已保存为 Parquet 格式")

# 读取 Parquet
import pandas as pd
df_loaded = pd.read_parquet("aapl_data.parquet")
```

### 导出格式对比

| 格式 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| **CSV** | 通用、可读 | 无类型信息 | 数据交换 |
| **Excel** | 可视化好 | 文件较大 | 报告分享 |
| **JSON** | 结构化 | 冗余较多 | API 传输 |
| **Parquet** | 高效压缩 | 不可读 | 大数据存储 |

---

## 6.3 数据可视化

### 使用 Matplotlib（基础）

```python
import matplotlib.pyplot as plt
from openbb import obb

# 获取数据
data = obb.equity.price.historical("AAPL", provider="yfinance")
df = data.to_dataframe()

# 绘制收盘价走势
plt.figure(figsize=(12, 6))
plt.plot(df.index, df['close'], label='收盘价')
plt.title('AAPL 股价走势')
plt.xlabel('日期')
plt.ylabel('价格 ($)')
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('aapl_price.png')
plt.show()
```

### 使用 Pandas 内置绑图

```python
# 简单折线图
df['close'].plot(figsize=(12, 6), title='AAPL 收盘价')
plt.savefig('aapl_close.png')
plt.show()

# K 线图（OHLC）
df[['open', 'high', 'low', 'close']].plot(
    figsize=(12, 6),
    title='AAPL OHLC'
)
plt.savefig('aapl_ohlc.png')
plt.show()

# 成交量柱状图
df['volume'].plot(kind='bar', figsize=(12, 4), title='成交量')
plt.show()
```

### 使用 OpenBB Charting（推荐）

如果安装了 `openbb-charting` 扩展：

```python
from openbb import obb

# 获取数据
data = obb.equity.price.historical("AAPL", provider="yfinance")

# 直接显示图表
data.show()  # 会打开交互式图表

# 如果在 Jupyter Notebook 中
# 图表会直接显示在单元格输出中
```

### 安装 Charting 扩展

```bash
pip install openbb-charting
```

### 多图对比

```python
import matplotlib.pyplot as plt
from openbb import obb

symbols = ["AAPL", "MSFT", "GOOGL"]
fig, axes = plt.subplots(len(symbols), 1, figsize=(12, 10))

for i, symbol in enumerate(symbols):
    data = obb.equity.price.historical(symbol, provider="yfinance")
    df = data.to_dataframe()
    
    axes[i].plot(df.index, df['close'])
    axes[i].set_title(f'{symbol} 股价')
    axes[i].set_ylabel('价格 ($)')
    axes[i].grid(True)

plt.tight_layout()
plt.savefig('comparison.png')
plt.show()
```

---

## 6.4 与 Pandas 结合

### 数据清洗

```python
from openbb import obb
import pandas as pd

# 获取数据
data = obb.equity.price.historical("AAPL", provider="yfinance")
df = data.to_dataframe()

# 处理缺失值
print(f"缺失值统计:\n{df.isnull().sum()}")

# 填充缺失值
df_filled = df.fillna(method='ffill')  # 前向填充

# 删除缺失值
df_dropped = df.dropna()

# 重置索引
df_reset = df.reset_index()
```

### 计算技术指标

```python
# 计算移动平均线
df['MA5'] = df['close'].rolling(window=5).mean()    # 5 日均线
df['MA20'] = df['close'].rolling(window=20).mean()  # 20 日均线
df['MA60'] = df['close'].rolling(window=60).mean()  # 60 日均线

# 计算日收益率
df['daily_return'] = df['close'].pct_change()

# 计算累计收益率
df['cumulative_return'] = (1 + df['daily_return']).cumprod() - 1

# 计算波动率（20 日滚动标准差）
df['volatility'] = df['daily_return'].rolling(window=20).std()

print(df[['close', 'MA5', 'MA20', 'daily_return']].tail(10))
```

### 绘制带均线的图表

```python
import matplotlib.pyplot as plt

plt.figure(figsize=(14, 7))
plt.plot(df.index, df['close'], label='收盘价', alpha=0.8)
plt.plot(df.index, df['MA5'], label='MA5', linestyle='--')
plt.plot(df.index, df['MA20'], label='MA20', linestyle='--')
plt.plot(df.index, df['MA60'], label='MA60', linestyle='--')

plt.title('AAPL 股价与移动平均线')
plt.xlabel('日期')
plt.ylabel('价格 ($)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('aapl_with_ma.png')
plt.show()
```

### 数据筛选

```python
# 筛选特定日期范围
df_2024 = df['2024-01-01':'2024-06-30']

# 筛选收盘价大于某值
df_high = df[df['close'] > 180]

# 筛选成交量异常高的日期
volume_mean = df['volume'].mean()
df_high_volume = df[df['volume'] > volume_mean * 2]

# 组合条件筛选
df_filtered = df[(df['close'] > 180) & (df['volume'] > volume_mean)]
```

### 数据聚合

```python
# 按月聚合
monthly = df.resample('M').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum'
})
print("月度数据:")
print(monthly.tail())

# 按周聚合
weekly = df.resample('W').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum'
})
print("\n周度数据:")
print(weekly.tail())
```

### 合并多只股票数据

```python
from openbb import obb
import pandas as pd

symbols = ["AAPL", "MSFT", "GOOGL"]
dfs = {}

for symbol in symbols:
    data = obb.equity.price.historical(symbol, provider="yfinance")
    df = data.to_dataframe()
    dfs[symbol] = df['close'].rename(symbol)

# 合并为一个 DataFrame
combined = pd.concat(dfs.values(), axis=1)
print("合并后的数据:")
print(combined.tail())

# 计算相关性
correlation = combined.corr()
print("\n相关性矩阵:")
print(correlation)
```

### 绘制相关性热力图

```python
import matplotlib.pyplot as plt
import seaborn as sns

plt.figure(figsize=(8, 6))
sns.heatmap(correlation, annot=True, cmap='coolwarm', center=0)
plt.title('股票价格相关性')
plt.tight_layout()
plt.savefig('correlation_heatmap.png')
plt.show()
```

---

## 💡 实践任务

### 任务 1：数据导出练习

获取特斯拉股票数据并导出为 CSV 和 Excel：

```python
from openbb import obb

# 获取特斯拉数据
data = obb.equity.price.historical("TSLA", provider="yfinance")
df = data.to_dataframe()

# 任务：
# 1. 导出为 CSV 文件
# 2. 导出为 Excel 文件
# 3. 验证文件是否正确保存
```

<details>
<summary>查看答案</summary>

```python
from openbb import obb

# 获取特斯拉数据
data = obb.equity.price.historical("TSLA", provider="yfinance")
df = data.to_dataframe()

# 1. 导出为 CSV
df.to_csv("tsla_data.csv", index=True)
print("CSV 已保存")

# 2. 导出为 Excel
df.to_excel("tsla_data.xlsx", index=True)
print("Excel 已保存")

# 3. 验证
import pandas as pd
csv_df = pd.read_csv("tsla_data.csv", index_col=0)
print(f"CSV 文件包含 {len(csv_df)} 行数据")
```
</details>

### 任务 2：技术指标计算

计算苹果股票的移动平均线和 RSI：

```python
from openbb import obb
import pandas as pd

# 获取数据
data = obb.equity.price.historical("AAPL", provider="yfinance")
df = data.to_dataframe()

# 任务：
# 1. 计算 5 日、10 日、20 日移动平均线
# 2. 计算日收益率
# 3. 绘制收盘价和均线图
```

<details>
<summary>查看答案</summary>

```python
from openbb import obb
import pandas as pd
import matplotlib.pyplot as plt

# 获取数据
data = obb.equity.price.historical("AAPL", provider="yfinance")
df = data.to_dataframe()

# 1. 计算移动平均线
df['MA5'] = df['close'].rolling(window=5).mean()
df['MA10'] = df['close'].rolling(window=10).mean()
df['MA20'] = df['close'].rolling(window=20).mean()

# 2. 计算日收益率
df['daily_return'] = df['close'].pct_change() * 100

# 3. 绘制图表
plt.figure(figsize=(14, 7))
plt.plot(df.index, df['close'], label='收盘价', linewidth=2)
plt.plot(df.index, df['MA5'], label='MA5', linestyle='--')
plt.plot(df.index, df['MA10'], label='MA10', linestyle='--')
plt.plot(df.index, df['MA20'], label='MA20', linestyle='--')

plt.title('AAPL 股价与移动平均线')
plt.xlabel('日期')
plt.ylabel('价格 ($)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

print(df[['close', 'MA5', 'MA10', 'MA20', 'daily_return']].tail())
```
</details>

### 任务 3：多股票对比分析

比较 AAPL、MSFT、GOOGL 的表现：

```python
from openbb import obb
import pandas as pd

symbols = ["AAPL", "MSFT", "GOOGL"]

# 任务：
# 1. 获取三只股票的数据
# 2. 合并收盘价到一个 DataFrame
# 3. 计算并打印相关性矩阵
# 4. 计算各股票的累计收益率
```

<details>
<summary>查看答案</summary>

```python
from openbb import obb
import pandas as pd
import matplotlib.pyplot as plt

symbols = ["AAPL", "MSFT", "GOOGL"]
close_prices = {}

# 1. 获取数据
for symbol in symbols:
    data = obb.equity.price.historical(symbol, provider="yfinance")
    df = data.to_dataframe()
    close_prices[symbol] = df['close']

# 2. 合并数据
combined = pd.DataFrame(close_prices)
print("合并后的收盘价:")
print(combined.tail())

# 3. 相关性矩阵
correlation = combined.corr()
print("\n相关性矩阵:")
print(correlation)

# 4. 累计收益率
returns = combined.pct_change()
cumulative_returns = (1 + returns).cumprod() - 1

print("\n最新累计收益率:")
print(cumulative_returns.iloc[-1])

# 绘制累计收益率图
plt.figure(figsize=(12, 6))
for col in cumulative_returns.columns:
    plt.plot(cumulative_returns.index, cumulative_returns[col], label=col)
plt.title('累计收益率对比')
plt.xlabel('日期')
plt.ylabel('累计收益率')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
```
</details>

---

## 📚 知识检查

1. **如何将 OBBject 转换为 DataFrame？**
   <details>
   <summary>查看答案</summary>
   使用 `data.to_dataframe()` 方法
   </details>

2. **导出数据有哪些常用格式？**
   <details>
   <summary>查看答案</summary>
   CSV、Excel、JSON、Parquet
   </details>

3. **如何计算 20 日移动平均线？**
   <details>
   <summary>查看答案</summary>
   `df['MA20'] = df['close'].rolling(window=20).mean()`
   </details>

4. **如何将日数据聚合为月数据？**
   <details>
   <summary>查看答案</summary>
   使用 `df.resample('M').agg({...})`
   </details>

---

## ➡️ 下一课预告

在下一课中，我们将学习如何使用 REST API：

- 启动 OpenBB API 服务
- 探索 API 端点
- 使用不同方式调用 API

👉 [**第 7 课：REST API 使用 →**](./lesson-07-rest-api.md)

---

[← 上一课](./lesson-05-data-fetching.md) | [返回目录](./README.md) | [下一课 →](./lesson-07-rest-api.md)
