"""安全计算器技能实现"""
import ast
from mcp.server.fastmcp import FastMCP
from config import settings

def register_calculator_tool(mcp: FastMCP):
    """注册计算器工具到MCP服务"""
    
    @mcp.tool()
    def calculator(expression: str) -> str:
        """
        安全的数学计算器，支持加减乘除、括号、正负号、幂运算
        示例：calculator(expression="(10+5)*2/3 - 4^2")
        
        Args:
            expression: 合法的数学表达式字符串，仅支持数字和基础运算符
        Returns:
            计算结果或错误提示
        """
        try:
            # 解析表达式为AST语法树，杜绝代码注入风险
            tree = ast.parse(expression, mode='eval')
            
            # 递归校验语法树，仅允许安全的节点类型
            def validate_node(node):
                # 允许数字常量
                if isinstance(node, ast.Constant):
                    if not isinstance(node.value, (int, float)):
                        raise ValueError(f"不支持的常量类型: {type(node.value)}")
                    return
                # 允许一元运算符（正负号）
                elif isinstance(node, ast.UnaryOp):
                    if type(node.op) not in settings.ALLOWED_OPERATORS:
                        raise ValueError(f"不支持的一元运算符: {type(node.op)}")
                    validate_node(node.operand)
                    return
                # 允许二元运算符（加减乘除等）
                elif isinstance(node, ast.BinOp):
                    if type(node.op) not in settings.ALLOWED_OPERATORS:
                        raise ValueError(f"不支持的二元运算符: {type(node.op)}")
                    validate_node(node.left)
                    validate_node(node.right)
                    return
                # 禁止其他所有节点（函数调用、变量、属性访问等）
                else:
                    raise ValueError(f"不支持的表达式节点: {type(node)}")
            
            # 执行校验
            validate_node(tree.body)
            
            # 安全计算表达式
            result = eval(compile(tree, filename='<ast>', mode='eval'))
            return f"计算结果: {expression} = {result}"
        
        except ZeroDivisionError:
            return "计算错误：除数不能为0"
        except ValueError as e:
            return f"表达式校验失败: {str(e)}"
        except SyntaxError:
            return "表达式语法错误，请检查括号、运算符是否正确"
        except Exception as e:
            return f"计算失败: {str(e)}"
