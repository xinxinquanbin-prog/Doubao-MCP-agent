# 豆包本地技能助手（增强版）

一个基于 MCP (Model Context Protocol) 协议的本地技能助手，支持计算器、天气查询、翻译、单位换算等多种自定义技能，提供 Web 界面和 API 接口。

## 🌟 新增功能

- ✅ **对话历史** - 支持多轮对话，自动记忆上下文
- ✅ **翻译技能** - 内置词典 + 多语言支持
- ✅ **单位换算** - 长度/重量/温度/面积/体积
- ✅ **流式返回** - 支持 SSE 流式输出
- ✅ **会话管理** - 支持多会话隔离

## 项目结构

```
d:\agent\
├── .env                    # 大模型api配置
├── index.html              # 前端 Web 界面
├── main.py                 # 主入口（命令行模式）
├── mcp_server.py          # MCP 服务端（核心）
├── server.py               # Flask 后端服务
├── requirements.txt        # 依赖清单
├── README.md               # 项目说明
├── config/                 # 配置目录
│   └── settings.py
├── client/                 # 客户端目录
│   └── doubao_mcp_client.py
└── skills/                 # 技能实现目录
    ├── calculator.py       # 计算器技能
    ├── weather.py          # 天气查询技能
    ├── translator.py       # 翻译技能 ✨
    └── unit_converter.py   # 单位换算技能 ✨
```

## 核心组件

1. **前端** (`index.html`) - 基于 HTML/CSS/JavaScript 的 Web 界面
2. **后端** (`server.py`) - Flask 服务，支持对话历史和流式输出
3. **MCP 服务** (`mcp_server.py`) - 处理技能调用的核心服务
4. **技能模块** (`skills/`) - 各种自定义技能的实现

## 环境要求

- Python 3.11+
- 火山引擎豆包 API 密钥（获取 AK/SK）

## 安装

1. **克隆项目**
   ```bash
   git clone https://github.com/taffy123d/Doubao-MCP-agent
   cd Doubao-MCP-agent
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   复制 `.env.example` 为 `.env` 并填写 API 密钥：
   ```env
   DOUBAO_API_KEY=你的API密钥
   DOUBAO_ENDPOINT_ID=你的终端ID
   DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3/chat/completions
   ```

## 运行

### 启动服务（推荐）

```bash
python server.py
```

- 前端访问：`http://localhost:5000`
- API 接口：`http://localhost:5000/api/*`

### 命令行模式

```bash
python main.py
```

## 技能列表

### 计算器技能
- **调用**：计算 `(10+5)*2`
- **功能**：支持加减乘除、括号、幂运算

### 天气查询技能
- **调用**：`北京天气` 或 `上海天气 3天`
- **功能**：查询城市天气和预报

### 翻译技能 ✨
- **调用**：`翻译 hello 到 中文` 或 `translate "good morning" to 日语`
- **功能**：
  - 内置常用短语词典（离线可用）
  - 支持中英日韩法德俄等10+语言
  - 自动识别源语言

### 单位换算技能 ✨
- **调用**：
  - `长度换算 100 km 到 m`
  - `重量换算 1 kg 到 磅`
  - `温度换算 100 C 到 F`
  - `面积换算 1 公顷 到 平方米`
  - `体积换算 1 加仑 到 升`
- **功能**：支持长度、重量、温度、面积、体积换算

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 前端页面 |
| `/api/health` | GET | 健康检查 |
| `/api/tools` | GET | 获取技能列表 |
| `/api/config` | GET/POST | 配置管理 |
| `/api/test-connection` | POST | 测试 API 连接 |
| `/api/chat` | POST | 聊天（支持历史） |
| `/api/chat/stream` | POST | 流式聊天（SSE） |
| `/api/chat/clear` | POST | 清除对话历史 |

## 对话历史

聊天接口支持 `session_id` 参数，实现多轮对话：

```javascript
// 第一次对话
const res1 = await fetch('/api/chat', {
  method: 'POST',
  body: JSON.stringify({
    api_key: 'xxx',
    endpoint_id: 'xxx',
    base_url: 'xxx',
    message: '我叫小明',
    session_id: 'user123'
  })
});

// 第二次对话（会自动带上历史）
const res2 = await fetch('/api/chat', {
  method: 'POST',
  body: JSON.stringify({
    api_key: 'xxx',
    endpoint_id: 'xxx',
    base_url: 'xxx',
    message: '我叫什么？',
    session_id: 'user123'  // 同一个session_id
  })
});
```

## 如何增加新技能

### 步骤 1：创建技能文件

在 `skills/` 目录下创建新的技能文件，例如 `my_skill.py`：

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my_skill")

@mcp.tool()
def my_skill(param1: str, param2: int = 1) -> str:
    """
    我的自定义技能描述
    示例：my_skill(param1="值", param2=2)
    
    Args:
        param1: 参数1描述
        param2: 参数2描述（默认值）
    Returns:
        技能执行结果
    """
    try:
        result = f"处理结果: {param1} - {param2}"
        return result
    except Exception as e:
        return f"处理失败: {str(e)}"

def register_my_skill(mcp: FastMCP):
    """注册技能"""
    mcp.add_tool(my_skill)
```

### 步骤 2：注册技能

编辑 `skills/__init__.py`：

```python
from .my_skill import register_my_skill

__all__ = [
    "register_my_skill",
    # ...其他技能
]
```

### 步骤 3：更新 MCP 服务

编辑 `mcp_server.py`：

```python
from skills import register_my_skill

register_my_skill(mcp)
```

## 故障排除

- **连接失败**：检查 API 密钥和网络连接
- **技能不响应**：检查 MCP 服务是否正常运行
- **前端不显示**：检查浏览器控制台是否有错误
- **工具列表为空**：重新启动服务

## License

MIT
