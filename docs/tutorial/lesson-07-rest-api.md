# 第 7 课：REST API 使用

**⏱ 课时**：40 分钟  
**🎯 学习目标**：搭建和调用 OpenBB REST API 服务  
**📚 难度**：⭐⭐⭐ 进阶

---

## 📖 本课内容

- [7.1 启动 API 服务](#71-启动-api-服务)
- [7.2 API 端点探索](#72-api-端点探索)
- [7.3 调用 API](#73-调用-api)
- [7.4 认证与安全](#74-认证与安全)
- [7.5 集成到应用](#75-集成到应用)
- [💡 实践任务](#-实践任务)

---

## 7.1 启动 API 服务

OpenBB 提供了一个基于 FastAPI 的 REST API 服务，让你可以通过 HTTP 请求获取数据。

### 安装 API 扩展

```bash
pip install openbb-platform-api
```

### 启动服务

#### 方式一：命令行启动

```bash
# 基础启动（默认端口 6900）
openbb-api

# 指定端口
openbb-api --port 8000

# 指定主机（允许外部访问）
openbb-api --host 0.0.0.0 --port 8000
```

#### 方式二：Python 代码启动

```python
from openbb_platform_api.main import run

# 启动 API 服务
run(host="127.0.0.1", port=6900)
```

### 启动成功提示

```
┌─────────────────────────────────────────────────────────────┐
│                    API 启动成功                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   INFO:     Started server process [12345]                  │
│   INFO:     Waiting for application startup.                │
│   INFO:     Application startup complete.                   │
│   INFO:     Uvicorn running on http://127.0.0.1:6900        │
│                                                             │
│   访问以下地址查看 API 文档：                                 │
│   - Swagger UI: http://127.0.0.1:6900/docs                  │
│   - ReDoc: http://127.0.0.1:6900/redoc                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 常用启动参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--host` | 监听地址 | `127.0.0.1` |
| `--port` | 监听端口 | `6900` |
| `--reload` | 开发模式（自动重载） | `False` |
| `--workers` | 工作进程数 | `1` |

---

## 7.2 API 端点探索

### 访问 Swagger 文档

启动服务后，打开浏览器访问：

```
http://127.0.0.1:6900/docs
```

你会看到一个交互式的 API 文档界面。

### API 端点结构

```
┌─────────────────────────────────────────────────────────────┐
│                    API 端点结构                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   /api/v1                                                   │
│   │                                                         │
│   ├── /equity                    股票数据                   │
│   │   ├── /price                                            │
│   │   │   ├── GET /historical    历史价格                   │
│   │   │   └── GET /quote         实时报价                   │
│   │   └── /fundamental                                      │
│   │       ├── GET /income        收入表                     │
│   │       └── GET /balance       资产负债表                 │
│   │                                                         │
│   ├── /crypto                    加密货币                   │
│   │   └── /price                                            │
│   │       └── GET /historical    历史价格                   │
│   │                                                         │
│   ├── /economy                   经济数据                   │
│   │   ├── GET /gdp               GDP                        │
│   │   └── GET /cpi               CPI                        │
│   │                                                         │
│   ├── /news                      新闻                       │
│   │   └── GET /company           公司新闻                   │
│   │                                                         │
│   └── /etf                       ETF                        │
│       └── GET /info              ETF 信息                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 端点命名规则

Python SDK 命令和 API 端点的对应关系：

| Python SDK | REST API 端点 |
|------------|---------------|
| `obb.equity.price.historical()` | `GET /api/v1/equity/price/historical` |
| `obb.crypto.price.historical()` | `GET /api/v1/crypto/price/historical` |
| `obb.economy.gdp.nominal()` | `GET /api/v1/economy/gdp/nominal` |
| `obb.news.company()` | `GET /api/v1/news/company` |

---

## 7.3 调用 API

### 使用 curl

```bash
# 获取苹果股票历史价格
curl "http://127.0.0.1:6900/api/v1/equity/price/historical?symbol=AAPL&provider=yfinance"

# 格式化输出
curl -s "http://127.0.0.1:6900/api/v1/equity/price/historical?symbol=AAPL&provider=yfinance" | python -m json.tool

# 指定日期范围
curl "http://127.0.0.1:6900/api/v1/equity/price/historical?symbol=AAPL&provider=yfinance&start_date=2024-01-01&end_date=2024-06-30"
```

### 使用 Python requests

```python
import requests
import json

# API 基础 URL
BASE_URL = "http://127.0.0.1:6900/api/v1"

# 获取股票历史价格
def get_stock_historical(symbol, provider="yfinance", start_date=None, end_date=None):
    """获取股票历史数据"""
    url = f"{BASE_URL}/equity/price/historical"
    
    params = {
        "symbol": symbol,
        "provider": provider
    }
    
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"错误: {response.status_code}")
        print(response.text)
        return None

# 使用示例
data = get_stock_historical("AAPL", start_date="2024-01-01")
if data:
    print(f"获取了 {len(data['results'])} 条数据")
    print(json.dumps(data['results'][0], indent=2))
```

### 使用 JavaScript fetch

```javascript
// 获取股票数据
async function getStockData(symbol, provider = 'yfinance') {
    const baseUrl = 'http://127.0.0.1:6900/api/v1';
    const url = `${baseUrl}/equity/price/historical?symbol=${symbol}&provider=${provider}`;
    
    try {
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log(`获取了 ${data.results.length} 条数据`);
        return data;
        
    } catch (error) {
        console.error('获取数据失败:', error);
        return null;
    }
}

// 使用示例
getStockData('AAPL').then(data => {
    if (data) {
        console.log('第一条数据:', data.results[0]);
    }
});
```

### API 响应格式

```json
{
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "results": [
        {
            "date": "2024-01-02",
            "open": 187.15,
            "high": 188.44,
            "low": 183.89,
            "close": 185.64,
            "volume": 82488700
        },
        ...
    ],
    "provider": "yfinance",
    "warnings": null,
    "chart": null,
    "extra": {
        "metadata": {
            "symbol": "AAPL",
            "arguments": {...}
        }
    }
}
```

---

## 7.4 认证与安全

### 配置 API 密钥认证

在生产环境中，你可能需要保护 API：

```python
# 在启动时配置
from openbb_platform_api.main import run

run(
    host="0.0.0.0",
    port=8000,
    # 可以通过环境变量配置认证
)
```

### 环境变量配置

```bash
# 设置 API 认证（如果需要）
export OPENBB_API_AUTH=true
export OPENBB_API_USERNAME=admin
export OPENBB_API_PASSWORD=secret_password
```

### 使用认证调用

```python
import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "http://127.0.0.1:6900/api/v1"

# 带认证的请求
response = requests.get(
    f"{BASE_URL}/equity/price/historical",
    params={"symbol": "AAPL", "provider": "yfinance"},
    auth=HTTPBasicAuth("admin", "secret_password")
)
```

### CORS 配置

如果需要从浏览器前端调用 API：

```python
# API 默认配置了 CORS 允许所有来源
# 生产环境建议限制允许的来源

# 通过环境变量配置
# OPENBB_API_CORS_ORIGINS=["http://localhost:3000", "https://myapp.com"]
```

---

## 7.5 集成到应用

### 集成到 Web 应用

#### React 示例

```jsx
// StockChart.jsx
import React, { useState, useEffect } from 'react';

function StockChart({ symbol }) {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
        async function fetchData() {
            try {
                const response = await fetch(
                    `http://localhost:6900/api/v1/equity/price/historical?symbol=${symbol}&provider=yfinance`
                );
                const result = await response.json();
                setData(result.results);
            } catch (error) {
                console.error('获取数据失败:', error);
            } finally {
                setLoading(false);
            }
        }
        
        fetchData();
    }, [symbol]);
    
    if (loading) return <div>加载中...</div>;
    
    return (
        <div>
            <h2>{symbol} 股票数据</h2>
            <table>
                <thead>
                    <tr>
                        <th>日期</th>
                        <th>开盘</th>
                        <th>最高</th>
                        <th>最低</th>
                        <th>收盘</th>
                    </tr>
                </thead>
                <tbody>
                    {data.slice(0, 10).map((item, index) => (
                        <tr key={index}>
                            <td>{item.date}</td>
                            <td>${item.open?.toFixed(2)}</td>
                            <td>${item.high?.toFixed(2)}</td>
                            <td>${item.low?.toFixed(2)}</td>
                            <td>${item.close?.toFixed(2)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

export default StockChart;
```

### 构建数据仪表板

```python
# dashboard.py - 使用 Streamlit 构建简单仪表板

import streamlit as st
import requests
import pandas as pd

st.title("📈 股票数据仪表板")

# 用户输入
symbol = st.text_input("输入股票代码", value="AAPL")

if st.button("获取数据"):
    # 调用 OpenBB API
    url = f"http://127.0.0.1:6900/api/v1/equity/price/historical"
    params = {"symbol": symbol, "provider": "yfinance"}
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if data["results"]:
            df = pd.DataFrame(data["results"])
            
            # 显示图表
            st.line_chart(df.set_index("date")["close"])
            
            # 显示表格
            st.dataframe(df.tail(10))
            
            # 显示统计
            st.write(f"数据来源: {data['provider']}")
            st.write(f"数据条数: {len(df)}")
        else:
            st.warning("没有获取到数据")
            
    except Exception as e:
        st.error(f"获取数据失败: {e}")

# 运行: streamlit run dashboard.py
```

### Python 封装类

```python
# openbb_client.py

import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

@dataclass
class OpenBBClient:
    """OpenBB API 客户端"""
    
    base_url: str = "http://127.0.0.1:6900/api/v1"
    timeout: int = 30
    
    def _request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict]:
        """发送请求"""
        try:
            response = requests.get(
                f"{self.base_url}/{endpoint}",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return None
    
    def get_stock_historical(
        self,
        symbol: str,
        provider: str = "yfinance",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[List[Dict]]:
        """获取股票历史数据"""
        params = {"symbol": symbol, "provider": provider}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        data = self._request("equity/price/historical", params)
        return data["results"] if data else None
    
    def get_stock_quote(self, symbol: str, provider: str = "yfinance") -> Optional[Dict]:
        """获取股票报价"""
        params = {"symbol": symbol, "provider": provider}
        data = self._request("equity/price/quote", params)
        return data["results"][0] if data and data["results"] else None
    
    def get_crypto_historical(
        self,
        symbol: str,
        provider: str = "yfinance"
    ) -> Optional[List[Dict]]:
        """获取加密货币历史数据"""
        params = {"symbol": symbol, "provider": provider}
        data = self._request("crypto/price/historical", params)
        return data["results"] if data else None

# 使用示例
if __name__ == "__main__":
    client = OpenBBClient()
    
    # 获取股票数据
    aapl_data = client.get_stock_historical("AAPL", start_date="2024-01-01")
    if aapl_data:
        print(f"获取了 {len(aapl_data)} 条 AAPL 数据")
    
    # 获取实时报价
    quote = client.get_stock_quote("AAPL")
    if quote:
        print(f"AAPL 当前价格: ${quote.get('last_price', 'N/A')}")
```

---

## 💡 实践任务

### 任务 1：启动 API 并测试

1. 安装 API 扩展
2. 启动 API 服务
3. 使用浏览器访问 Swagger 文档
4. 测试一个端点

```bash
# 步骤
pip install openbb-platform-api
openbb-api --port 8000

# 访问 http://127.0.0.1:8000/docs
```

### 任务 2：编写 API 调用函数

编写一个函数，可以通过 API 获取多只股票的数据：

```python
import requests

def get_multiple_stocks(symbols, provider="yfinance"):
    """
    获取多只股票的数据
    
    参数:
        symbols: 股票代码列表
        provider: 数据提供者
    
    返回:
        字典 {symbol: data}
    """
    # 在这里实现
    pass

# 测试
result = get_multiple_stocks(["AAPL", "MSFT", "GOOGL"])
```

<details>
<summary>查看答案</summary>

```python
import requests

def get_multiple_stocks(symbols, provider="yfinance"):
    """获取多只股票的数据"""
    base_url = "http://127.0.0.1:6900/api/v1"
    results = {}
    
    for symbol in symbols:
        try:
            response = requests.get(
                f"{base_url}/equity/price/historical",
                params={"symbol": symbol, "provider": provider}
            )
            
            if response.status_code == 200:
                data = response.json()
                results[symbol] = data["results"]
                print(f"✓ {symbol}: 获取了 {len(data['results'])} 条数据")
            else:
                print(f"✗ {symbol}: 请求失败 ({response.status_code})")
                results[symbol] = None
                
        except Exception as e:
            print(f"✗ {symbol}: 错误 - {e}")
            results[symbol] = None
    
    return results

# 测试
result = get_multiple_stocks(["AAPL", "MSFT", "GOOGL"])
```
</details>

### 任务 3：构建简单的 HTML 页面

创建一个 HTML 页面，通过 JavaScript 调用 API 并显示数据：

```html
<!-- stock_viewer.html -->
<!DOCTYPE html>
<html>
<head>
    <title>股票数据查看器</title>
</head>
<body>
    <h1>股票数据查看器</h1>
    
    <input type="text" id="symbol" placeholder="输入股票代码" value="AAPL">
    <button onclick="fetchData()">获取数据</button>
    
    <div id="result"></div>
    
    <script>
        // 在这里实现 fetchData 函数
    </script>
</body>
</html>
```

<details>
<summary>查看答案</summary>

```html
<!DOCTYPE html>
<html>
<head>
    <title>股票数据查看器</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        table { border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: right; }
        th { background-color: #4CAF50; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>📈 股票数据查看器</h1>
    
    <input type="text" id="symbol" placeholder="输入股票代码" value="AAPL">
    <button onclick="fetchData()">获取数据</button>
    
    <div id="result"></div>
    
    <script>
        async function fetchData() {
            const symbol = document.getElementById('symbol').value;
            const resultDiv = document.getElementById('result');
            
            resultDiv.innerHTML = '加载中...';
            
            try {
                const response = await fetch(
                    `http://127.0.0.1:6900/api/v1/equity/price/historical?symbol=${symbol}&provider=yfinance`
                );
                
                const data = await response.json();
                
                if (data.results && data.results.length > 0) {
                    let html = `<h2>${symbol} 最近 10 条数据</h2>`;
                    html += '<table><tr><th>日期</th><th>开盘</th><th>最高</th><th>最低</th><th>收盘</th><th>成交量</th></tr>';
                    
                    data.results.slice(-10).forEach(item => {
                        html += `<tr>
                            <td>${item.date}</td>
                            <td>$${item.open?.toFixed(2) || 'N/A'}</td>
                            <td>$${item.high?.toFixed(2) || 'N/A'}</td>
                            <td>$${item.low?.toFixed(2) || 'N/A'}</td>
                            <td>$${item.close?.toFixed(2) || 'N/A'}</td>
                            <td>${item.volume?.toLocaleString() || 'N/A'}</td>
                        </tr>`;
                    });
                    
                    html += '</table>';
                    html += `<p>数据来源: ${data.provider} | 总数据条数: ${data.results.length}</p>`;
                    resultDiv.innerHTML = html;
                } else {
                    resultDiv.innerHTML = '<p>没有获取到数据</p>';
                }
                
            } catch (error) {
                resultDiv.innerHTML = `<p style="color: red;">错误: ${error.message}</p>`;
            }
        }
    </script>
</body>
</html>
```
</details>

---

## 📚 知识检查

1. **如何启动 OpenBB API 服务？**
   <details>
   <summary>查看答案</summary>
   使用命令 `openbb-api` 或在 Python 中使用 `from openbb_platform_api.main import run; run()`
   </details>

2. **API 的默认端口是多少？**
   <details>
   <summary>查看答案</summary>
   6900
   </details>

3. **如何查看 API 的交互式文档？**
   <details>
   <summary>查看答案</summary>
   访问 http://127.0.0.1:6900/docs（Swagger UI）
   </details>

4. **Python SDK 命令和 API 端点的对应关系是什么？**
   <details>
   <summary>查看答案</summary>
   `obb.module.submodule.method()` 对应 `GET /api/v1/module/submodule/method`
   </details>

---

## ➡️ 下一课预告

在下一课中，我们将学习如何开发自定义扩展：

- 创建自定义 Provider
- 实现 Fetcher 类
- 测试和发布扩展

👉 [**第 8 课：自定义扩展开发 →**](./lesson-08-extension-dev.md)

---

[← 上一课](./lesson-06-data-processing.md) | [返回目录](./README.md) | [下一课 →](./lesson-08-extension-dev.md)
