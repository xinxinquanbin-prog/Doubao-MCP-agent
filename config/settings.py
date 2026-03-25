"""全局配置文件"""
import ast 
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 天气API配置（Open-Meteo 免费无密钥）
    GEOCODING_API_URL: str = "https://geocoding-api.open-meteo.com/v1/search"
    WEATHER_API_URL: str = "https://api.open-meteo.com/v1/forecast"
    API_TIMEOUT: int = 10  # 接口超时时间（秒）
    
    # 计算器支持的运算符
    ALLOWED_OPERATORS: set = {
        ast.Add, ast.Sub, ast.Mult, ast.Div,
        ast.Pow, ast.USub, ast.UAdd
    }
    
    # 天气代码映射（中文描述）
    WEATHER_CODE_MAP: dict = {
        0: "晴",
        1: "大部晴朗",
        2: "多云",
        3: "阴天",
        45: "有雾",
        48: "凝露",
        51: "毛毛雨(轻度)",
        53: "毛毛雨(中度)",
        55: "毛毛雨(重度)",
        61: "小雨",
        63: "中雨",
        65: "大雨",
        71: "小雪",
        73: "中雪",
        75: "大雪",
        80: "阵雨",
        81: "强阵雨",
        82: "极端阵雨",
        95: "雷暴",
        96: "雷暴伴轻度冰雹",
        99: "雷暴伴重度冰雹"
    }

settings = Settings()
