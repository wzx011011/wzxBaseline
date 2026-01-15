#!/usr/bin/env python3
"""
自动检测 CrealityPrint 路径并生成 .env 文件
"""

import os
from pathlib import Path


def auto_detect_exe_path():
    """自动检测 CrealityPrint.exe 路径"""
    common_paths = [
        "C:/Program Files/Creality/Creality Print 7.0 Beta/CrealityPrint.exe",
        "C:/Program Files/Creality/Creality Print/CrealityPrint.exe",
        str(Path.home() / "AppData/Local/Programs/Creality/CrealityPrint.exe"),
        "E:/wzx/C3DSlicer/C3DSlicer/build_unified/src/Release/CrealityPrint.exe",
    ]
    
    for path_str in common_paths:
        p = Path(path_str).expanduser()
        if p.exists() and p.is_file():
            return str(p)
    
    return None


def auto_detect_log_path():
    """自动检测日志路径，如果不存在则创建"""
    username = os.getenv("USERNAME") or os.getenv("USER")
    if username:
        candidate = Path(f"C:/Users/{username}/AppData/Local/creality/creality-print/automated-test-logs")
        # 如果目录不存在，则创建它
        if not candidate.exists():
            try:
                candidate.mkdir(parents=True, exist_ok=True)
                print(f"  [INFO] 已创建日志目录: {candidate}")
            except Exception as e:
                print(f"  [WARNING] 创建日志目录失败: {e}")
                return None
        return str(candidate)
    return None


def main():
    print("=" * 80)
    print("自动检测 CrealityPrint 环境变量")
    print("=" * 80)
    
    # 检测路径
    exe_path = auto_detect_exe_path()
    log_path = auto_detect_log_path()
    
    print("\n检测结果：")
    print(f"  CREALITY_PRINTER_PATH = {exe_path or '未检测到'}")
    print(f"  CREALITY_PRINTER_LOG_PATH = {log_path or '未检测到'}")
    
    # 生成 .env 文件
    env_file = Path(__file__).parent.parent / ".env"
    
    if exe_path or log_path:
        with open(env_file, "w", encoding="utf-8") as f:
            if exe_path:
                f.write(f"CREALITY_PRINTER_PATH={exe_path}\n")
            if log_path:
                f.write(f"CREALITY_PRINTER_LOG_PATH={log_path}\n")
        
        print(f"\n✓ 已生成 .env 文件: {env_file.absolute()}")
        print("\n文件内容：")
        with open(env_file, "r", encoding="utf-8") as f:
            print(f.read())
    else:
        print("\n✗ 未检测到任何路径，无法生成 .env 文件")
        print("  请手动创建 .env 文件并配置环境变量")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
