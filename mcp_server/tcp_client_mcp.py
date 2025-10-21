"""
TCP客户端MCP工具
每次调用时连接到本地12345端口的TCP服务器，发送JSON命令后断开连接
"""

from ast import Num
import os
import sys
import socket
import json
import time
import psutil
import subprocess
from typing import Dict, Any, Optional

import cv2
from PIL import Image
import pyautogui

current_app_id = None

def gen_respone(code: int, error: str, payload: Dict[str, Any] = {}) -> Dict[str, Any]:
    """
    生成响应字典
    
    Args:
        code: 响应状态码
        error: 错误信息
        payload: 响应数据
        
    Returns:
        包含状态码、错误信息和数据的字典
    """
    return {
        "code": code,
        "error": error,
        "payload": payload
    }

def send_tcp_command(command: str, 
                     host: str = "127.0.0.1", 
                     port: int = 12345, 
                     timeout: int = -1) -> Dict[str, Any]:
    """
    发送TCP命令到服务器（每次调用都建立新连接）
    
    Args:
        command: 要发送的命令字典
        host: 服务器主机地址
        port: 服务器端口
        timeout: 连接和响应超时时间（秒）
        
    Returns:
        服务器响应结果
    """
    socket_obj = None
    try:
        # 创建socket连接
        socket_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if timeout > 0:
            socket_obj.settimeout(timeout)
        
        # 连接到服务器
        socket_obj.connect((host, port))
        
        # 发送数据
        socket_obj.sendall(command.encode('utf-8'))
        
        # 接收响应
        response_data = b""
        start_time = time.time()
        while True:
            # 检查超时
            if timeout > 0:
                if time.time() - start_time > timeout:
                    raise socket.timeout("接收响应超时")

            chunk = socket_obj.recv(2048)
            response_data += chunk
            break
        
        # 解析响应
        response_str = response_data.decode('utf-8').strip()
        response_str = response_str.split(';')[1]
        
        return {
            "status": "success",
            "message": f"命令发送成功到 {host}:{port}",
            "response": response_str,
            "host": host,
            "port": port
        }
        
    except socket.timeout as e:
        return {
            "status": "error",
            "message": f"连接或响应超时: {str(e)}",
            "response": json.dumps({"code": "-1", "error": "timeout", "payload": {}}),
            "host": host,
            "port": port
        }
    except ConnectionRefusedError:
        return {
            "status": "error",
            "message": f"连接被拒绝: {host}:{port}",
            "response": json.dumps({"code": "-2", "error": "refused", "payload": {}}),
            "host": host,
            "port": port
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"发送命令错误: {str(e)}",
            "response": json.dumps({"code": "-3", "error": "send", "payload": {}}),
            "host": host,
            "port": port    
        }
    finally:
        # 确保关闭socket连接
        if socket_obj:
            try:
                socket_obj.close()
            except:
                pass

def handle_get_resources(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """获取所有资源占用情况"""

    def get_cpu_usage() -> Dict[str, Any]:
        """获取CPU使用情况"""
        try:
            # 获取CPU使用率（1秒间隔）
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 获取每个CPU核心的使用率
            cpu_percent_per_core = psutil.cpu_percent(interval=1, percpu=True)
            
            # 获取CPU频率
            cpu_freq = psutil.cpu_freq()
            
            # 获取CPU统计信息
            cpu_stats = psutil.cpu_stats()
            
            return {
                "total_usage_percent": cpu_percent,
                "per_core_usage_percent": cpu_percent_per_core,
                "core_count": psutil.cpu_count(),
                "logical_core_count": psutil.cpu_count(logical=True),
                "frequency": {
                    "current": cpu_freq.current if cpu_freq else None,
                    "min": cpu_freq.min if cpu_freq else None,
                    "max": cpu_freq.max if cpu_freq else None
                },
                "stats": {
                    "ctx_switches": cpu_stats.ctx_switches,
                    "interrupts": cpu_stats.interrupts,
                    "soft_interrupts": cpu_stats.soft_interrupts,
                    "syscalls": cpu_stats.syscalls
                }
            }
        except Exception as e:
            return {"error": f"获取CPU信息失败: {e}"}


    def get_memory_usage() -> Dict[str, Any]:
        """获取内存使用情况"""
        try:
            # 获取虚拟内存信息
            virtual_memory = psutil.virtual_memory()
            
            # 获取交换内存信息
            swap_memory = psutil.swap_memory()
            
            return {
                "virtual_memory": {
                    "total": virtual_memory.total,
                    "available": virtual_memory.available,
                    "used": virtual_memory.used,
                    "free": virtual_memory.free,
                    "usage_percent": virtual_memory.percent,
                    "used_gb": round(virtual_memory.used / (1024**3), 2),
                    "total_gb": round(virtual_memory.total / (1024**3), 2)
                },
                "swap_memory": {
                    "total": swap_memory.total,
                    "used": swap_memory.used,
                    "free": swap_memory.free,
                    "usage_percent": swap_memory.percent,
                    "used_gb": round(swap_memory.used / (1024**3), 2),
                    "total_gb": round(swap_memory.total / (1024**3), 2)
                }
            }
        except Exception as e:
            return {"error": f"获取内存信息失败: {e}"}
        
    resp = {
        "code": 0,
        "error": "OK",
        "payload": {
            "cpu": get_cpu_usage(),
            "memory": get_memory_usage()
        }
    }
    return {
        "status": "success",
        "message": f"获取资源占用情况成功",
        "response": json.dumps(resp)
    }

def handle_tcp_client_send(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """处理TCP命令发送请求"""
    command = arguments.get("command", {})
    host = arguments.get("host", "127.0.0.1")
    port = arguments.get("port", 12345)
    timeout = arguments.get("timeout", 10)
    
    if not command:
        return {
            "status": "error",
            "message": "命令不能为空",
            "response": None
        }
    
    # 发送命令
    result = send_tcp_command(command, host, port, timeout)
    return result

def loop_query_status_with_ping(cmd, ping_timeout: int=5):
    interlval = 0
    while True:
        # 探活
        if (interlval >= ping_timeout):
            interlval = 0
            ping_result = handle_ping({})
            ping_result = json.loads(ping_result["response"])
            if (ping_result["code"] != 0):
                return {
                    "status": "error",
                    "message": "app宕机了",
                    "response": json.dumps({"code": "-1", "error": "app dead", "payload": {}})
                }

        status = handle_query_cmd_status({"cmd": cmd})
        if (status == 1):
            break
        time.sleep(1)
        interlval += 1

def handle_load_project(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """处理加载项目请求"""
    path = arguments.get("path", "")
    
    if not path:
        return {
            "status": "error",
            "message": "项目路径不能为空",
            "response": None
        }
    
    # 加载项目
    result = send_tcp_command(f"trigger_load_project;{json.dumps({'file': path})}")

    loop_query_status_with_ping("trigger_load_project")
    # interlval = 0
    # while True:
    #     # 探活
    #     if (interlval >= 5):
    #         interlval = 0
    #         ping_result = handle_ping({})
    #         ping_result = json.loads(ping_result["response"])
    #         if (ping_result["code"] != 0):
    #             return {
    #                 "status": "error",
    #                 "message": "app宕机了",
    #                 "response": json.dumps({"code": "-1", "error": "app dead", "payload": {}})
    #             }

    #     status = handle_query_cmd_status({"cmd": "trigger_load_project"})
    #     if (status == 1):
    #         break
    #     time.sleep(1)
    #     interlval += 1

    return result

def handle_ping(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """处理探活请求"""
    result = send_tcp_command(f"ping;{json.dumps({})}", timeout = 30) 
    return result

def handle_wait_app_ready(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """处理等待应用就绪请求"""
    arg = {
        "type": 0,
    }
    result = send_tcp_command(f"query_status;{json.dumps(arg)}") 
    res = json.loads(result["response"])
    global current_app_id
    current_app_id = res["payload"]
    return result

def handle_query_cmd_status(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """处理查询命令状态请求"""
    arg = {
        "type": 1,
        "app_id": current_app_id,
        "cmd": arguments.get("cmd", ""),
    }
    result = send_tcp_command(f"query_status;{json.dumps(arg)}") 
    res = json.loads(result["response"])
    status = json.loads(res["payload"])["status"]
    return status

def handle_capture(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """处理截图请求"""
    arg = {
        "save_as": arguments.get("save_as", ""),
        "type": arguments.get("type", "ready"),
        "w": arguments.get("w", 512),
        "h": arguments.get("h", 512)
    }
    result = send_tcp_command(f"capture;{json.dumps(arg)}") 
    return result

def handle_set_capture_mode(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """处理截图请求"""
    arg = {
        "enable": arguments.get("enable")
    }
    result = send_tcp_command(f"set_capture_mode;{json.dumps(arg)}") 
    return result

def handle_take_screenshot(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    截取当前屏幕
    """
    try:
        # 查询控件几何信息，确定3D区域并截图
        topbar_geometry = handle_get_widget_geometry({"widget_id": 1})
        canvas_geometry = handle_get_widget_geometry({"widget_id": 2})
        topbar_geometry = json.loads(topbar_geometry["response"])["payload"]
        topbar_geometry = json.loads(topbar_geometry)
        canvas_geometry = json.loads(canvas_geometry["response"])["payload"]
        canvas_geometry = json.loads(canvas_geometry)
        region = (0, topbar_geometry["h"], canvas_geometry["w"], canvas_geometry["h"])
        # 启用截图模式
        handle_set_capture_mode({"enable": 1})
        time.sleep(1)
        # 截取屏幕
        screenshot = pyautogui.screenshot(region=region)
        save_path = arguments.get("save_path", "")
        # 保存截图
        # 确保目录存在
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        screenshot.save(save_path) 
        return {
            "status": "success",
            "message": "OK",
            "response": json.dumps({"code": 0, "error": "OK", "payload": {}})
        }
        
    except Exception as e:
        print(f"截图失败: {e}")
        raise
    finally:
        # 取消截图模式
        handle_set_capture_mode({"enable": 0})



def handle_get_widget_geometry(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """查询控件几何信息"""
    arg = {
        "widget_id": arguments.get("widget_id")
    }
    result = send_tcp_command(f"get_widget_geometry;{json.dumps(arg)}") 
    return result

def handle_new_project(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """新建项目"""
    result = send_tcp_command(f"new_project;{json.dumps({})}") 
    return result

def contours_similar(image_path1, image_path2, output_path1=None, output_path2=None, similarity_threshold=0.15, match_ratio_threshold=0.95):
    # 读取图片
    img1 = cv2.imread(image_path1)
    img2 = cv2.imread(image_path2)

    if img1 is None or img2 is None:
        raise ValueError("无法读取图片，请检查路径是否正确")

    # 转灰度
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    # 二值化
    _, binary1 = cv2.threshold(gray1, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    _, binary2 = cv2.threshold(gray2, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 使用 RETR_CCOMP 获取所有轮廓 + 层级信息（可区分外轮廓和内轮廓/洞）
    contours1, hierarchy1 = cv2.findContours(binary1, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    contours2, hierarchy2 = cv2.findContours(binary2, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    if hierarchy1 is None or hierarchy2 is None:
        return False

    hierarchy1 = hierarchy1[0]  # OpenCV 返回的是一个带额外维度的数组，取第0维
    hierarchy2 = hierarchy2[0]

    # 分离外轮廓和内轮廓（基于 hierarchy 中的 Parent 字段）
    def separate_contours(contours, hierarchy):
        external = []
        internal = []
        for i, h in enumerate(hierarchy):
            if h[3] == -1:  # Parent == -1 表示是外轮廓
                external.append(contours[i])
            else:  # Parent != -1 表示是内轮廓（洞）
                internal.append(contours[i])
        return external, internal

    external_contours1, internal_contours1 = separate_contours(contours1, hierarchy1)
    external_contours2, internal_contours2 = separate_contours(contours2, hierarchy2)

    # 定义一个函数：对两个轮廓列表按面积排序后，依次匹配并计算匹配上的数量
    def match_contours(list1, list2, similarity_threshold):
        # 按面积从大到小排序
        list1_sorted = sorted(list1, key=cv2.contourArea, reverse=True)
        list2_sorted = sorted(list2, key=cv2.contourArea, reverse=True)
        min_len = min(len(list1_sorted), len(list2_sorted))
        if min_len == 0:
            return 0

        matched = 0
        for i in range(min_len):
            sim = cv2.matchShapes(list1_sorted[i], list2_sorted[i], cv2.CONTOURS_MATCH_I1, 0)
            if sim < similarity_threshold:
                matched += 1
        return matched

    # 分别匹配外轮廓和内轮廓
    external_matched = match_contours(external_contours1, external_contours2, similarity_threshold)
    internal_matched = match_contours(internal_contours1, internal_contours2, similarity_threshold)

    external_total = max(1, len(external_contours1))  # 避免除零
    internal_total = max(1, len(internal_contours1))

    external_ratio = external_matched / external_total
    internal_ratio = internal_matched / internal_total

    # 可选：打印调试信息
    # print(f"外轮廓匹配率: {external_ratio:.2f}, 内轮廓匹配率: {internal_ratio:.2f}")
    # print(f"外轮廓匹配率raw: {external_matched:.2f}, 内轮廓匹配率raw: {internal_matched:.2f}")
    # print(f"inner======>:{len(internal_contours1)} {len(internal_contours2)}")
    # print(f"outer======>:{len(external_contours1)} {len(external_contours2)}")

    # 综合判断：你可以根据需求调整这里的逻辑，比如要求两者都高于某阈值
    ext_vaild = True
    int_vaild = True
    if (len(external_contours1) == 0) and (len(external_contours2) == 0):
        ext_vaild = False
    if (len(internal_contours1) == 0) and (len(internal_contours2) == 0):
        int_vaild = False
    # 结果判断
    external_similar = (external_ratio >= match_ratio_threshold)
    internal_similar = (internal_ratio >= match_ratio_threshold)
    if ext_vaild == False and int_vaild == False:
        overall_similar = False
    elif (ext_vaild == True)  and (int_vaild == False):
        overall_similar = external_similar
    elif (ext_vaild == False)  and (int_vaild == True):
        overall_similar = internal_similar
    elif (ext_vaild == True)  and (int_vaild == True):
        overall_similar = external_similar and internal_similar

    # 可选：保存带轮廓的图像
    if output_path1 is not None:
        contour_img1 = img1.copy()
        cv2.drawContours(contour_img1, external_contours1 + internal_contours1, -1, (0, 255, 0), 2)
        cv2.imwrite(output_path1, contour_img1)

    if output_path2 is not None:
        contour_img2 = img2.copy()
        cv2.drawContours(contour_img2, external_contours2 + internal_contours2, -1, (0, 255, 0), 2)
        cv2.imwrite(output_path2, contour_img2)

    return overall_similar

def handle_contours_similar(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """图像对比，基于轮廓相似性"""
    image_path1 = arguments["image_path1"]
    image_path2 = arguments["image_path2"]
    output_path1 = arguments.get("output_path1", None)
    output_path2 = arguments.get("output_path2", None)
    similarity_threshold = arguments.get("similarity_threshold", 0.5)
    match_ratio_threshold = arguments.get("match_ratio_threshold", 0.8)
    equal = contours_similar(image_path1, image_path2, output_path1, output_path2, similarity_threshold, match_ratio_threshold)

    if (equal):
        resp = gen_respone(0, "图像相似", {"equal": equal})
    else:
        resp = gen_respone(0, "图像不相似", {"equal": equal})
    return {
        "status": "success",
        "message": f"",
        "response": json.dumps(resp)
    }
    
def handle_trigger_slice(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """触发切片"""
    result = send_tcp_command(f"trigger_slice;{json.dumps({})}") 
    loop_query_status_with_ping("trigger_slice")
    return result

def handle_execute_terminal_command(arguments: Dict[str, Any]) -> Dict[str, Any]:
# def execute_terminal_command(command, timeout=30, cwd=None):
    """
    安全地执行终端命令

    Args:
        command (str or list): 要执行的命令
        timeout (int): 超时时间（秒）
        cwd (str): 工作目录

    Returns:
        dict: 包含执行结果的字典
    """
    command = arguments["command"]
    timeout = arguments.get("timeout", 30)
    cwd = arguments.get("cwd", None)
    try:
        # 安全检查：可以在这里添加命令白名单或黑名单
        if isinstance(command, str):
            cmd = command.split()
        else:
            cmd = command

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            shell=isinstance(command, str)
        )

        
        resp = gen_respone(
            0, 
            "命令执行成功", 
            {"stdout": result.stdout, "stderr": result.stderr, "return_code": result.returncode}
        )
        return {
            "status": "success",
            "message": f"",
            "response": json.dumps(resp)
        }
        

    except subprocess.TimeoutExpired:
        resp = gen_respone(
            -1, 
            "Command timed out", 
            {"stdout": result.stdout, "stderr": result.stderr, "return_code": -1}
        )
        return {
            "status": "success",
            "message": f"",
            "response": json.dumps(resp)
        }
    except Exception as e:
        resp = gen_respone(
            -1, 
            str(e), 
            {"stdout": result.stdout, "stderr": result.stderr, "return_code": -1}
        )
        return {
            "status": "success",
            "message": f"",
            "response": json.dumps(resp)
        }

# MCP工具处理映射
TCP_CLIENT_HANDLERS = {
    # "get_resources": handle_get_resources,
    "load_project": handle_load_project,
    "ping": handle_ping,
    "wait_app_ready": handle_wait_app_ready,
    "capture": handle_take_screenshot,
    "new_project": handle_new_project,
    "contours_similar": handle_contours_similar,
    "trigger_slice": handle_trigger_slice,
    "execute_terminal_command": handle_execute_terminal_command,
}

# MCP工具定义
TCP_CLIENT_TOOLS = {
    "load_project": {
        "name": "load_project",
        "description": "加载3mf",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "项目绝对路径"
                }
            },
            "required": ["path"]
        }
    },
    "ping": {
        "name": "ping",
        "description": "探活",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "wait_app_ready": {
        "name": "wait_app_ready",
        "description": "等待app就绪",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "capture": {
        "name": "capture",
        "description": "截图",
        "inputSchema": {
            "type": "object",
            "properties": {
                "save_path": {
                    "type": "string",
                    "description": "保存路径"
                }
            },
            "required": ["save_path"]
        }
    },
    "new_project": {
        "name": "new_project",
        "description": "新建项目",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "contours_similar": {
        "name": "contours_similar",
        "description": "对比两张图的轮廓是否相似",
        "inputSchema": {
            "type": "object",
            "properties": {
                "image_path1": {
                    "type": "string",
                    "description": "第一张图路径"
                },
                "image_path2": {
                    "type": "string",
                    "description": "第二张图路径"
                },
                "output_path1": {
                    "type": "string",
                    "description": "第一张图轮廓图保存路径"
                },
                "output_path2": {
                    "type": "string",
                    "description": "第二张图轮廓图保存路径"
                },
                "similarity_threshold": {
                    "type": "number",
                    "description": "轮廓相似度阈值"
                },
                "match_ratio_threshold": {
                    "type": "number",
                    "description": "匹配率阈值"
                }
            },
            "required": ["image_path1", "image_path2"]
        }
    },
    "trigger_slice": {
        "name": "trigger_slice",
        "description": "触发切片",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "execute_terminal_command": {
        "name": "execute_terminal_command",
        "description": "执行终端命令",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "要执行的命令"
                },
                "timeout": {
                    "type": "integer",
                    "description": "超时时间（秒）"
                },
                "cwd": {
                    "type": "string",
                    "description": "工作目录"
                }
            },
            "required": ["command"]
        }
    },
}

# MCP服务器标准接口
def handle_initialize():
    """处理初始化请求"""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "tcp-client-mcp",
            "version": "1.0.0"
        }
    }


def handle_list_tools():
    """列出可用工具"""
    return {"tools": list(TCP_CLIENT_TOOLS.values())}


def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """调用工具"""
    if name in TCP_CLIENT_HANDLERS:
        return TCP_CLIENT_HANDLERS[name](arguments)
    else:
        return {
            "status": "error",
            "message": f"未知工具: {name}"
        }

def main():
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
                
            try:
                request = json.loads(line.strip())
                method = request.get("method", "")
                
                if method == "initialize":
                    response = handle_initialize()
                elif method == "tools/list":
                    response = handle_list_tools()
                elif method == "tools/call":
                    params = request.get("params", {})
                    response = handle_call_tool(
                        params.get("name", ""),
                        params.get("arguments", {})
                    )
                    cmd_resp = json.loads(response["response"])
                    is_error = cmd_resp["code"] != 0
                    ret_text =  cmd_resp["error"] if is_error else json.dumps(cmd_resp["payload"])
                    response_message = {
                        "jsonrpc": "2.0",
                        "id": request.get("id", None),
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": ret_text
                                }
                            ],
                            "isError": is_error
                        }
                    }
                    print(json.dumps(response_message), flush=True)
                    continue
                else:
                    response = {
                        "error": {
                            "code": -32601,
                            "message": f"未知方法: {method}"
                        }
                    }


                response_message = {
                    "jsonrpc": "2.0",
                    "id": request.get("id", None),
                    "result": response
                }
                print(json.dumps(response_message), flush=True)
                
            except json.JSONDecodeError:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "解析错误"
                    }
                }
                print(json.dumps(error_response), flush=True)
                
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id", None) if 'request' in locals() else None,
                    "error": {
                        "code": -32000,
                        "message": f"内部错误: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)
                
    except KeyboardInterrupt:
        print("\n服务器已停止", file=sys.stderr)

if __name__ == "__main__":
    main()
