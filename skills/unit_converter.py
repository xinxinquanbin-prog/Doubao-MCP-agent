"""单位换算技能 - 支持长度、重量、温度、面积等"""
import re
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("unit_converter")


# ===== 长度换算 =====
LENGTH_UNITS = ["m", "meter", "米", "km", "kilometer", "千米", "cm", "centimeter", "厘米", 
                "mm", "millimeter", "毫米", "mi", "mile", "英里", "ft", "foot", "英尺",
                "in", "inch", "英寸", "yd", "yard", "码"]

LENGTH_TO_M = {
    "m": 1, "meter": 1, "米": 1,
    "km": 1000, "kilometer": 1000, "千米": 1000,
    "cm": 0.01, "centimeter": 0.01, "厘米": 0.01,
    "mm": 0.001, "millimeter": 0.001, "毫米": 0.001,
    "mi": 1609.344, "mile": 1609.344, "英里": 1609.344,
    "ft": 0.3048, "foot": 0.3048, "英尺": 0.3048,
    "in": 0.0254, "inch": 0.0254, "英寸": 0.0254,
    "yd": 0.9144, "yard": 0.9144, "码": 0.9144,
}

# ===== 重量换算 =====
WEIGHT_UNITS = ["kg", "kilogram", "千克", "g", "gram", "克", "mg", "milligram", "毫克",
                "lb", "pound", "磅", "oz", "ounce", "盎司", "t", "ton", "吨"]

WEIGHT_TO_KG = {
    "kg": 1, "kilogram": 1, "千克": 1,
    "g": 0.001, "gram": 0.001, "克": 0.001,
    "mg": 0.000001, "milligram": 0.000001, "毫克": 0.000001,
    "lb": 0.453592, "pound": 0.453592, "磅": 0.453592,
    "oz": 0.0283495, "ounce": 0.0283495, "盎司": 0.0283495,
    "t": 1000, "ton": 1000, "吨": 1000,
}

# ===== 温度换算 =====
def celsius_to_fahrenheit(c: float) -> float:
    return c * 9/5 + 32

def celsius_to_kelvin(c: float) -> float:
    return c + 273.15

def fahrenheit_to_celsius(f: float) -> float:
    return (f - 32) * 5/9

def kelvin_to_celsius(k: float) -> float:
    return k - 273.15

# ===== 面积换算 =====
AREA_UNITS = ["m2", "平方米", "km2", "平方千米", "km²", "hectare", "公顷", "acre", "英亩"]

AREA_TO_M2 = {
    "m2": 1, "平方米": 1,
    "km2": 1000000, "平方千米": 1000000, "km²": 1000000,
    "hectare": 10000, "公顷": 10000,
    "acre": 4046.8564224, "英亩": 4046.8564224,
}

# ===== 体积换算 =====
VOLUME_UNITS = ["L", "liter", "升", "mL", "ml", "毫升", "gallon", "gal", "加仑"]

VOLUME_TO_L = {
    "L": 1, "liter": 1, "升": 1,
    "mL": 0.001, "ml": 0.001, "毫升": 0.001,
    "gallon": 3.78541, "gal": 3.78541, "加仑": 3.78541,
}


def normalize_unit(unit: str) -> str:
    """标准化单位"""
    unit = unit.lower().strip()
    unit_map = {
        "平方千米": "km2", "平方英里": "sq mi", "square meter": "m2",
        "square kilometer": "km2", "liter": "L", "milliliter": "mL",
        " kilogram": "kg", "gram": "g", "milligram": "mg",
        " kilogram": "kg", "ounce": "oz", "pound": "lb",
    }
    return unit_map.get(unit, unit)


def parse_value_unit(text: str):
    """解析数值和单位"""
    text = text.strip()
    
    # 匹配 "100 km" 或 "100km"
    match = re.match(r'^([\d.]+)\s*([a-zA-Z\u4e00-\u9fa5°²³]+)', text)
    if match:
        value = float(match.group(1))
        unit = match.group(2).lower()
        return value, normalize_unit(unit)
    
    # 纯数字，默认是米
    try:
        return float(text), "m"
    except:
        return None, None


@mcp.tool()
def convert_length(value: str, from_unit: str, to_unit: str) -> str:
    """
    长度单位换算
    
    示例：convert_length(value="100 km", from_unit="km", to_unit="m")
    
    Args:
        value: 数值和单位，如 "100 km" 或 "100千米"
        from_unit: 源单位 (m/km/cm/mm/mi/ft/in/yd)
        to_unit: 目标单位 (m/km/cm/mm/mi/ft/in/yd)
    
    Returns:
        换算结果
    """
    try:
        val, from_u = parse_value_unit(value)
        if val is None:
            return f"无法解析数值: {value}"
        
        to_u = normalize_unit(to_unit)
        
        # 转成米
        if from_u in LENGTH_TO_M:
            meters = val * LENGTH_TO_M[from_u]
        else:
            return f"不支持的单位: {from_unit}"
        
        # 转成目标单位
        if to_u in LENGTH_TO_M:
            result = meters / LENGTH_TO_M[to_u]
        else:
            return f"不支持的目标单位: {to_unit}"
        
        # 格式化输出
        if result == int(result):
            result_str = str(int(result))
        else:
            result_str = f"{result:.4f}".rstrip('0').rstrip('.')
        
        return f"{val} {from_u} = {result_str} {to_u}"
        
    except Exception as e:
        return f"长度换算失败: {str(e)}"


@mcp.tool()
def convert_weight(value: str, from_unit: str, to_unit: str) -> str:
    """
    重量单位换算
    
    示例：convert_weight(value="1 kg", from_unit="kg", to_unit="g")
    
    Args:
        value: 数值和单位，如 "1 kg" 或 "1千克"
        from_unit: 源单位 (kg/g/mg/lb/oz/t)
        to_unit: 目标单位 (kg/g/mg/lb/oz/t)
    
    Returns:
        换算结果
    """
    try:
        val, from_u = parse_value_unit(value)
        if val is None:
            return f"无法解析数值: {value}"
        
        to_u = normalize_unit(to_unit)
        
        if from_u in WEIGHT_TO_KG:
            kg = val * WEIGHT_TO_KG[from_u]
        else:
            return f"不支持的单位: {from_unit}"
        
        if to_u in WEIGHT_TO_KG:
            result = kg / WEIGHT_TO_KG[to_u]
        else:
            return f"不支持的目标单位: {to_unit}"
        
        if result == int(result):
            result_str = str(int(result))
        else:
            result_str = f"{result:.4f}".rstrip('0').rstrip('.')
        
        return f"{val} {from_u} = {result_str} {to_u}"
        
    except Exception as e:
        return f"重量换算失败: {str(e)}"


@mcp.tool()
def convert_temperature(value: str, from_unit: str, to_unit: str) -> str:
    """
    温度单位换算
    
    示例：convert_temperature(value="100 C", from_unit="C", to_unit="F")
    
    Args:
        value: 数值和单位，如 "100 C" 或 "100摄氏度"
        from_unit: 源单位 (C/celsius/F/fahrenheit/K/kelvin)
        to_unit: 目标单位 (C/F/K)
    
    Returns:
        换算结果
    """
    try:
        val_str, from_u = parse_value_unit(value)
        if val_str is None:
            return f"无法解析数值: {value}"
        
        val = float(val_str)
        from_u = from_u.lower()
        to_u = to_unit.lower()
        
        # 先转成摄氏度
        if from_u in ["c", "celsius", "摄氏度", "℃"]:
            c = val
        elif from_u in ["f", "fahrenheit", "华氏度", "℉"]:
            c = fahrenheit_to_celsius(val)
        elif from_u in ["k", "kelvin"]:
            c = kelvin_to_celsius(val)
        else:
            return f"不支持的温度单位: {from_unit}"
        
        # 再转成目标单位
        if to_u in ["c", "celsius", "摄氏度", "℃"]:
            result = c
            unit = "°C"
        elif to_u in ["f", "fahrenheit", "华氏度", "℉"]:
            result = celsius_to_fahrenheit(c)
            unit = "°F"
        elif to_u in ["k", "kelvin"]:
            result = celsius_to_kelvin(c)
            unit = "K"
        else:
            return f"不支持的温度单位: {to_unit}"
        
        if result == int(result):
            result_str = str(int(result))
        else:
            result_str = f"{result:.2f}"
        
        return f"{val}{from_u} = {result_str}{unit}"
        
    except Exception as e:
        return f"温度换算失败: {str(e)}"


@mcp.tool()
def convert_area(value: str, from_unit: str, to_unit: str) -> str:
    """
    面积单位换算
    
    示例：convert_area(value="1 hectare", from_unit="hectare", to_unit="m2")
    
    Args:
        value: 数值和单位，如 "1 公顷"
        from_unit: 源单位 (m2/km2/hectare/acre)
        to_unit: 目标单位 (m2/km2/hectare/acre)
    
    Returns:
        换算结果
    """
    try:
        val, from_u = parse_value_unit(value)
        if val is None:
            return f"无法解析数值: {value}"
        
        to_u = normalize_unit(to_unit)
        
        if from_u in AREA_TO_M2:
            m2 = val * AREA_TO_M2[from_u]
        else:
            return f"不支持的面积单位: {from_unit}"
        
        if to_u in AREA_TO_M2:
            result = m2 / AREA_TO_M2[to_u]
        else:
            return f"不支持的目标单位: {to_unit}"
        
        if result == int(result):
            result_str = str(int(result))
        else:
            result_str = f"{result:.4f}".rstrip('0').rstrip('.')
        
        return f"{val} {from_u} = {result_str} {to_u}"
        
    except Exception as e:
        return f"面积换算失败: {str(e)}"


@mcp.tool()
def convert_volume(value: str, from_unit: str, to_unit: str) -> str:
    """
    体积单位换算
    
    示例：convert_volume(value="1 gallon", from_unit="gallon", to_unit="L")
    
    Args:
        value: 数值和单位，如 "1 加仑"
        from_unit: 源单位 (L/mL/gallon)
        to_unit: 目标单位 (L/mL/gallon)
    
    Returns:
        换算结果
    """
    try:
        val, from_u = parse_value_unit(value)
        if val is None:
            return f"无法解析数值: {value}"
        
        to_u = normalize_unit(to_unit)
        
        if from_u in VOLUME_TO_L:
            liters = val * VOLUME_TO_L[from_u]
        else:
            return f"不支持的体积单位: {from_unit}"
        
        if to_u in VOLUME_TO_L:
            result = liters / VOLUME_TO_L[to_u]
        else:
            return f"不支持的目标单位: {to_unit}"
        
        if result == int(result):
            result_str = str(int(result))
        else:
            result_str = f"{result:.4f}".rstrip('0').rstrip('.')
        
        return f"{val} {from_u} = {result_str} {to_u}"
        
    except Exception as e:
        return f"体积换算失败: {str(e)}"


def register_unit_converter_tool(mcp: FastMCP):
    """注册单位换算技能"""
    mcp.add_tool(convert_length)
    mcp.add_tool(convert_weight)
    mcp.add_tool(convert_temperature)
    mcp.add_tool(convert_area)
    mcp.add_tool(convert_volume)
