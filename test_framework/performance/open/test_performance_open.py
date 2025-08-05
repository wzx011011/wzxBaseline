import time
import pyautogui
import pytest
import pyperclip
import shutil
import os
import cv2
import re
import numpy as np
import json
import zipfile
from pathlib import Path

def are_images_similar(img1_path, img2_path, min_match_count=10):
    # 读取图像
    img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)
    min_match_count = img1.shape[0]*0.8
    print("========>最小点：", min_match_count)

    if img1 is None or img2 is None:
        print("无法读取图像")
        return False

    # 初始化 SIFT 检测器
    sift = cv2.SIFT_create()

    # 检测关键点和计算描述子
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)

    # 如果没有检测到关键点，直接返回 False
    if des1 is None or des2 is None:
        print("未检测到关键点")
        return False

    # 使用 FLANN 匹配器
    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)  # 或者设置更高的值以获得更准确的匹配

    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des1, des2, k=2)

    # 应用 Lowe's ratio test 过滤匹配点
    good_matches = []
    for m, n in matches:
        if m.distance < 0.7 * n.distance:
            good_matches.append(m)

    # 如果足够多的匹配点，则认为图像相似
    if len(good_matches) >= min_match_count:
        print(f"图像相似，匹配点数量: {len(good_matches)}")
        return True
    else:
        print(f"图像不相似，匹配点数量: {len(good_matches)}")
        return False

def are_images_identical(img1_path, img2_path):
    # 读取图像（保持原始颜色通道，通常用 BGR）
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)

    if img1 is None or img2 is None:
        print("无法读取图像")
        return False

    # 检查图像尺寸是否相同
    if img1.shape != img2.shape:
        print("图像尺寸不同")
        return False

    diff = cv2.absdiff(img1, img2)  # 计算绝对差异
    diff_pixels = np.where(diff > 0)  # 获取差异像素的坐标 (y, x)

    # 逐像素比较
    if len(diff_pixels[0]) == 0:
        print("图像完全相同")
        return True
    else:
        print(f"图像不完全相同{len(diff_pixels[0])}")
        return False

def find_plate_png_files(directory):
    """
    查找指定目录下所有符合 'plate_数字.png' 格式的文件
    
    Args:
        directory (str): 要搜索的目录路径
        
    Returns:
        list: 匹配的文件路径列表
    """
    pattern = re.compile(r'plate_\d+\.png$')  # 匹配 plate_数字.png 格式
    matched_files = []
    
    # 获取目录下的所有文件和文件夹
    with os.scandir(directory) as entries:
        for entry in entries:
            if entry.is_file() and pattern.match(entry.name):  # 只检查文件，且匹配模式
                full_path = os.path.join(directory, entry.name)
                matched_files.append(full_path)
    
    return matched_files

def extract_number_from_filename(filename):
    """
    从文件名中提取数字部分（如 'plate_1.png' -> 1）
    
    Args:
        filename (str): 文件路径（如 'D:/plate_1.png'）
        
    Returns:
        int: 提取的数字
    """
    # 从文件名中提取数字部分
    basename = os.path.basename(filename)  # 获取文件名（如 'plate_1.png'）
    match = re.search(r'plate_(\d+)\.png', basename)
    if match:
        return int(match.group(1))  # 返回数字部分
    else:
        raise ValueError(f"文件名格式不正确: {filename}，应为 'plate_数字.png'")

def match_plate_files(list1, list2):
    """
    根据文件名中的数字匹配两个列表中的文件
    
    Args:
        list1 (list): 第一个文件路径列表
        list2 (list): 第二个文件路径列表
        
    Returns:
        list: 匹配成功的文件对列表，每个元素是 (file1, file2) 的元组
    """
    # 构建数字到文件路径的映射字典
    dict1 = {}
    for file_path in list1:
        num = extract_number_from_filename(file_path)
        dict1[num] = file_path
    
    dict2 = {}
    for file_path in list2:
        num = extract_number_from_filename(file_path)
        dict2[num] = file_path
    
    # 找出两个字典中共同的数字
    common_numbers = set(dict1.keys()) & set(dict2.keys())
    
    # 组合匹配的文件对
    matched_pairs = []
    for num in common_numbers:
        matched_pairs.append((dict1[num], dict2[num]))
    
    return matched_pairs

def are_contours_similar(image_path1, image_path2, output_path1=None, output_path2=None, similarity_threshold=0.15, match_ratio_threshold=0.95):
    """
    比较两张图片的轮廓相似性，如果轮廓总体匹配度 >= 95%，返回 True，否则 False。
    同时，可以将绘制轮廓后的图片保存到指定路径。

    参数:
        image_path1 (str): 第一张图片路径
        image_path2 (str): 第二张图片路径
        output_path1 (str): 第一张图片绘制轮廓后的保存路径，如果为 None 则不保存
        output_path2 (str): 第二张图片绘制轮廓后的保存路径，如果为 None 则不保存
        similarity_threshold (float): 单个轮廓匹配相似度阈值，越小越严格，默认 0.15
        match_ratio_threshold (float): 轮廓匹配率阈值，比如 0.95 表示 95% 的轮廓要匹配，才认为相似

    返回:
        bool: True 表示轮廓相似度 >= 95%，否则 False
    """
    # 读取图片并转为灰度
    img1 = cv2.imread(image_path1)
    img2 = cv2.imread(image_path2)

    if img1 is None or img2 is None:
        raise ValueError("无法读取图片，请检查路径是否正确")

    # 转为灰度图
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    # 二值化处理（提取前景）
    _, binary1 = cv2.threshold(gray1, 127, 255, cv2.THRESH_BINARY)
    _, binary2 = cv2.threshold(gray2, 127, 255, cv2.THRESH_BINARY)

    # 查找轮廓（只提取外部轮廓）
    contours1, _ = cv2.findContours(binary1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours2, _ = cv2.findContours(binary2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 如果一张图没有轮廓，另一张有，则肯定不相似
    if len(contours1) == 0 or len(contours2) == 0:
        print("1111")
        return False

    # 如果轮廓数量相差太大，直接认为不相似
    if abs(len(contours1) - len(contours2)) > min(len(contours1), len(contours2)) * 0.2:
        print("2222")
        return False

    # 取每个图片中面积最大的几个轮廓（比如前N个），避免太多小轮廓干扰
    def get_main_contours(contours, top_n=5):
        print("3333")
        # 按轮廓面积从大到小排序
        sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)
        return sorted_contours[:top_n]

    main_contours1 = get_main_contours(contours1)
    main_contours2 = get_main_contours(contours2)

    all_contours1 = main_contours1
    all_contours2 = main_contours2

    len1 = len(all_contours1)
    len2 = len(all_contours2)

    if len1 == 0 or len2 == 0:
        print("1111")
        return False

    # 取较小的轮廓数量作为比较基准
    min_count = min(len1, len2)
    if min_count == 0:
        print("22222")
        return False

    matched_count = 0

    # 依次比较两张图中的轮廓（按面积排序后一一对应）
    for i in range(min_count):
        contour1 = all_contours1[i]
        contour2 = all_contours2[i]

        # 使用 Hu 矩匹配形状相似度，值越小越相似
        similarity = cv2.matchShapes(contour1, contour2, cv2.CONTOURS_MATCH_I1, 0)
        
        if similarity < similarity_threshold:
            matched_count += 1

    # 计算匹配率
    match_ratio = matched_count / min_count

    print(f"✅ 轮廓匹配率: {match_ratio * 100:.2f}% （匹配阈值: {match_ratio_threshold * 100}%）")

    # 如果需要保存轮廓图
    if output_path1 is not None:
        # 在原图上绘制轮廓
        contour_img1 = img1.copy()
        cv2.drawContours(contour_img1, all_contours1, -1, (0, 255, 0), 2)
        cv2.imwrite(output_path1, contour_img1)

    if output_path2 is not None:
        # 在原图上绘制轮廓
        contour_img2 = img2.copy()
        cv2.drawContours(contour_img2, all_contours2, -1, (0, 255, 0), 2)
        cv2.imwrite(output_path2, contour_img2)

    return match_ratio >= match_ratio_threshold

def unzip_file(zip_file_path: str, extract_to_path: str) -> bool:
    """
    解压 zip 文件到指定目录

    参数:
        zip_file_path (str): 压缩文件路径，例如 "example.zip"
        extract_to_path (str): 解压目标文件夹路径，例如 "./output/"

    返回:
        bool: 解压成功返回 True，失败返回 False
    """
    try:
        # 如果目标路径不存在，则创建
        os.makedirs(extract_to_path, exist_ok=True)

        # 检查 zip 文件是否存在
        if not os.path.isfile(zip_file_path):
            print(f"[错误] 压缩文件不存在：{zip_file_path}")
            return False

        # 打开 zip 文件并解压
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to_path)
        
        print(f"[成功] 文件已解压到：{extract_to_path}")
        return True

    except zipfile.BadZipFile:
        print(f"[错误] 文件 '{zip_file_path}' 不是有效的 ZIP 文件 或已损坏")
    except PermissionError:
        print(f"[错误] 没有权限写入目标目录：{extract_to_path}")
    except Exception as e:
        print(f"[错误] 解压失败，原因：{e}")

    return False

def extract_time_from_log(log_str: str) -> str:
    """
    从输入的日志字符串中提取第二列的时分秒及毫秒（格式如：14:25:23.952322）

    参数:
        log_str (str): 输入的日志字符串，例如：
                       '2025-08-04 14:25:23.952322[head]:APP_READY_0[body]:'

    返回:
        str: 时间部分，例如 '14:25:23.952322'
    """
    # 按空格分割字符串
    parts = log_str.split()

    # 第二列就是时间（索引为 1，因为索引从 0 开始）
    time_part = parts[1]
    time_part = time_part.split("[")
    time_str = time_part[0]
    dt = datetime.strptime(time_str, "%H:%M:%S.%f")
    return dt

def test_performance_reopen(reopen_item, baseline_cur_path, open_creality_printer_with_file, check_app_respone, tmp_path):
    prefix = tmp_path/"test_performance_reopen"
    if prefix.exists():
        shutil.rmtree(prefix)
    prefix.mkdir()
    # capture prefix
    capture_prefix = prefix/"capture"
    capture_prefix.mkdir()
    # unzip prefix
    extract_prefix = prefix/"extract"
    extract_prefix.mkdir()

    path = os.path.join(baseline_cur_path, reopen_item["input"])
    send_cmd_handle = open_creality_printer_with_file
    # open project
    send_cmd_handle("trigger_load_project", json.dumps({"file": path}))

     # heartbeat
    def heartbeat(delay):
        ret,_,_ = send_cmd_handle("ping", json.dumps({}), 30, True)
        return ret

    ret = check_app_respone("FILES", "LOAD_PROJECT", 0)
    assert ret["code"] == 0
    start_time = extract_time_from_log(ret["data"])
    ret = check_app_respone("FILES", "LOAD_PROJECT", 1, -1, heartbeat)
    assert ret["code"] == 0
    end_time = extract_time_from_log(ret["data"])
    print("Using time", (end_time - start_time).total_seconds() * 1000)

    # unzip 3mf
    ret = unzip_file(path, str(extract_prefix))
    assert ret == True

    # found one thumnail to get size
    list1 = find_plate_png_files(str(extract_prefix/"Metadata"))
    thumnail_size = -1
    if len(list1) != 0:
        img = cv2.imread(list1[0], cv2.IMREAD_GRAYSCALE)
        thumnail_size = img.shape[0]
    if thumnail_size == -1:
        thumnail_size = 300

    ret,_,_ = send_cmd_handle("capture", json.dumps({
        "type": "ready",
        "save_as": str(capture_prefix)+"/"+"plate_%s.png",
        "w": thumnail_size,
        "h": thumnail_size
    }))
    # becompre images    
    list2 = find_plate_png_files(str(capture_prefix))
    matched = match_plate_files(list1, list2)
    similar = True
    if len(matched) == 0:
        similar = False
    for file_pair in matched:
        img1_path, img2_path = file_pair
        similar = similar and are_contours_similar(img1_path, img2_path, None, None, 0.8, 0.95)
    assert similar == reopen_item["expectation"]
