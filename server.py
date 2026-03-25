"""
豆包本地技能助手 - Flask 后端服务
"""
import asyncio
import json
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# MCP 服务配置
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
MCP_SERVER = StdioServerParameters(
    command="python",
    args=["-u", os.path.join(ROOT_DIR, "mcp_server.py")],
    cwd=ROOT_DIR
)

# 缓存 MCP 工具列表
_cached_tools = None


async def get_mcp_tools():
    """获取 MCP 工具列表"""
    global _cached_tools
    if _cached_tools is not None:
        return _cached_tools
    
    async with stdio_client(MCP_SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            _cached_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.inputSchema
                    }
                }
                for t in tools_result.tools
            ]
            return _cached_tools


async def run_mcp_tool(tool_name: str, arguments: dict):
    """运行 MCP 工具"""
    async with stdio_client(MCP_SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name=tool_name, arguments=arguments)
            return result.content[0].text


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({"status": "ok", "message": "服务正常运行"})


@app.route('/api/config', methods=['GET'])
def get_config():
    """获取配置"""
    config = {}
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip("'").strip('"')
    return jsonify(config)


@app.route('/api/config', methods=['POST'])
def save_config():
    """保存配置到 .env 文件"""
    data = request.json
    try:
        # 读取现有配置
        existing_config = {}
        if os.path.exists('.env'):
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line:
                        key, value = line.split('=', 1)
                        existing_config[key.strip()] = value.strip()
        
        # 更新配置
        if 'DOUBAO_API_KEY' in data:
            existing_config['DOUBAO_API_KEY'] = f"'{data['DOUBAO_API_KEY']}'"
        if 'DOUBAO_ENDPOINT_ID' in data:
            existing_config['DOUBAO_ENDPOINT_ID'] = f"'{data['DOUBAO_ENDPOINT_ID']}'"
        if 'DOUBAO_BASE_URL' in data:
            existing_config['DOUBAO_BASE_URL'] = f"'{data['DOUBAO_BASE_URL']}'"
        
        # 写入配置文件
        with open('.env', 'w', encoding='utf-8') as f:
            for key, value in existing_config.items():
                f.write(f"{key}={value}\n")
        
        return jsonify({"success": True, "message": "配置保存成功"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/tools', methods=['GET'])
def get_tools():
    """获取可用工具列表"""
    try:
        tools = asyncio.run(get_mcp_tools())
        return jsonify({"tools": tools})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    """测试 API 连接"""
    data = request.json
    api_key = data.get('api_key', '')
    endpoint_id = data.get('endpoint_id', '')
    base_url = data.get('base_url', '')
    
    if not api_key or not endpoint_id:
        return jsonify({"connected": False, "error": "缺少 API Key 或 Endpoint ID"})
    
    async def _test():
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    url=base_url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": endpoint_id,
                        "messages": [{"role": "user", "content": "test"}],
                        "temperature": 0.1
                    }
                )
                return resp.status_code == 200
        except Exception:
            return False
    
    try:
        is_connected = asyncio.run(_test())
        return jsonify({"connected": is_connected})
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)})


@app.route('/api/chat', methods=['POST'])
def chat():
    """聊天接口 - 调用豆包 API 和 MCP 工具"""
    data = request.json
    api_key = data.get('api_key', '')
    endpoint_id = data.get('endpoint_id', '')
    base_url = data.get('base_url', '')
    user_message = data.get('message', '')
    
    if not api_key or not endpoint_id:
        return jsonify({"error": "缺少 API Key 或 Endpoint ID"}), 400
    
    if not user_message:
        return jsonify({"error": "消息内容不能为空"}), 400
    
    async def _chat():
        # 获取 MCP 工具
        tools = await get_mcp_tools()
        
        async with httpx.AsyncClient(timeout=60) as http_client:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            messages = [{"role": "user", "content": user_message}]
            
            # 第一次调用豆包 API
            resp = await http_client.post(
                url=base_url,
                headers=headers,
                json={
                    "model": endpoint_id,
                    "messages": messages,
                    "tools": tools,
                    "temperature": 0.1
                }
            )
            
            if resp.status_code != 200:
                return f"API 调用失败: {resp.status_code}"
            
            result = resp.json()
            msg = result["choices"][0]["message"]
            
            # 检查是否需要调用工具
            if "tool_calls" in msg:
                tool_call = msg["tool_calls"][0]
                tool_name = tool_call["function"]["name"]
                tool_args = json.loads(tool_call["function"]["arguments"])
                
                # 调用 MCP 工具
                tool_result = await run_mcp_tool(tool_name, tool_args)
                
                # 构建第二次调用的消息
                messages.append(msg)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": tool_result
                })
                
                # 第二次调用豆包 API
                final_resp = await http_client.post(
                    url=base_url,
                    headers=headers,
                    json={
                        "model": endpoint_id,
                        "messages": messages,
                        "temperature": 0.1
                    }
                )
                
                if final_resp.status_code == 200:
                    final_result = final_resp.json()
                    return final_result["choices"][0]["message"].get("content") or tool_result
                else:
                    return tool_result
            
            return msg.get("content", "无响应内容")
    
    try:
        response = asyncio.run(_chat())
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """流式聊天接口（SSE）"""
    data = request.json
    api_key = data.get('api_key', '')
    endpoint_id = data.get('endpoint_id', '')
    base_url = data.get('base_url', '')
    user_message = data.get('message', '')
    
    # 流式响应实现较复杂，先返回普通响应
    return chat()


@app.route('/')
def index():
    """返回前端页面"""
    return send_from_directory('.', 'index.html')


@app.route('/<path:path>')
def static_files(path):
    """返回静态文件"""
    return send_from_directory('.', path)


if __name__ == '__main__':
    print("=" * 50)
    print("豆包本地技能助手 - Flask 后端服务")
    print("=" * 50)
    print("服务地址: http://localhost:5000")
    print("API 文档:")
    print("  GET  /api/health          - 健康检查")
    print("  GET  /api/tools           - 获取工具列表")
    print("  POST /api/test-connection - 测试连接")
    print("  POST /api/chat            - 聊天")
    print("=" * 50)
    
    # 确保 MCP 服务文件存在
    mcp_server_path = os.path.join(ROOT_DIR, "mcp_server.py")
    if not os.path.exists(mcp_server_path):
        print(f"\n警告: 未找到 MCP 服务文件: {mcp_server_path}")
        print("请先创建 mcp_server.py 文件\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
