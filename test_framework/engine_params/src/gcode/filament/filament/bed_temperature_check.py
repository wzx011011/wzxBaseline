"""
Bed temperature parameters validation for filament settings.
鐑簥娓╁害鍙傛暟鏍￠獙妯″潡

鏍规嵁 filament_parameters_validation.md 2.1.4 Bed temperature 鍒嗙粍
鍖呭惈12涓弬鏁扮殑鏍￠獙閫昏緫
"""

def parse_cool_plate_temp_initial_layer(gcode_content):
    """
    鏍￠獙鍐峰簥鍒濆眰娓╁害鍙傛暟
    鍙傛暟: cool_plate_temp_initial_layer (coInt, 0-100)
    """
    result = {
        "parameter": "cool_plate_temp_initial_layer",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*cool_plate_temp_initial_layer\s*=\s*([0-9]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        try:
            result["value"] = int(matches[0])
            
            # 鏍￠獙鑼冨洿 0-100掳C
            if result["value"] < 0 or result["value"] > 100:
                result["validation"] = False
                result["errors"].append(f"cool_plate_temp_initial_layer {result['value']} out of range (0-100掳C)")
                
        except ValueError:
            result["validation"] = False
            result["errors"].append("cool_plate_temp_initial_layer must be a valid integer")
    
    return result

def parse_cool_plate_temp(gcode_content):
    """
    鏍￠獙鍐峰簥娓╁害鍙傛暟
    鍙傛暟: cool_plate_temp (coInt, 0-100)
    """
    result = {
        "parameter": "cool_plate_temp",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    # 鏌ユ壘鍐峰簥娓╁害璁剧疆锛堟帓闄ゅ垵灞傛俯搴︼級
    pattern = r';.*cool_plate_temp\s*=\s*([0-9]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    # 杩囨护鎺夊寘鍚玦nitial_layer鐨勫尮閰?
    filtered_matches = []
    for match in matches:
        line_pattern = r';.*cool_plate_temp_initial_layer.*' + re.escape(match)
        if not re.search(line_pattern, gcode_content, re.IGNORECASE):
            filtered_matches.append(match)
    
    if filtered_matches:
        result["found"] = True
        try:
            result["value"] = int(filtered_matches[0])
            
            # 鏍￠獙鑼冨洿 0-100掳C
            if result["value"] < 0 or result["value"] > 100:
                result["validation"] = False
                result["errors"].append(f"cool_plate_temp {result['value']} out of range (0-100掳C)")
                
        except ValueError:
            result["validation"] = False
            result["errors"].append("cool_plate_temp must be a valid integer")
    
    return result

def parse_eng_plate_temp_initial_layer(gcode_content):
    """
    鏍￠獙宸ョ▼鏉垮垵灞傛俯搴﹀弬鏁?
    鍙傛暟: eng_plate_temp_initial_layer (coInt, 0-120)
    """
    result = {
        "parameter": "eng_plate_temp_initial_layer",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*eng_plate_temp_initial_layer\s*=\s*([0-9]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        try:
            result["value"] = int(matches[0])
            
            # 鏍￠獙鑼冨洿 0-120掳C
            if result["value"] < 0 or result["value"] > 120:
                result["validation"] = False
                result["errors"].append(f"eng_plate_temp_initial_layer {result['value']} out of range (0-120掳C)")
                
        except ValueError:
            result["validation"] = False
            result["errors"].append("eng_plate_temp_initial_layer must be a valid integer")
    
    return result

def parse_eng_plate_temp(gcode_content):
    """
    鏍￠獙宸ョ▼鏉挎俯搴﹀弬鏁?
    鍙傛暟: eng_plate_temp (coInt, 0-120)
    """
    result = {
        "parameter": "eng_plate_temp",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    # 鏌ユ壘宸ョ▼鏉挎俯搴﹁缃紙鎺掗櫎鍒濆眰娓╁害锛?
    pattern = r';.*eng_plate_temp\s*=\s*([0-9]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    # 杩囨护鎺夊寘鍚玦nitial_layer鐨勫尮閰?
    filtered_matches = []
    for match in matches:
        line_pattern = r';.*eng_plate_temp_initial_layer.*' + re.escape(match)
        if not re.search(line_pattern, gcode_content, re.IGNORECASE):
            filtered_matches.append(match)
    
    if filtered_matches:
        result["found"] = True
        try:
            result["value"] = int(filtered_matches[0])
            
            # 鏍￠獙鑼冨洿 0-120掳C
            if result["value"] < 0 or result["value"] > 120:
                result["validation"] = False
                result["errors"].append(f"eng_plate_temp {result['value']} out of range (0-120掳C)")
                
        except ValueError:
            result["validation"] = False
            result["errors"].append("eng_plate_temp must be a valid integer")
    
    return result

def parse_hot_plate_temp_initial_layer(gcode_content):
    """
    鏍￠獙楂樻俯鏉垮垵灞傛俯搴﹀弬鏁?
    鍙傛暟: hot_plate_temp_initial_layer (coInt, 0-120)
    """
    result = {
        "parameter": "hot_plate_temp_initial_layer",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*hot_plate_temp_initial_layer\s*=\s*([0-9]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        try:
            result["value"] = int(matches[0])
            
            # 鏍￠獙鑼冨洿 0-120掳C
            if result["value"] < 0 or result["value"] > 120:
                result["validation"] = False
                result["errors"].append(f"hot_plate_temp_initial_layer {result['value']} out of range (0-120掳C)")
                
        except ValueError:
            result["validation"] = False
            result["errors"].append("hot_plate_temp_initial_layer must be a valid integer")
    
    return result

def parse_hot_plate_temp(gcode_content):
    """
    鏍￠獙楂樻俯鏉挎俯搴﹀弬鏁?
    鍙傛暟: hot_plate_temp (coInt, 0-120)
    """
    result = {
        "parameter": "hot_plate_temp",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    # 鏌ユ壘楂樻俯鏉挎俯搴﹁缃紙鎺掗櫎鍒濆眰娓╁害锛?
    pattern = r';.*hot_plate_temp\s*=\s*([0-9]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    # 杩囨护鎺夊寘鍚玦nitial_layer鐨勫尮閰?
    filtered_matches = []
    for match in matches:
        line_pattern = r';.*hot_plate_temp_initial_layer.*' + re.escape(match)
        if not re.search(line_pattern, gcode_content, re.IGNORECASE):
            filtered_matches.append(match)
    
    if filtered_matches:
        result["found"] = True
        try:
            result["value"] = int(filtered_matches[0])
            
            # 鏍￠獙鑼冨洿 0-120掳C
            if result["value"] < 0 or result["value"] > 120:
                result["validation"] = False
                result["errors"].append(f"hot_plate_temp {result['value']} out of range (0-120掳C)")
                
        except ValueError:
            result["validation"] = False
            result["errors"].append("hot_plate_temp must be a valid integer")
    
    return result

def parse_textured_plate_temp_initial_layer(gcode_content):
    """
    鏍￠獙绾圭悊鏉垮垵灞傛俯搴﹀弬鏁?
    鍙傛暟: textured_plate_temp_initial_layer (coInt, 0-120)
    """
    result = {
        "parameter": "textured_plate_temp_initial_layer",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*textured_plate_temp_initial_layer\s*=\s*([0-9]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        try:
            result["value"] = int(matches[0])
            
            # 鏍￠獙鑼冨洿 0-120掳C
            if result["value"] < 0 or result["value"] > 120:
                result["validation"] = False
                result["errors"].append(f"textured_plate_temp_initial_layer {result['value']} out of range (0-120掳C)")
                
        except ValueError:
            result["validation"] = False
            result["errors"].append("textured_plate_temp_initial_layer must be a valid integer")
    
    return result

def parse_textured_plate_temp(gcode_content):
    """
    鏍￠獙绾圭悊鏉挎俯搴﹀弬鏁?
    鍙傛暟: textured_plate_temp (coInt, 0-120)
    """
    result = {
        "parameter": "textured_plate_temp",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    # 鏌ユ壘绾圭悊鏉挎俯搴﹁缃紙鎺掗櫎鍒濆眰娓╁害锛?
    pattern = r';.*textured_plate_temp\s*=\s*([0-9]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    # 杩囨护鎺夊寘鍚玦nitial_layer鐨勫尮閰?
    filtered_matches = []
    for match in matches:
        line_pattern = r';.*textured_plate_temp_initial_layer.*' + re.escape(match)
        if not re.search(line_pattern, gcode_content, re.IGNORECASE):
            filtered_matches.append(match)
    
    if filtered_matches:
        result["found"] = True
        try:
            result["value"] = int(filtered_matches[0])
            
            # 鏍￠獙鑼冨洿 0-120掳C
            if result["value"] < 0 or result["value"] > 120:
                result["validation"] = False
                result["errors"].append(f"textured_plate_temp {result['value']} out of range (0-120掳C)")
                
        except ValueError:
            result["validation"] = False
            result["errors"].append("textured_plate_temp must be a valid integer")
    
    return result

def parse_customized_plate_temp_initial_layer(gcode_content):
    """
    鏍￠獙鑷畾涔夋澘鍒濆眰娓╁害鍙傛暟
    鍙傛暟: customized_plate_temp_initial_layer (coInt, 0-120)
    """
    result = {
        "parameter": "customized_plate_temp_initial_layer",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*customized_plate_temp_initial_layer\s*=\s*([0-9]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        try:
            result["value"] = int(matches[0])
            
            # 鏍￠獙鑼冨洿 0-120掳C
            if result["value"] < 0 or result["value"] > 120:
                result["validation"] = False
                result["errors"].append(f"customized_plate_temp_initial_layer {result['value']} out of range (0-120掳C)")
                
        except ValueError:
            result["validation"] = False
            result["errors"].append("customized_plate_temp_initial_layer must be a valid integer")
    
    return result

def parse_customized_plate_temp(gcode_content):
    """
    鏍￠獙鑷畾涔夋澘娓╁害鍙傛暟
    鍙傛暟: customized_plate_temp (coInt, 0-120)
    """
    result = {
        "parameter": "customized_plate_temp",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    # 鏌ユ壘鑷畾涔夋澘娓╁害璁剧疆锛堟帓闄ゅ垵灞傛俯搴︼級
    pattern = r';.*customized_plate_temp\s*=\s*([0-9]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    # 杩囨护鎺夊寘鍚玦nitial_layer鐨勫尮閰?
    filtered_matches = []
    for match in matches:
        line_pattern = r';.*customized_plate_temp_initial_layer.*' + re.escape(match)
        if not re.search(line_pattern, gcode_content, re.IGNORECASE):
            filtered_matches.append(match)
    
    if filtered_matches:
        result["found"] = True
        try:
            result["value"] = int(filtered_matches[0])
            
            # 鏍￠獙鑼冨洿 0-120掳C
            if result["value"] < 0 or result["value"] > 120:
                result["validation"] = False
                result["errors"].append(f"customized_plate_temp {result['value']} out of range (0-120掳C)")
                
        except ValueError:
            result["validation"] = False
            result["errors"].append("customized_plate_temp must be a valid integer")
    
    return result

def parse_epoxy_resin_plate_temp_initial_layer(gcode_content):
    """
    鏍￠獙鐜哀鏍戣剛鏉垮垵灞傛俯搴﹀弬鏁?
    鍙傛暟: epoxy_resin_plate_temp_initial_layer (coInt, 0-80)
    """
    result = {
        "parameter": "epoxy_resin_plate_temp_initial_layer",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    pattern = r';.*epoxy_resin_plate_temp_initial_layer\s*=\s*([0-9]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    if matches:
        result["found"] = True
        try:
            result["value"] = int(matches[0])
            
            # 鏍￠獙鑼冨洿 0-80掳C
            if result["value"] < 0 or result["value"] > 80:
                result["validation"] = False
                result["errors"].append(f"epoxy_resin_plate_temp_initial_layer {result['value']} out of range (0-80掳C)")
                
        except ValueError:
            result["validation"] = False
            result["errors"].append("epoxy_resin_plate_temp_initial_layer must be a valid integer")
    
    return result

def parse_epoxy_resin_plate_temp(gcode_content):
    """
    鏍￠獙鐜哀鏍戣剛鏉挎俯搴﹀弬鏁?
    鍙傛暟: epoxy_resin_plate_temp (coInt, 0-80)
    """
    result = {
        "parameter": "epoxy_resin_plate_temp",
        "found": False,
        "value": None,
        "validation": True,
        "errors": []
    }
    
    import re
    
    # 鏌ユ壘鐜哀鏍戣剛鏉挎俯搴﹁缃紙鎺掗櫎鍒濆眰娓╁害锛?
    pattern = r';.*epoxy_resin_plate_temp\s*=\s*([0-9]+)'
    matches = re.findall(pattern, gcode_content, re.IGNORECASE)
    
    # 杩囨护鎺夊寘鍚玦nitial_layer鐨勫尮閰?
    filtered_matches = []
    for match in matches:
        line_pattern = r';.*epoxy_resin_plate_temp_initial_layer.*' + re.escape(match)
        if not re.search(line_pattern, gcode_content, re.IGNORECASE):
            filtered_matches.append(match)
    
    if filtered_matches:
        result["found"] = True
        try:
            result["value"] = int(filtered_matches[0])
            
            # 鏍￠獙鑼冨洿 0-80掳C
            if result["value"] < 0 or result["value"] > 80:
                result["validation"] = False
                result["errors"].append(f"epoxy_resin_plate_temp {result['value']} out of range (0-80掳C)")
                
        except ValueError:
            result["validation"] = False
            result["errors"].append("epoxy_resin_plate_temp must be a valid integer")
    
    return result

def validate_bed_temperature_group(gcode_content):
    """
    鏍￠獙 Bed temperature 鍒嗙粍鐨勬墍鏈夊弬鏁?
    """
    results = []
    
    # 鍚勭鏉挎潗鐨勫垵灞傛俯搴﹀拰娓╁害
    results.extend([
        parse_cool_plate_temp_initial_layer(gcode_content),
        parse_cool_plate_temp(gcode_content),
        parse_eng_plate_temp_initial_layer(gcode_content),
        parse_eng_plate_temp(gcode_content),
        parse_hot_plate_temp_initial_layer(gcode_content),
        parse_hot_plate_temp(gcode_content),
        parse_textured_plate_temp_initial_layer(gcode_content),
        parse_textured_plate_temp(gcode_content),
        parse_customized_plate_temp_initial_layer(gcode_content),
        parse_customized_plate_temp(gcode_content),
        parse_epoxy_resin_plate_temp_initial_layer(gcode_content),
        parse_epoxy_resin_plate_temp(gcode_content),
    ])
    
    # 娓╁害閫昏緫涓€鑷存€ф鏌?
    plate_types = ['cool', 'eng', 'hot', 'textured', 'customized', 'epoxy_resin']
    for plate_type in plate_types:
        initial_result = None
        normal_result = None
        
        for result in results:
            if result["parameter"] == f"{plate_type}_plate_temp_initial_layer":
                initial_result = result
            elif result["parameter"] == f"{plate_type}_plate_temp":
                normal_result = result
        
        if initial_result and normal_result and initial_result["found"] and normal_result["found"]:
            if initial_result["value"] < normal_result["value"] - 10:
                initial_result["validation"] = False
                initial_result["errors"].append(
                    f"{plate_type}_plate_temp_initial_layer {initial_result['value']} is much lower than {plate_type}_plate_temp {normal_result['value']}"
                )
    
    return results
