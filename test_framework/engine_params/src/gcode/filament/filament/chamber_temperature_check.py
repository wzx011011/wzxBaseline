"""
Print chamber temperature parameters validation for filament settings.
鎵撳嵃鑵斿娓╁害鍙傛暟鏍￠獙妯″潡

鏍规嵁 filament_parameters_validation.md 2.1.2 Print chamber temperature 鍒嗙粍
鍖呭惈3涓弬鏁扮殑鏍￠獙閫昏緫
"""

def parse_chamber_temperature(gcode_content):
    """
    鏍￠獙鎵撳嵃鑵斿娓╁害鍙傛暟
    鍙傛暟: chamber_temperature (coFloat, 0.0-150.0)
    """
    result = {
        "parameter": "chamber_temperature",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    # 鏌ユ壘鑵斿娓╁害璁剧疆
    pattern = r';.*chamber_temperature\s*=\s*([0-9.]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        try:
            result["value"] = float(matches[0])
            
            # 鏍￠獙鑼冨洿 0.0-150.0掳C
            if result["value"] < 0.0 or result["value"] > 150.0:
                result["validation"] = False
                result["errors"].append(f"chamber_temperature {result['value']} out of range (0.0-150.0掳C)")
                
        except ValueError:
            result["validation"] = False
            result["errors"].append("chamber_temperature must be a valid number")
    
    return result

def parse_activate_chamber_temp_control(gcode_content):
    """
    鏍￠獙鑵斿娓╁害鎺у埗鍚敤鍙傛暟
    鍙傛暟: activate_chamber_temp_control (coBool)
    """
    result = {
        "parameter": "activate_chamber_temp_control",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*activate_chamber_temp_control\s*=\s*(true|false|1|0)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        value_str = matches[0].lower()
        result["value"] = value_str in ['true', '1']
        
        # 鍙互娣诲姞閫昏緫妫€鏌ワ細濡傛灉鍚敤浜嗚厰瀹ゆ俯搴︽帶鍒讹紝chamber_temperature 搴旇 > 0
    
    return result

def parse_activate_chamber_layer(gcode_content):
    """
    鏍￠獙鑵斿鎺у埗婵€娲诲眰鏁板弬鏁?
    鍙傛暟: activate_chamber_layer (coInt, 0-10000)
    """
    result = {
        "parameter": "activate_chamber_layer",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*activate_chamber_layer\s*=\s*([0-9]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        try:
            result["value"] = int(matches[0])
            
            # 鏍￠獙鑼冨洿 0-10000
            if result["value"] < 0 or result["value"] > 10000:
                result["validation"] = False
                result["errors"].append(f"activate_chamber_layer {result['value']} out of range (0-10000)")
                
        except ValueError:
            result["validation"] = False
            result["errors"].append("activate_chamber_layer must be a valid integer")
    
    return result

def validate_chamber_temperature_group(gcode_content):
    """
    鏍￠獙 Print chamber temperature 鍒嗙粍鐨勬墍鏈夊弬鏁?
    """
    results = []
    
    # 鑵斿娓╁害鍙傛暟鏍￠獙
    chamber_temp = parse_chamber_temperature(gcode_content)
    activate_control = parse_activate_chamber_temp_control(gcode_content)
    activate_layer = parse_activate_chamber_layer(gcode_content)
    
    results.extend([chamber_temp, activate_control, activate_layer])
    
    # 閫昏緫涓€鑷存€ф鏌?
    if activate_control["found"] and activate_control["value"] and chamber_temp["found"]:
        if chamber_temp["value"] == 0:
            chamber_temp["validation"] = False
            chamber_temp["errors"].append("chamber_temperature should be > 0 when activate_chamber_temp_control is enabled")
    
    return results
