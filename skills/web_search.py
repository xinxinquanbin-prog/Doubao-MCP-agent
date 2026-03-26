"""网络搜索技能实现（国内网络优化版 - 必应搜索）"""
import httpx
import re
from mcp.server.fastmcp import FastMCP

def register_web_search_tool(mcp: FastMCP):
    """注册网络搜索工具到 MCP 服务"""
    
    @mcp.tool()
    async def web_search(query: str, num_results: int = 5) -> str:
        """
        搜索互联网信息，支持新闻、百科、技术文档等查询
        
        Args:
            query: 搜索关键词（支持中文）
            num_results: 返回结果数量（默认5条，最多10条）
        
        Returns:
            格式化的搜索结果
        """
        if not query or len(query.strip()) == 0:
            return "❌ 搜索关键词不能为空"
        
        query = query.strip()
        num_results = max(1, min(num_results, 10))
        
        try:
            # 使用必应搜索（国内可访问）
            search_url = "https://cn.bing.com/search"
            params = {
                "q": query,
                "count": num_results,
                "ensearch": 1
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
            
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(search_url, params=params, headers=headers)
                resp.raise_for_status()
                
                # 解析必应搜索结果
                html = resp.text
                results = _parse_bing_html(html, num_results)
                
                if not results:
                    return f"🔍 未找到与「{query}」相关的网络结果\n\n建议：\n• 尝试简化关键词\n• 检查拼写是否正确\n• 使用英文关键词试试"
                
                # 格式化输出
                output = [f"🔍 网络搜索结果：「{query}」\n"]
                for i, (title, url, snippet) in enumerate(results, 1):
                    output.append(f"{i}. {title}")
                    if snippet:
                        output.append(f"   {snippet}")
                    output.append(f"   🔗 {url}\n")
                
                return "\n".join(output)
                
        except httpx.TimeoutException:
            return f"❌ 搜索超时，请检查网络连接后重试"
        except httpx.HTTPStatusError as e:
            return f"❌ 搜索请求失败（HTTP {e.response.status_code}），请稍后重试"
        except Exception as e:
            return f"❌ 搜索失败：{str(e)[:50]}"
    
    @mcp.tool()
    async def get_page_content(url: str) -> str:
        """
        获取网页正文内容（用于提取文章、技术文档等）
        
        Args:
            url: 网页URL（支持http/https）
        
        Returns:
            网页正文内容（最多2000字符）
        """
        if not url:
            return "❌ URL不能为空"
        
        # 简单验证URL格式
        if not url.startswith(("http://", "https://")):
            return "❌ URL必须以 http:// 或 https:// 开头"
        
        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml",
                }
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                
                # 简单提取正文（去除HTML标签）
                html = resp.text
                content = _extract_text(html)
                
                if len(content) > 2000:
                    content = content[:2000] + "\n\n...（内容过长已截断）"
                
                if not content.strip():
                    return "⚠️ 无法提取网页正文内容"
                
                return f"📄 网页内容：\n\n{content}"
                
        except httpx.TimeoutException:
            return f"❌ 获取网页超时，请检查URL是否可访问"
        except httpx.HTTPStatusError as e:
            return f"❌ 网页请求失败（HTTP {e.response.status_code}）"
        except Exception as e:
            return f"❌ 获取网页失败：{str(e)[:50]}"


def _parse_bing_html(html: str, num_results: int) -> list:
    """解析必应搜索结果 HTML"""
    results = []
    
    # 必应搜索结果pattern
    # <li class="b_algo"><h2><a href="URL" ...>标题</a></h2><p>摘要...</p></li>
    item_pattern = r'<li class="b_algo">(.*?)</li>'
    title_pattern = r'<h2><a[^>]+href="([^"]+)"[^>]*>([^<]+)</a></h2>'
    snippet_pattern = r'<p>([^<]+)</p>'
    
    items = re.findall(item_pattern, html, re.DOTALL)
    
    for item in items[:num_results]:
        title_match = re.search(title_pattern, item)
        snippet_match = re.search(snippet_pattern, item)
        
        if title_match:
            url = title_match.group(1)
            title = _clean_html(title_match.group(2))
            snippet = _clean_html(snippet_match.group(1)) if snippet_match else ""
            results.append((title, url, snippet))
    
    return results


def _extract_text(html: str) -> str:
    """简单去除HTML标签提取正文"""
    # 移除 script 和 style 标签及内容
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # 移除所有 HTML 标签
    html = re.sub(r'<[^>]+>', ' ', html)
    # 清理多余空白
    html = re.sub(r'\s+', ' ', html)
    return html.strip()


def _clean_html(text: str) -> str:
    """清理HTML实体和标签残留"""
    import html
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
