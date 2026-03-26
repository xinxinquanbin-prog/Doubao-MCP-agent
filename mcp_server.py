"""MCP服务端启动入口（优化版）"""
from mcp.server.fastmcp import FastMCP
from skills import (
    register_calculator_tool, 
    register_weather_tool,
    register_translator_tool,
    register_unit_converter_tool,
    register_currency_converter_tool,
    register_web_search_tool
)

# 初始化MCP服务
mcp = FastMCP(
    name="local-custom-skills"
)

# 注册所有技能工具
register_calculator_tool(mcp)
register_weather_tool(mcp)
register_translator_tool(mcp)
register_unit_converter_tool(mcp)
register_currency_converter_tool(mcp)
register_web_search_tool(mcp)

# 启动MCP服务（stdio模式）
def main():
    mcp.run()

if __name__ == "__main__":
    main()
