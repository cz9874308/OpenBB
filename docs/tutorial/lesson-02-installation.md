# 第 2 课：环境搭建与安装

**⏱ 课时**：20 分钟  
**🎯 学习目标**：完成 OpenBB 安装并验证环境  
**📚 难度**：⭐ 入门

---

## 📖 本课内容

- [2.1 环境要求](#21-环境要求)
- [2.2 安装方式](#22-安装方式)
- [2.3 验证安装](#23-验证安装)
- [2.4 配置 API 密钥（可选）](#24-配置-api-密钥可选)
- [2.5 常见问题排查](#25-常见问题排查)
- [💡 实践任务](#-实践任务)

---

## 2.1 环境要求

在安装 OpenBB 之前，请确保你的系统满足以下要求：

### 🖥️ 操作系统

| 操作系统 | 支持情况 |
|---------|---------|
| Windows 10/11 | ✅ 完全支持 |
| macOS 10.15+ | ✅ 完全支持 |
| Linux (Ubuntu 20.04+) | ✅ 完全支持 |

### 🐍 Python 版本

```
┌─────────────────────────────────────────┐
│           Python 版本要求               │
├─────────────────────────────────────────┤
│                                         │
│   最低版本：Python 3.9                   │
│   推荐版本：Python 3.10 或 3.11          │
│   最高版本：Python 3.12                  │
│                                         │
│   ⚠️  不支持 Python 3.8 及以下版本       │
│                                         │
└─────────────────────────────────────────┘
```

### 检查当前 Python 版本

打开终端（命令行），输入：

```bash
python --version
```

或者：

```bash
python3 --version
```

你应该看到类似这样的输出：

```
Python 3.11.5
```

> 💡 **提示**：如果版本低于 3.9，请先升级 Python。推荐使用 [pyenv](https://github.com/pyenv/pyenv) 管理多个 Python 版本。

---

## 2.2 安装方式

OpenBB 提供三种安装方式，根据你的需求选择：

### 方式一：基础安装（推荐新手）

这是最简单的安装方式，适合快速体验：

```bash
pip install openbb
```

**安装内容**：
- OpenBB 核心库
- 常用数据提供者（yfinance、SEC 等免费源）

**适合人群**：
- 刚接触 OpenBB 的新手
- 只需要基础数据功能
- 不需要付费数据源

### 方式二：完整安装

安装所有可用的扩展和数据提供者：

```bash
pip install "openbb[all]"
```

**安装内容**：
- OpenBB 核心库
- 所有数据提供者
- 所有扩展（图表、技术分析等）

**适合人群**：
- 需要访问多个数据源
- 需要图表和可视化功能
- 计划深入使用 OpenBB

### 方式三：按需安装

只安装你需要的组件：

```bash
# 安装核心库
pip install openbb

# 按需添加数据提供者
pip install openbb-yfinance      # Yahoo Finance
pip install openbb-fmp           # Financial Modeling Prep
pip install openbb-fred          # 美联储经济数据
pip install openbb-sec           # SEC 监管数据

# 按需添加扩展
pip install openbb-charting      # 图表功能
pip install openbb-technical     # 技术分析
```

**适合人群**：
- 对安装包大小有要求
- 明确知道需要哪些功能
- 想要更精细的控制

### 📊 安装方式对比

| 安装方式 | 命令 | 安装时间 | 磁盘空间 | 功能覆盖 |
|---------|------|---------|---------|---------|
| 基础安装 | `pip install openbb` | ~2 分钟 | ~200MB | 基础 |
| 完整安装 | `pip install "openbb[all]"` | ~5 分钟 | ~500MB | 全部 |
| 按需安装 | 手动选择 | 视情况 | 自定义 | 自定义 |

---

## 2.3 验证安装

安装完成后，让我们验证一切是否正常。

### 步骤 1：检查导入

打开 Python 解释器或创建一个新的 Python 文件：

```python
from openbb import obb
print("OpenBB 导入成功！")
```

如果没有报错，说明安装成功。

### 步骤 2：查看版本

```python
from openbb import obb

# 查看 OpenBB 版本
print(f"OpenBB 版本: {obb.__version__}")
```

### 步骤 3：测试数据获取

```python
from openbb import obb

# 获取苹果股票最近 5 天的数据（使用免费的 yfinance）
data = obb.equity.price.historical(
    symbol="AAPL",
    provider="yfinance",
    start_date="2024-01-01",
    end_date="2024-01-10"
)

# 打印结果
print(data)
```

如果看到数据输出，恭喜你，OpenBB 已经可以正常工作了！

### 🎯 预期输出示例

```
OBBject

id: 0a1b2c3d-4e5f-6789-abcd-ef0123456789
results: [{'date': datetime.date(2024, 1, 2), 'open': 185.33, 'high': 186.06, ...}]
provider: yfinance
warnings: None
chart: None
extra: {'metadata': {'symbol': 'AAPL', ...}}
```

---

## 2.4 配置 API 密钥（可选）

有些数据提供者需要 API 密钥才能使用。免费数据源（如 yfinance、SEC）不需要密钥。

### 哪些提供者需要密钥？

| 提供者 | 需要密钥 | 是否免费 | 注册链接 |
|-------|---------|---------|---------|
| yfinance | ❌ 不需要 | ✅ 免费 | - |
| SEC | ❌ 不需要 | ✅ 免费 | - |
| FRED | ✅ 需要 | ✅ 免费 | [注册](https://fred.stlouisfed.org/docs/api/api_key.html) |
| FMP | ✅ 需要 | 部分免费 | [注册](https://financialmodelingprep.com/developer) |
| Polygon | ✅ 需要 | 部分免费 | [注册](https://polygon.io/) |
| Intrinio | ✅ 需要 | ❌ 付费 | [注册](https://intrinio.com/) |

### 配置方式一：代码中配置（临时）

```python
from openbb import obb

# 设置 FMP 的 API 密钥
obb.user.credentials.fmp_api_key = "your_api_key_here"

# 现在可以使用 FMP 数据源了
data = obb.equity.price.historical("AAPL", provider="fmp")
```

### 配置方式二：环境变量（推荐）

设置环境变量，这样不用在代码中暴露密钥：

**Windows (PowerShell)**：
```powershell
$env:OPENBB_FMP_API_KEY = "your_api_key_here"
```

**Windows (CMD)**：
```cmd
set OPENBB_FMP_API_KEY=your_api_key_here
```

**macOS / Linux**：
```bash
export OPENBB_FMP_API_KEY="your_api_key_here"
```

永久保存（添加到 `~/.bashrc` 或 `~/.zshrc`）：
```bash
echo 'export OPENBB_FMP_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

### 配置方式三：配置文件

创建配置文件 `~/.openbb_platform/user_settings.json`：

```json
{
  "credentials": {
    "fmp_api_key": "your_api_key_here",
    "fred_api_key": "your_fred_key_here"
  }
}
```

> 💡 **安全提示**：不要将包含 API 密钥的代码提交到公开仓库！

---

## 2.5 常见问题排查

### 问题 1：pip install 失败

**错误信息**：
```
ERROR: Could not find a version that satisfies the requirement openbb
```

**解决方案**：
1. 检查 Python 版本是否 >= 3.9
2. 升级 pip：`pip install --upgrade pip`
3. 使用国内镜像：`pip install openbb -i https://pypi.tuna.tsinghua.edu.cn/simple`

### 问题 2：导入时报错

**错误信息**：
```
ModuleNotFoundError: No module named 'openbb'
```

**解决方案**：
1. 确认安装成功：`pip show openbb`
2. 检查是否在正确的虚拟环境中
3. 尝试重新安装：`pip uninstall openbb && pip install openbb`

### 问题 3：获取数据时超时

**错误信息**：
```
ConnectionError: HTTPSConnectionPool(host='...', port=443): Read timed out
```

**解决方案**：
1. 检查网络连接
2. 尝试使用代理
3. 稍后重试（可能是数据源服务器问题）

### 问题 4：API 密钥无效

**错误信息**：
```
AuthenticationError: Invalid API key
```

**解决方案**：
1. 检查密钥是否正确复制（无多余空格）
2. 确认密钥未过期
3. 检查是否使用了正确的环境变量名

---

## 💡 实践任务

完成以下任务，巩固你的学习：

- [ ] **任务 1**：创建一个新的虚拟环境
  ```bash
  python -m venv openbb-env
  # Windows 激活
  openbb-env\Scripts\activate
  # macOS/Linux 激活
  source openbb-env/bin/activate
  ```

- [ ] **任务 2**：安装 OpenBB（选择基础安装或完整安装）

- [ ] **任务 3**：运行验证代码，确保安装成功

- [ ] **任务 4**：（可选）注册一个免费的 FRED API 密钥并配置

---

## 📚 知识检查

1. **OpenBB 支持的最低 Python 版本是多少？**
   <details>
   <summary>查看答案</summary>
   Python 3.9
   </details>

2. **如何安装 OpenBB 的所有功能？**
   <details>
   <summary>查看答案</summary>
   使用命令：pip install "openbb[all]"
   </details>

3. **配置 API 密钥有哪几种方式？**
   <details>
   <summary>查看答案</summary>
   三种：代码中配置、环境变量、配置文件
   </details>

---

## ➡️ 下一课预告

在下一课中，我们将：

- 编写第一个 OpenBB 程序
- 学习如何解读返回的数据
- 探索更多数据获取命令

👉 [**第 3 课：第一个程序 →**](./lesson-03-first-program.md)

---

[← 上一课](./lesson-01-introduction.md) | [返回目录](./README.md) | [下一课 →](./lesson-03-first-program.md)
