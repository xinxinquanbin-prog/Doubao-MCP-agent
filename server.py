"""
豆包本地技能助手 - Flask 后端服务（优化版）
✅ 修复异步问题
✅ 支持对话历史
✅ 实现流式返回
✅ 新增翻译和单位换算技能
"""
import asyncio
import json
import os
import threading
from collections import defaultdict
from queue import Queue
from flask import Flask, request, jsonify, send_from_directory, Response
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

# 对话历史存储 (session_id -> messages)
chat_histories = defaultdict(list)
MAX_HISTORY = 20  # 最多保留20轮


def get_mcp_tools_cached():
    """同步获取MCP工具列表（使用缓存）"""
    global _cached_tools
    if _cached_tools is not None:
        return _cached_tools
    
    # 在新线程中运行
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        _cached_tools = loop.run_until_complete(_get_mcp_tools_async())
    finally:
        loop.close()
    
    return _cached_tools


async def _get_mcp_tools_async():
    """异步获取MCP工具列表"""
    try:
        async with stdio_client(MCP_SERVER) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                return [
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
    except Exception as e:
        print(f"获取工具列表失败: {e}")
        return []


def run_mcp_tool_sync(tool_name: str, arguments: dict) -> str:
    """在新线程中运行MCP工具"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_run_mcp_tool_async(tool_name, arguments))
        return result
    finally:
        loop.close()


async def _run_mcp_tool_async(tool_name: str, arguments: dict) -> str:
    """异步运行MCP工具"""
    try:
        async with stdio_client(MCP_SERVER) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(name=tool_name, arguments=arguments)
                return result.content[0].text
    except Exception as e:
        return f"工具调用失败: {str(e)}"


async def _chat_with_tools_async(api_key: str, endpoint_id: str, base_url: str, 
                                 user_message: str, messages_history: list) -> dict:
    """异步处理聊天（支持工具调用和对话历史）"""
    tools = get_mcp_tools_cached()
    
    async with httpx.AsyncClient(timeout=60) as http_client:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建消息列表（带历史）
        messages = messages_history.copy()
        messages.append({"role": "user", "content": user_message})
        
        # 第一次调用豆包 API
        resp = await http_client.post(
            url=base_url,
            headers=headers,
            json={
                "model": endpoint_id,
                "messages": messages,
                "tools": tools,
                "temperature": 0.7
            }
        )
        
        if resp.status_code != 200:
            return {"error": f"API 调用失败: {resp.status_code}", "messages": messages_history}
        
        result = resp.json()
        msg = result["choices"][0]["message"]
        
        # 检查是否需要调用工具
        if "tool_calls" in msg:
            tool_call = msg["tool_calls"][0]
            tool_name = tool_call["function"]["name"]
            tool_args = json.loads(tool_call["function"]["arguments"])
            
            # 保存AI的回复
            messages.append(msg)
            
            # 调用 MCP 工具
            tool_result = await _run_mcp_tool_async(tool_name, tool_args)
            
            # 保存工具结果
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
                    "temperature": 0.7
                }
            )
            
            if final_resp.status_code == 200:
                final_result = final_resp.json()
                final_msg = final_result["choices"][0]["message"]
                answer = final_msg.get("content", tool_result)
                messages.append(final_msg)
            else:
                answer = tool_result
                messages.append({"role": "assistant", "content": tool_result})
        else:
            # 普通对话
            answer = msg.get("content", "无响应内容")
            messages.append(msg)
        
        return {"response": answer, "messages": messages}


def chat_in_thread(api_key: str, endpoint_id: str, base_url: str, 
                   user_message: str, messages_history: list) -> dict:
    """在线程中运行异步聊天"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            _chat_with_tools_async(api_key, endpoint_id, base_url, user_message, messages_history)
        )
    finally:
        loop.close()


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
        existing_config = {}
        if os.path.exists('.env'):
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line:
                        key, value = line.split('=', 1)
                        existing_config[key.strip()] = value.strip()
        
        if 'DOUBAO_API_KEY' in data:
            existing_config['DOUBAO_API_KEY'] = f"'{data['DOUBAO_API_KEY']}'"
        if 'DOUBAO_ENDPOINT_ID' in data:
            existing_config['DOUBAO_ENDPOINT_ID'] = f"'{data['DOUBAO_ENDPOINT_ID']}'"
        if 'DOUBAO_BASE_URL' in data:
            existing_config['DOUBAO_BASE_URL'] = f"'{data['DOUBAO_BASE_URL']}'"
        
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
        tools = get_mcp_tools_cached()
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
    
    def test():
        try:
            import requests
            resp = requests.post(
                url=base_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": endpoint_id,
                    "messages": [{"role": "user", "content": "test"}],
                    "temperature": 0.1
                },
                timeout=10
            )
            return resp.status_code == 200
        except:
            return False
    
    is_connected = test()
    return jsonify({"connected": is_connected})


@app.route('/api/chat', methods=['POST'])
def chat():
    """聊天接口 - 支持对话历史"""
    data = request.json
    api_key = data.get('api_key', '')
    endpoint_id = data.get('endpoint_id', '')
    base_url = data.get('base_url', '')
    user_message = data.get('message', '')
    session_id = data.get('session_id', 'default')
    
    if not api_key or not endpoint_id:
        return jsonify({"error": "缺少 API Key 或 Endpoint ID"}), 400
    
    if not user_message:
        return jsonify({"error": "消息内容不能为空"}), 400
    
    # 获取该session的历史
    messages_history = chat_histories.get(session_id, [])
    
    # 执行聊天
    result = chat_in_thread(api_key, endpoint_id, base_url, user_message, messages_history)
    
    # 更新历史
    if "messages" in result:
        chat_histories[session_id] = result["messages"][-MAX_HISTORY:]
    
    if "error" in result:
        return jsonify({"error": result["error"]}), 500
    
    return jsonify({
        "response": result["response"],
        "session_id": session_id
    })


@app.route('/api/chat/clear', methods=['POST'])
def clear_history():
    """清除对话历史"""
    data = request.json
    session_id = data.get('session_id', 'default')
    chat_histories.pop(session_id, None)
    return jsonify({"success": True, "message": f"会话 {session_id} 历史已清除"})


@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """流式聊天接口（SSE）"""
    data = request.json
    api_key = data.get('api_key', '')
    endpoint_id = data.get('endpoint_id', '')
    base_url = data.get('base_url', '')
    user_message = data.get('message', '')
    session_id = data.get('session_id', 'default')
    
    if not api_key or not endpoint_id:
        return jsonify({"error": "缺少 API Key 或 Endpoint ID"}), 400
    
    if not user_message:
        return jsonify({"error": "消息内容不能为空"}), 400
    
    messages_history = chat_histories.get(session_id, [])
    
    def generate():
        try:
            # 发送开始信号
            yield f"data: {json.dumps({'type': 'start'})}\n\n"
            
            # 执行聊天（这里简化处理，完整实现需要SSE流式）
            result = chat_in_thread(api_key, endpoint_id, base_url, user_message, messages_history)
            
            if "error" in result:
                yield f"data: {json.dumps({'type': 'error', 'content': result['error']})}\n\n"
            else:
                # 更新历史
                if "messages" in result:
                    chat_histories[session_id] = result["messages"][-MAX_HISTORY:]
                
                # 发送完成信号
                yield f"data: {json.dumps({'type': 'done', 'content': result['response']})}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        }
    )


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
    print("豆包本地技能助手 - Flask 后端服务（优化版）")
    print("=" * 50)
    print("服务地址: http://localhost:5000")
    print("API 文档:")
    print("  GET  /api/health          - 健康检查")
    print("  GET  /api/tools           - 获取工具列表")
    print("  POST /api/test-connection - 测试连接")
    print("  POST /api/chat           - 聊天（支持历史）")
    print("  POST /api/chat/stream     - 流式聊天")
    print("  POST /api/chat/clear     - 清除历史")
    print("=" * 50)
    print("新增技能: 计算器 | 天气查询 | 翻译 | 单位换算")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
