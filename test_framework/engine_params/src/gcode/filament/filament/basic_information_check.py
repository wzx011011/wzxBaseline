"""
Basic information parameters validation for filament settings.
鑰楁潗鍩虹淇℃伅鍙傛暟鏍￠獙妯″潡

鏍规嵁 filament_parameters_validation.md 2.1.1 Basic information 鍒嗙粍
鍖呭惈19涓弬鏁扮殑鏍￠獙閫昏緫
"""

def parse_filament_type(gcode_content):
    """
    鏍￠獙鑰楁潗绫诲瀷鍙傛暟
    鍙傛暟: filament_type (coString)
    """
    result = {
        "parameter": "filament_type",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    # 鏌ユ壘 filament_type 鐩稿叧鐨?G-code 娉ㄩ噴鎴栬缃?
    import re
    
    # 鍦ㄦ敞閲婁腑鏌ユ壘 filament_type
    pattern = r';.*filament_type\s*=\s*([^\s;]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        result["value"] = matches[0].strip('"\'')
        
        # 鏍￠獙鑰楁潗绫诲瀷涓嶈兘涓虹┖
        if not result["value"]:
            result["validation"] = False
            result["errors"].append("filament_type cannot be empty")
    
    return result

def parse_filament_colour(gcode_content):
    """
    鏍￠獙鑰楁潗棰滆壊鍙傛暟
    鍙傛暟: filament_colour (coString)
    """
    result = {
        "parameter": "filament_colour",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    # 鏌ユ壘鑰楁潗棰滆壊璁剧疆
    pattern = r';.*filament_colour\s*=\s*([^\n;]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        result["value"] = matches[0].strip('"\'')
        
        # 鍩烘湰鏍￠獙锛氶鑹插€煎簲璇ユ槸鏈夋晥鐨勯鑹茶〃绀猴紙鍙互鏄疪GB銆佸崄鍏繘鍒舵垨棰滆壊鍚嶏級
        if result["value"]:
            # 妫€鏌ュ崄鍏繘鍒堕鑹叉牸寮?(#RRGGBB)
            hex_pattern = r'^#[0-9A-Fa-f]{6}$'
            if not re.match(hex_pattern, result["value"]):
                # 濡傛灉涓嶆槸鍗佸叚杩涘埗锛屽彲鑳芥槸棰滆壊鍚嶏紝鏆傛椂璁や负鏈夋晥
                pass
    
    return result

def parse_filament_diameter(gcode_content):
    """
    鏍￠獙鑰楁潗鐩村緞鍙傛暟
    鍙傛暟: filament_diameter (coFloat, 1.5-4.0)
    """
    result = {
        "parameter": "filament_diameter", 
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    # 鏌ユ壘 filament_diameter
    pattern = r';.*filament_diameter\s*=\s*([0-9.]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        try:
            result["value"] = float(matches[0])
            
            # 鏍￠獙鑼冨洿 1.5-4.0 mm
            if result["value"] < 1.5 or result["value"] > 4.0:
                result["validation"] = False
                result["errors"].append(f"filament_diameter {result['value']} out of range (1.5-4.0 mm)")
                
        except ValueError:
            result["validation"] = False
            result["errors"].append("filament_diameter must be a valid number")
    
    return result

def parse_filament_flow_ratio(gcode_content):
    """
    鏍￠獙娴侀噺姣斿弬鏁?
    鍙傛暟: filament_flow_ratio (coFloat, 0.5-1.5)
    """
    result = {
        "parameter": "filament_flow_ratio",
        "found": False, 
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*filament_flow_ratio\s*=\s*([0-9.]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        try:
            result["value"] = float(matches[0])
            
            # 鏍￠獙鑼冨洿 0.5-1.5
            if result["value"] < 0.5 or result["value"] > 1.5:
                result["validation"] = False
                result["errors"].append(f"filament_flow_ratio {result['value']} out of range (0.5-1.5)")
                
        except ValueError:
            result["validation"] = False
            result["errors"].append("filament_flow_ratio must be a valid number")
    
    return result

def parse_required_nozzle_hrc(gcode_content):
    """
    鏍￠獙鍠峰槾纭害瑕佹眰鍙傛暟
    鍙傛暟: required_nozzle_HRC (coInt, 0-100)
    """
    result = {
        "parameter": "required_nozzle_HRC",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*required_nozzle_HRC\s*=\s*([0-9]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        try:
            result["value"] = int(matches[0])
            
            # 鏍￠獙鑼冨洿 0-100
            if result["value"] < 0 or result["value"] > 100:
                result["validation"] = False
                result["errors"].append(f"required_nozzle_HRC {result['value']} out of range (0-100)")
                
        except ValueError:
            result["validation"] = False
            result["errors"].append("required_nozzle_HRC must be a valid integer")
    
    return result

def parse_filament_density(gcode_content):
    """
    鏍￠獙鑰楁潗瀵嗗害鍙傛暟
    鍙傛暟: filament_density (coFloat, 0.5-2.5 g/cm鲁)
    """
    result = {
        "parameter": "filament_density",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*filament_density\s*=\s*([0-9.]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        try:
            result["value"] = float(matches[0])
            
            # 鏍￠獙鑼冨洿 0.5-2.5 g/cm鲁
            if result["value"] < 0.5 or result["value"] > 2.5:
                result["validation"] = False
                result["errors"].append(f"filament_density {result['value']} out of range (0.5-2.5 g/cm鲁)")
                
        except ValueError:
            result["validation"] = False
            result["errors"].append("filament_density must be a valid number")
    
    return result

def parse_nozzle_temperature_range(gcode_content):
    """
    鏍￠獙鎺ㄨ崘鍠峰槾娓╁害鑼冨洿鍙傛暟
    鍙傛暟: nozzle_temperature_range_low, nozzle_temperature_range_high (coFloat, 0-300)
    """
    result = {
        "parameter": "nozzle_temperature_range",
        "found": False,
        "value": {"low": None, "high": None},
        "validation": True,
        "errors": []
    }
    
    import re
    
    # 鏌ユ壘娓╁害鑼冨洿
    low_pattern = r';.*nozzle_temperature_range_low\s*=\s*([0-9.]+)'
    high_pattern = r';.*nozzle_temperature_range_high\s*=\s*([0-9.]+)'
    
    low_matches = re.findall(low_pattern, gcode_content, re.IGNORECASE)
    high_matches = re.findall(high_pattern, gcode_content, re.IGNORECASE)
    
    if low_matches or high_matches:
        result["found"] = True
        
        try:
            if low_matches:
                result["value"]["low"] = float(low_matches[0])
                if result["value"]["low"] < 0 or result["value"]["low"] > 300:
                    result["validation"] = False
                    result["errors"].append(f"nozzle_temperature_range_low {result['value']['low']} out of range (0-300)")
            
            if high_matches:
                result["value"]["high"] = float(high_matches[0])
                if result["value"]["high"] < 0 or result["value"]["high"] > 300:
                    result["validation"] = False
                    result["errors"].append(f"nozzle_temperature_range_high {result['value']['high']} out of range (0-300)")
            
            # 鏍￠獙 low <= high
            if result["value"]["low"] and result["value"]["high"]:
                if result["value"]["low"] > result["value"]["high"]:
                    result["validation"] = False
                    result["errors"].append(f"nozzle_temperature_range_low {result['value']['low']} > high {result['value']['high']}")
                    
        except ValueError:
            result["validation"] = False
            result["errors"].append("nozzle_temperature_range values must be valid numbers")
    
    return result

def parse_enable_pressure_advance(gcode_content):
    """
    鏍￠獙鍘嬪姏琛ュ伩鍚敤鍙傛暟
    鍙傛暟: enable_pressure_advance (coBool)
    """
    result = {
        "parameter": "enable_pressure_advance",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*enable_pressure_advance\s*=\s*(true|false|1|0)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        value_str = matches[0].lower()
        result["value"] = value_str in ['true', '1']
    
    return result

def parse_filament_soluble(gcode_content):
    """
    鏍￠獙鍙憾鎬ц€楁潗鏍囪鍙傛暟
    鍙傛暟: filament_soluble (coBool)
    """
    result = {
        "parameter": "filament_soluble",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*filament_soluble\s*=\s*(true|false|1|0)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        value_str = matches[0].lower()
        result["value"] = value_str in ['true', '1']
    
    return result

def parse_filament_is_support(gcode_content):
    """
    鏍￠獙鏀拺鑰楁潗鏍囪鍙傛暟
    鍙傛暟: filament_is_support (coBool)
    """
    result = {
        "parameter": "filament_is_support",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*filament_is_support\s*=\s*(true|false|1|0)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        value_str = matches[0].lower()
        result["value"] = value_str in ['true', '1']
    
    return result

def parse_filament_vendor(gcode_content):
    """
    鏍￠獙鑰楁潗鍘傚晢鍙傛暟
    鍙傛暟: filament_vendor (coString)
    """
    result = {
        "parameter": "filament_vendor",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*filament_vendor\s*=\s*([^\n;]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        result["value"] = matches[0].strip('"\'')
    
    return result

def parse_default_filament_colour(gcode_content):
    """
    校验耗材颜色参数
    参数: default_filament_colour (coString)
    """
    result = {
        "parameter": "default_filament_colour",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    # 只匹配 default_filament_colour，因为这是G-code中实际输出的参数名
    pattern = r';.*default_filament_colour\s*=\s*([^\n;]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        result["value"] = matches[0].strip('"\'')
        
        # 简单的颜色格式检查
        color_value = result["value"]
        if color_value and not (color_value.startswith('#') or color_value.lower() in ['red', 'blue', 'green', 'black', 'white']):
            result["errors"].append(f"default_filament_colour '{color_value}' may not be a valid color format")
    
    return result

def parse_pressure_advance(gcode_content):
    """
    校验压力补偿值参数
    参数: pressure_advance (coFloat, 0.0-2.0)
    
    支持多种G-code格式:
    1. M900 K值 (Marlin Linear Advance)
    2. SET_PRESSURE_ADVANCE ADVANCE=值 (Klipper) 
    3. M572 D0 S值 (RepRap firmware)
    4. 注释中的 pressure_advance=值
    """
    result = {
        "parameter": "pressure_advance",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    # 多种pressure advance命令模式，按优先级排序
    patterns = [
        # Marlin Linear Advance: M900 K0.02
        (r'M900\s+K([0-9.]+)', "M900 K命令"),
        # Klipper: SET_PRESSURE_ADVANCE ADVANCE=0.02  
        (r'SET_PRESSURE_ADVANCE\s+ADVANCE=([0-9.]+)', "Klipper SET_PRESSURE_ADVANCE命令"),
        # RepRap firmware: M572 D0 S0.02
        (r'M572\s+D\d+\s+S([0-9.]+)', "RepRap M572命令"),
        # 注释中的配置: ; pressure_advance = 0.02
        (r';.*pressure_advance\s*=\s*([0-9.]+)', "注释配置"),
    ]
    
    found_values = []
    
    for pattern, description in patterns:
        matches = re.findall(pattern, gcode_content, re.IGNORECASE)
        if matches:
            for match in matches:
                try:
                    value = float(match)
                    found_values.append((value, description))
                except ValueError:
                    result["errors"].append(f"Invalid pressure_advance value in {description}: {match}")
    
    if found_values:
        result["found"] = True
        # 使用最后一个找到的值（通常是最终设置）
        result["value"], source = found_values[-1]
        result["source"] = source
        
        # 校验范围 0.0-2.0
        if result["value"] < 0.0 or result["value"] > 2.0:
            result["validation"] = False
            result["errors"].append(f"pressure_advance {result['value']} out of range (0.0-2.0)")
    else:
        # 如果没有找到任何命令，可能是被禁用或设为0
        # 检查是否有M900 K0或类似的禁用命令
        disable_patterns = [
            r'M900\s+K0(?:\.0*)?(?:\s|$)',  # M900 K0
            r'SET_PRESSURE_ADVANCE\s+ADVANCE=0(?:\.0*)?(?:\s|$)',  # SET_PRESSURE_ADVANCE ADVANCE=0
            r'M572\s+D\d+\s+S0(?:\.0*)?(?:\s|$)',  # M572 D0 S0
        ]
        
        for pattern in disable_patterns:
            if re.search(pattern, gcode_content, re.IGNORECASE):
                result["found"] = True
                result["value"] = 0.0
                result["source"] = "禁用命令"
                break
    
    return result

def parse_filament_cost(gcode_content):
    """
    鏍￠獙鑰楁潗鎴愭湰鍙傛暟
    鍙傛暟: filament_cost (coFloat, 0.0-1000.0)
    """
    result = {
        "parameter": "filament_cost",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*filament_cost\s*=\s*([0-9.]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        try:
            result["value"] = float(matches[0])
            
            # 鏍￠獙鑼冨洿 0.0-1000.0
            if result["value"] < 0.0 or result["value"] > 1000.0:
                result["validation"] = False
                result["errors"].append(f"filament_cost {result['value']} out of range (0.0-1000.0)")
                
        except ValueError:
            result["validation"] = False
            result["errors"].append("filament_cost must be a valid number")
    
    return result

def validate_basic_information_group(gcode_content):
    """
    鏍￠獙 Basic information 鍒嗙粍鐨勬墍鏈夊弬鏁?
    """
    results = []
    
    # 鏍稿績鍙傛暟鏍￠獙
    results.append(parse_filament_type(gcode_content))
    results.append(parse_filament_diameter(gcode_content))
    results.append(parse_filament_flow_ratio(gcode_content))
    results.append(parse_required_nozzle_hrc(gcode_content))
    results.append(parse_filament_density(gcode_content))
    results.append(parse_nozzle_temperature_range(gcode_content))
    
    # 甯冨皵鍙傛暟鏍￠獙
    results.append(parse_enable_pressure_advance(gcode_content))
    results.append(parse_filament_soluble(gcode_content))
    results.append(parse_filament_is_support(gcode_content))
    
    return results

def parse_compatible_printers(gcode_content):
    """
    鏍￠獙鍏煎鐨勬墦鍗版満鍒楄〃
    鍙傛暟: compatible_printers (coString)
    """
    result = {
        "parameter": "compatible_printers",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*compatible_printers\s*=\s*([^\n;]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        result["value"] = matches[0].strip('"\'')
    
    return result

def parse_compatible_printers_condition(gcode_content):
    """
    鏍￠獙鎵撳嵃鏈哄吋瀹规€ф潯浠?
    鍙傛暟: compatible_printers_condition (coString)
    """
    result = {
        "parameter": "compatible_printers_condition",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*compatible_printers_condition\s*=\s*([^\n;]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        result["value"] = matches[0].strip('"\'')
    
    return result

def parse_compatible_prints(gcode_content):
    """
    鏍￠獙鍏煎鐨勬墦鍗伴璁?
    鍙傛暟: compatible_prints (coString)
    """
    result = {
        "parameter": "compatible_prints",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*compatible_prints\s*=\s*([^\n;]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        result["value"] = matches[0].strip('"\'')
    
    return result

def parse_compatible_prints_condition(gcode_content):
    """
    鏍￠獙鎵撳嵃棰勮鍏煎鎬ф潯浠?
    鍙傛暟: compatible_prints_condition (coString)
    """
    result = {
        "parameter": "compatible_prints_condition",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*compatible_prints_condition\s*=\s*([^\n;]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        result["value"] = matches[0].strip('"\'')
    
    return result

def parse_inherits(gcode_content):
    """
    鏍￠獙缁ф壙鐨勮€楁潗閰嶇疆
    鍙傛暟: inherits (coString)
    """
    result = {
        "parameter": "inherits",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*inherits\s*=\s*([^\n;]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        result["value"] = matches[0].strip('"\'')
    
    return result

def parse_start_filament_gcode(gcode_content):
    """
    鏍￠獙寮€濮嬭€楁潗G浠ｇ爜
    鍙傛暟: start_filament_gcode (coString)
    """
    result = {
        "parameter": "start_filament_gcode",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*start_filament_gcode\s*=\s*([^\n;]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        result["value"] = matches[0].strip('"\'')
    
    return result

def parse_end_filament_gcode(gcode_content):
    """
    鏍￠獙缁撴潫鑰楁潗G浠ｇ爜
    鍙傛暟: end_filament_gcode (coString)
    """
    result = {
        "parameter": "end_filament_gcode",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*end_filament_gcode\s*=\s*([^\n;]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        result["value"] = matches[0].strip('"\'')
    
    return result

def parse_compatible_machine(gcode_content):
    """
    鏍￠獙鍏煎鐨勬満鍣?
    鍙傛暟: compatible_machine (coString)
    """
    result = {
        "parameter": "compatible_machine",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*compatible_machine\s*=\s*([^\n;]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        result["value"] = matches[0].strip('"\'')
    
    return result

def parse_compatible_machine_condition(gcode_content):
    """
    鏍￠獙鏈哄櫒鍏煎鎬ф潯浠?
    鍙傛暟: compatible_machine_condition (coString)
    """
    result = {
        "parameter": "compatible_machine_condition",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*compatible_machine_condition\s*=\s*([^\n;]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        result["value"] = matches[0].strip('"\'')
    
    return result

def parse_filament_notes(gcode_content):
    """
    鏍￠獙鑰楁潗澶囨敞
    鍙傛暟: filament_notes (coString)
    """
    result = {
        "parameter": "filament_notes",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*filament_notes\s*=\s*([^\n;]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        result["value"] = matches[0].strip('"\'')
    
    return result

def parse_filament_toolchange_delay(gcode_content):
    """
    鏍￠獙鎹㈡枡寤惰繜鏃堕棿
    鍙傛暟: filament_toolchange_delay (coFloat)
    """
    result = {
        "parameter": "filament_toolchange_delay",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*filament_toolchange_delay\s*=\s*([0-9.]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        try:
            result["value"] = float(matches[0])
            
            # 鏍￠獙鑼冨洿 0.0-60.0绉?
            if result["value"] < 0.0 or result["value"] > 60.0:
                result["validation"] = False
                result["errors"].append(f"filament_toolchange_delay {result['value']} out of range (0.0-60.0 seconds)")
                
        except ValueError:
            result["validation"] = False
            result["errors"].append("filament_toolchange_delay must be a valid number")
    
    return result
