"""货币换算技能"""
import re
import httpx
from mcp.server.fastmcp import FastMCP

# 默认汇率表（基准货币：美元）— 2024年参考值
DEFAULT_RATES = {
    "USD": 1.0,
    "CNY": 7.24,
    "EUR": 0.92,
    "GBP": 0.79,
    "JPY": 149.50,
    "HKD": 7.82,
    "KRW": 1330.0,
    "TWD": 31.50,
    "SGD": 1.34,
    "AUD": 1.53,
    "CAD": 1.36,
    "CHF": 0.88,
    "INR": 83.20,
    "THB": 35.50,
    "MYR": 4.72,
    "PHP": 56.20,
    "VND": 24500.0,
}

CURRENCY_NAMES = {
    "CNY": "人民币",
    "USD": "美元",
    "EUR": "欧元",
    "GBP": "英镑",
    "JPY": "日元",
    "HKD": "港币",
    "KRW": "韩元",
    "TWD": "台币",
    "SGD": "新加坡元",
    "AUD": "澳元",
    "CAD": "加元",
    "CHF": "瑞士法郎",
    "INR": "印度卢比",
    "THB": "泰铢",
    "MYR": "林吉特",
    "PHP": "菲律宾比索",
    "VND": "越南盾",
}

CURRENCY_CODES = list(DEFAULT_RATES.keys())


def normalize_currency(currency_str: str) -> str:
    """规范化货币代码"""
    s = currency_str.upper().strip()
    # 支持中文名
    for code, name in CURRENCY_NAMES.items():
        if name in s or code in s:
            return code
    # 去掉"元""圆""块"等后缀
    s = re.sub(r"(元|圆|块|美元?|英鎊|日圓|韓圓)?$", "", s)
    for code in CURRENCY_CODES:
        if code in s:
            return code
    return s


def parse_amount_and_currency(text: str) -> tuple:
    """从文本中解析金额和货币代码"""
    # 匹配数字（支持千分位、逗号、小数点）
    m = re.search(r"([\d,]+(?:\.\d+)?)", text)
    if not m:
        return None, None
    amount = float(m.group(1).replace(",", ""))
    currency = normalize_currency(text)
    return amount, currency


async def fetch_live_rates() -> dict:
    """从免费API获取实时汇率"""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                "https://api.exchangerate-api.com/v4/latest/USD",
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("rates", {})
    except Exception:
        pass
    return {}


def register_currency_converter_tool(mcp: FastMCP):
    """注册货币换算工具到MCP服务"""

    @mcp.tool()
    async def currency_converter(amount: str, from_currency: str, to_currency: str) -> str:
        """
        货币换算，支持中英文货币名称，自动识别货币类型。
        支持的货币：人民币(CNY)、美元(USD)、欧元(EUR)、英镑(GBP)、日元(JPY)、港币(HKD)、韩元(KRW)、台币(TWD)、新加坡元(SGD)、澳元(AUD)、加元(CAD)、瑞士法郎(CHF)、印度卢比(INR)、泰铢(THB)、马来西亚林吉特(MY)、菲律宾比索(PHP)、越南盾(VND)

        示例1：currency_converter(amount="100", from_currency="USD", to_currency="CNY")
        示例2：currency_converter(amount="1000", from_currency="美元", to_currency="人民币")
        示例3：currency_converter(amount="50", from_currency="USD", to_currency="JPY")

        Args:
            amount: 要换算的金额数字（字符串格式，支持带逗号千分位）
            from_currency: 源货币代码或中文名称，如 "USD"、"美元"、"人民币"
            to_currency: 目标货币代码或中文名称，如 "CNY"、"日元"、"JPY"
        Returns:
            换算结果，包含详细汇率信息
        """
        try:
            # 解析金额
            amount = float(str(amount).replace(",", ""))

            # 规范化货币代码
            from_code = normalize_currency(from_currency)
            to_code = normalize_currency(to_currency)

            if from_code not in DEFAULT_RATES:
                return f"不支持的源货币：{from_currency}，支持的货币：{', '.join(CURRENCY_NAMES.values())}"
            if to_code not in DEFAULT_RATES:
                return f"不支持的目标货币：{to_currency}，支持的货币：{', '.join(CURRENCY_NAMES.values())}"

            # 尝试获取实时汇率
            live_rates = await fetch_live_rates()
            if live_rates and from_code in live_rates and to_code in live_rates:
                from_rate = live_rates[from_code]
                to_rate = live_rates[to_code]
            else:
                # 使用内置默认汇率
                from_rate = DEFAULT_RATES[from_code]
                to_rate = DEFAULT_RATES[to_code]

            # 换算：先转USD，再转目标货币
            usd_amount = amount / from_rate
            result = usd_amount * to_rate

            from_name = CURRENCY_NAMES.get(from_code, from_code)
            to_name = CURRENCY_NAMES.get(to_code, to_code)

            # 格式化输出
            if result >= 1000:
                result_str = f"{result:,.2f}"
            elif result >= 1:
                result_str = f"{result:.4f}"
            else:
                result_str = f"{result:.6f}"

            rate_from = f"1 {from_code} = {to_rate/from_rate:.4f} {to_code}"
            source_note = "（实时汇率）" if live_rates else "（参考汇率）"

            return (
                f"💱 货币换算结果：\n\n"
                f"{amount:,.2f} {from_name} ({from_code})\n"
                f"= {result_str} {to_name} ({to_code})\n\n"
                f"汇率：{rate_from} {source_note}"
            )

        except ValueError:
            return f"金额格式错误：{amount}，请输入有效数字"
        except Exception as e:
            return f"换算失败：{str(e)}"

    @mcp.tool()
    def list_currencies() -> str:
        """
        列出所有支持的货币种类。

        示例：list_currencies()

        Returns:
            所有支持的货币列表
        """
        lines = ["支持的货币种类："]
        for code in CURRENCY_CODES:
            name = CURRENCY_NAMES.get(code, code)
            lines.append(f"  {code} - {name}")
        return "\n".join(lines)

    @mcp.tool()
    def exchange_rate(base_currency: str, target_currency: str) -> str:
        """
        查询两种货币之间的汇率。

        示例1：exchange_rate(base_currency="USD", target_currency="CNY")
        示例2：exchange_rate(base_currency="欧元", target_currency="人民币")

        Args:
            base_currency: 基准货币代码或名称
            target_currency: 目标货币代码或名称
        Returns:
            汇率信息
        """
        try:
            base = normalize_currency(base_currency)
            target = normalize_currency(target_currency)

            if base not in DEFAULT_RATES:
                return f"不支持的货币：{base_currency}"
            if target not in DEFAULT_RATES:
                return f"不支持的货币：{target_currency}"

            rate = DEFAULT_RATES[target] / DEFAULT_RATES[base]
            base_name = CURRENCY_NAMES.get(base, base)
            target_name = CURRENCY_NAMES.get(target, target)

            return (
                f"📊 当前汇率：\n\n"
                f"1 {base_name} ({base}) = {rate:.4f} {target_name} ({target})\n\n"
                f"基准货币：{base_name} | 目标货币：{target_name}"
            )
        except Exception as e:
            return f"查询失败：{str(e)}"
