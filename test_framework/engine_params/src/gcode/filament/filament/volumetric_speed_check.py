"""
Volumetric speed limitation parameters validation for filament settings.
浣撶Н閫熷害闄愬埗鍙傛暟鏍￠獙妯″潡

鏍规嵁 filament_parameters_validation.md 2.1.5 Volumetric speed limitation 鍒嗙粍
鍖呭惈1涓弬鏁扮殑鏍￠獙閫昏緫
"""

def parse_filament_max_volumetric_speed(gcode_content):
    """
    鏍￠獙鏈€澶т綋绉€熷害鍙傛暟
    鍙傛暟: filament_max_volumetric_speed (coFloat, 0.0-100.0)
    """
    result = {
        "parameter": "filament_max_volumetric_speed",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    # 鏌ユ壘鏈€澶т綋绉€熷害璁剧疆
    pattern = r';.*filament_max_volumetric_speed\s*=\s*([0-9.]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        try:
            result["value"] = float(matches[0])
            
            # 鏍￠獙鑼冨洿 0.0-100.0 mm鲁/s
            if result["value"] < 0.0 or result["value"] > 100.0:
                result["validation"] = False
                result["errors"].append(f"filament_max_volumetric_speed {result['value']} out of range (0.0-100.0 mm鲁/s)")
            
            # 鍚堢悊鎬ф鏌ワ細璀﹀憡杩囬珮鎴栬繃浣庣殑鍊?
            if result["value"] > 50.0:
                result["errors"].append(f"filament_max_volumetric_speed {result['value']} is very high, may cause print quality issues")
            elif result["value"] < 1.0 and result["value"] > 0:
                result["errors"].append(f"filament_max_volumetric_speed {result['value']} is very low, may cause extremely slow printing")
                
        except ValueError:
            result["validation"] = False
            result["errors"].append("filament_max_volumetric_speed must be a valid number")
    
    return result

def validate_volumetric_speed_group(gcode_content):
    """
    鏍￠獙 Volumetric speed limitation 鍒嗙粍鐨勬墍鏈夊弬鏁?
    """
    results = []
    
    # 浣撶Н閫熷害闄愬埗鍙傛暟鏍￠獙
    results.append(parse_filament_max_volumetric_speed(gcode_content))
    
    return results
