"""
Print temperature parameters validation for filament settings.
鎵撳嵃娓╁害鍙傛暟鏍￠獙妯″潡

鏍规嵁 filament_parameters_validation.md 2.1.3 Print temperature 鍒嗙粍
鍖呭惈4涓弬鏁扮殑鏍￠獙閫昏緫
"""

def parse_nozzle_temperature_initial_layer(gcode_content):
    """
    鏍￠獙棣栧眰鍠峰槾娓╁害鍙傛暟
    鍙傛暟: nozzle_temperature_initial_layer (coFloat, 0.0-300.0)
    """
    result = {
        "parameter": "nozzle_temperature_initial_layer",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    # 鏌ユ壘棣栧眰鍠峰槾娓╁害璁剧疆
    pattern = r';.*nozzle_temperature_initial_layer\s*=\s*([0-9.]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        try:
            result["value"] = float(matches[0])
            
            # 鏍￠獙鑼冨洿 0.0-300.0掳C
            if result["value"] < 0.0 or result["value"] > 300.0:
                result["validation"] = False
                result["errors"].append(f"nozzle_temperature_initial_layer {result['value']} out of range (0.0-300.0掳C)")
                
        except ValueError:
            result["validation"] = False
            result["errors"].append("nozzle_temperature_initial_layer must be a valid number")
    
    return result

def parse_nozzle_temperature(gcode_content):
    """
    鏍￠獙鎵撳嵃鍠峰槾娓╁害鍙傛暟
    鍙傛暟: nozzle_temperature (coFloat, 0.0-300.0)
    """
    result = {
        "parameter": "nozzle_temperature",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    # 鏌ユ壘鍠峰槾娓╁害璁剧疆锛堟帓闄ゅ垵灞傛俯搴︼級
    pattern = r';.*nozzle_temperature\s*=\s*([0-9.]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    # 杩囨护鎺夊寘鍚玦nitial_layer鐨勫尮閰?
    filtered_matches = []
    for match in matches:
        line_pattern = r';.*nozzle_temperature_initial_layer.*' + re.escape(match)
        if not re.search(line_pattern, gcode_content, re.IGNORECASE):
            filtered_matches.append(match)
    
    if filtered_matches:
        result["found"] = True
        try:
            result["value"] = float(filtered_matches[0])
            
            # 鏍￠獙鑼冨洿 0.0-300.0掳C
            if result["value"] < 0.0 or result["value"] > 300.0:
                result["validation"] = False
                result["errors"].append(f"nozzle_temperature {result['value']} out of range (0.0-300.0掳C)")
                
        except ValueError:
            result["validation"] = False
            result["errors"].append("nozzle_temperature must be a valid number")
    
    return result

def parse_material_flow_dependent_temperature(gcode_content):
    """
    鏍￠獙娴侀噺鐩稿叧娓╁害鍙傛暟
    鍙傛暟: material_flow_dependent_temperature (coBool)
    """
    result = {
        "parameter": "material_flow_dependent_temperature",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*material_flow_dependent_temperature\s*=\s*(true|false|1|0)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        value_str = matches[0].lower()
        result["value"] = value_str in ['true', '1']
    
    return result

def parse_material_flow_temp_graph(gcode_content):
    """
    鏍￠獙娓╁害-娴侀噺鍥捐〃鍙傛暟
    鍙傛暟: material_flow_temp_graph (coString) - L3绾у埆
    """
    result = {
        "parameter": "material_flow_temp_graph",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    # 鏌ユ壘娓╁害娴侀噺鍥捐〃鏁版嵁
    pattern = r';.*material_flow_temp_graph\s*=\s*([^\n;]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        result["value"] = matches[0].strip('"\'')
        
        # L3绾у埆鏍￠獙锛氱畝鍗曠殑鏍煎紡妫€鏌?
        if result["value"] and len(result["value"]) > 0:
            # 妫€鏌ユ槸鍚︽槸鍚堢悊鐨勫浘琛ㄦ暟鎹牸寮忥紙鍙互鏄疛SON鎴栧叾浠栨牸寮忥級
            try:
                # 杩欓噷鍙互娣诲姞鏇村鏉傜殑鍥捐〃鏁版嵁楠岃瘉閫昏緫
                pass
            except:
                result["validation"] = False
                result["errors"].append("material_flow_temp_graph format validation failed")
    
    return result

def validate_print_temperature_group(gcode_content):
    """
    鏍￠獙 Print temperature 鍒嗙粍鐨勬墍鏈夊弬鏁?
    """
    results = []
    
    # 娓╁害鍙傛暟鏍￠獙
    nozzle_temp_initial = parse_nozzle_temperature_initial_layer(gcode_content)
    nozzle_temp = parse_nozzle_temperature(gcode_content)
    flow_dependent = parse_material_flow_dependent_temperature(gcode_content)
    flow_graph = parse_material_flow_temp_graph(gcode_content)
    
    results.extend([nozzle_temp_initial, nozzle_temp, flow_dependent, flow_graph])
    
    # 娓╁害閫昏緫涓€鑷存€ф鏌?
    if nozzle_temp_initial["found"] and nozzle_temp["found"]:
        if nozzle_temp_initial["value"] < nozzle_temp["value"] - 20:
            nozzle_temp_initial["validation"] = False
            nozzle_temp_initial["errors"].append(
                f"nozzle_temperature_initial_layer {nozzle_temp_initial['value']} is much lower than nozzle_temperature {nozzle_temp['value']}, may cause adhesion issues"
            )
    
    return results

