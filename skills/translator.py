"""翻译技能 - 支持多种语言互译"""
import re
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("translator")

# 内置翻译字典（离线备用，无需API）
BUILTIN_TRANSLATIONS = {
    "hello": {"zh": "你好", "ja": "こんにちは", "ko": "안녕하세요", "fr": "Bonjour", "de": "Hallo", "es": "Hola", "ru": "Привет"},
    "goodbye": {"zh": "再见", "ja": "さようなら", "ko": "안녕히 가세요", "fr": "Au revoir", "de": "Auf Wiedersehen", "es": "Adiós", "ru": "До свидания"},
    "thank you": {"zh": "谢谢", "ja": "ありがとう", "ko": "감사합니다", "fr": "Merci", "de": "Danke", "es": "Gracias", "ru": "Спасибо"},
    "yes": {"zh": "是", "ja": "はい", "ko": "네", "fr": "Oui", "de": "Ja", "es": "Sí", "ru": "Да"},
    "no": {"zh": "否", "ja": "いいえ", "ko": "아니요", "fr": "Non", "de": "Nein", "es": "No", "ru": "Нет"},
    "good morning": {"zh": "早上好", "ja": "おはよう", "ko": "좋은 아침", "fr": "Bonjour", "de": "Guten Morgen", "es": "Buenos días", "ru": "Доброе утро"},
    "good night": {"zh": "晚安", "ja": "おやすみ", "ko": "잘 자요", "fr": "Bonne nuit", "de": "Gute Nacht", "es": "Buenas noches", "ru": "Спокойной ночи"},
    "how are you": {"zh": "你好吗", "ja": "お元気ですか", "ko": "어떻게 지내세요", "fr": "Comment allez-vous", "de": "Wie geht es Ihnen", "es": "¿Cómo estás", "ru": "Как дела"},
    "i love you": {"zh": "我爱你", "ja": "愛してる", "ko": "사랑해요", "fr": "Je t'aime", "de": "Ich liebe dich", "es": "Te amo", "ru": "Я тебя люблю"},
    "welcome": {"zh": "欢迎", "ja": "ようこそ", "ko": "환영합니다", "fr": "Bienvenue", "de": "Willkommen", "es": "Bienvenido", "ru": "Добро пожаловать"},
}

# 语言名称映射
LANG_NAMES = {
    "zh": "中文", "chinese": "中文",
    "en": "英语", "english": "英语",
    "ja": "日语", "japanese": "日语",
    "ko": "韩语", "korean": "韩语",
    "fr": "法语", "french": "法语",
    "de": "德语", "german": "德语",
    "es": "西班牙语", "spanish": "西班牙语",
    "ru": "俄语", "russian": "俄语",
    "pt": "葡萄牙语", "portuguese": "葡萄牙语",
    "it": "意大利语", "italian": "意大利语",
    "ar": "阿拉伯语", "arabic": "阿拉伯语",
}

LANG_CODES = {v: k for k, v in LANG_NAMES.items()}
LANG_CODES.update({k: k for k in LANG_NAMES.keys()})


def normalize_lang(lang: str) -> str:
    """标准化语言代码"""
    lang = lang.lower().strip()
    return LANG_CODES.get(lang, lang)


@mcp.tool()
def translate(text: str, from_lang: str = "auto", to_lang: str = "zh") -> str:
    """
    翻译文本到指定语言
    
    示例：translate(text="hello", from_lang="en", to_lang="zh")
    
    Args:
        text: 要翻译的文本
        from_lang: 源语言 (en/zh/ja/ko/fr/de/es/ru等，支持中文名或代码)
        to_lang: 目标语言 (en/zh/ja/ko/fr/de/es/ru等)
    
    Returns:
        翻译结果
    """
    try:
        text = text.strip()
        if not text:
            return "翻译内容不能为空"
        
        from_code = normalize_lang(from_lang)
        to_code = normalize_lang(to_lang)
        
        # 查内置词典
        text_lower = text.lower()
        if text_lower in BUILTIN_TRANSLATIONS:
            if from_code == "auto":
                # 尝试识别源语言
                for code, trans in BUILTIN_TRANSLATIONS[text_lower].items():
                    if code != "zh":
                        from_code = code
                        break
            if to_code in BUILTIN_TRANSLATIONS[text_lower]:
                return BUILTIN_TRANSLATIONS[text_lower][to_code]
        
        # 简单规则翻译（数字、时间等）
        simple_result = _simple_translate(text, from_code, to_code)
        if simple_result:
            return simple_result
        
        # 内置词典找不到，返回提示
        return f"【翻译结果】\n{text}\n\n📝 离线词典暂不支持此内容翻译。\n💡 如需完整翻译，请配置翻译API密钥。"
        
    except Exception as e:
        return f"翻译失败: {str(e)}"


def _simple_translate(text: str, from_code: str, to_code: str) -> str:
    """简单翻译规则"""
    # 数字翻译
    numbers = {
        "0": {"zh": "零", "en": "zero", "ja": "ゼロ", "ko": "영"},
        "1": {"zh": "一", "en": "one", "ja": "一", "ko": "하나"},
        "2": {"zh": "二", "en": "two", "ja": "二", "ko": "둘"},
        "3": {"zh": "三", "en": "three", "ja": "三", "ko": "셋"},
        "4": {"zh": "四", "en": "four", "ja": "四", "ko": "넷"},
        "5": {"zh": "五", "en": "five", "ja": "五", "ko": "다섯"},
    }
    
    # 如果全是数字
    if text.isdigit() and text in numbers:
        if to_code in numbers[text]:
            return numbers[text][to_code]
    
    return None


def register_translator_tool(mcp: FastMCP):
    """注册翻译技能"""
    mcp.add_tool(translate)
