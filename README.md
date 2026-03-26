# 豆包本地技能助手 🐔

一个基于 MCP (Model Context Protocol) 协议的本地技能助手，支持计算器、天气查询、时间查询等自定义技能，提供 Web 界面和 API 接口。

[![GitHub stars](https://img.shields.io/github/stars/taffy123d/Doubao-MCP-agent)](https://github.com/taffy123d/Doubao-MCP-agent/stargazers)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## ✨ 功能特性

- 🔌 **MCP 协议支持** - 基于 Model Context Protocol 标准协议
- 🧮 **智能计算器** - 安全数学计算，支持复杂表达式
- 🌤️ **天气查询** - 支持国内主要城市实时天气
- ⏰ **时间查询** - 获取当前时间和时区信息
- 💬 **多轮对话** - 支持对话上下文记忆
- 📡 **流式输出** - SSE 流式响应，实时显示
- 🌐 **双端支持** - Web 界面 + 命令行

## 📁 项目结构

```
Doubao-MCP-agent/
├── .env                      # API配置
├── index.html                # 前端页面
├── main.py                   # 命令行入口
├── mcp_server.py            # MCP服务
├── server.py                 # Flask后端
├── requirements.txt          # 依赖
├── client/                   # 客户端
│   └── doubao_mcp_client.py
├── config/                   # 配置
│   └── settings.py
└── skills/                   # 技能
    ├── calculator.py
    ├── weather.py
    └── time_query.py        # 🆕 新增
```

## 🚀 快速开始

### 环境要求

- Python 3.11+
- 火山引擎豆包 API 密钥

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/taffy123d/Doubao-MCP-agent
cd Doubao-MCP-agent

# 使用 uv（推荐）
uv venv && uv sync

# 或使用 pip
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### 配置

在 `.env` 中配置：

```env
DOUBAO_API_KEY=你的API密钥
DOUBAO_ENDPOINT_ID=你的终端ID
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3/chat/completions
```

### 运行

```bash
# Web服务（访问 http://localhost:5000）
python server.py

# 命令行模式
python main.py
```

## 🛠️ API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `GET /api/health` | 健康检查 |
| `GET /api/tools` | 获取技能列表 |
| `GET /api/config` | 获取配置 |
| `POST /api/config` | 保存配置 |
| `POST /api/test-connection` | 测试连接 |
| `POST /api/chat` | 聊天 |
| `POST /api/chat/stream` | 流式聊天 |
| `POST /api/chat/clear` | 清除历史 |

## 💡 使用示例

### 计算器
```
用户: 计算 (10+5)*2/3 - 4^2
助手: 计算结果: (10+5)*2/3 - 4^2 = -9.333333333333334
```

### 天气查询
```
用户: 北京天气
助手: 【北京】实时天气
      天气：晴
      温度：25℃
```

### 时间查询
```
用户: 现在几点了
助手: 当前时间：2024-01-15 14:30:45 (UTC+8 北京时间)
```

## 🧩 自定义技能

在 `skills/` 目录创建新技能：

```python
# skills/my_skill.py
from mcp.server.fastmcp import FastMCP

def register_my_skill(mcp: FastMCP):
    @mcp.tool()
    def my_tool(param: str) -> str:
        """技能描述"""
        return f"结果: {param}"
```

注册到 `mcp_server.py` 即可。

## 📝 License

MIT License
