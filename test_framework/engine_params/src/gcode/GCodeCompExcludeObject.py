"""
G-code EXCLUDE_OBJECT 数据比较类
用于比较两个G-code文件中特定对象的EXCLUDE_OBJECT_START/END之间的数据
"""

from pathlib import Path
from typing import List, Tuple, Dict, Optional
import mmap
import re


class GCodeCompExcludeObject:
    """
    G-code EXCLUDE_OBJECT 数据比较器
    
    提供对G-code文件中EXCLUDE_OBJECT_START/END指令间数据的提取和比较功能
    """
    
    # EXCLUDE_OBJECT 指令正则表达式
    EXCLUDE_OBJECT_START_RE = re.compile(
        rb"^\s*;?\s*EXCLUDE_OBJECT_START\s+NAME=(?P<name>[^\r\n]+)\s*$",
        re.IGNORECASE
    )
    EXCLUDE_OBJECT_END_RE = re.compile(
        rb"^\s*;?\s*EXCLUDE_OBJECT_END\s+NAME=(?P<name>[^\r\n]+)\s*$",
        re.IGNORECASE
    )
    
    # 从NAME中提取对象ID的正则表达式
    ID_FROM_NAME_RE = re.compile(rb"(?:^|[^A-Za-z0-9])id_(\d+)(?:[^A-Za-z0-9]|$)", re.IGNORECASE)
    
    def __init__(self, tolerance: float = 1e-6):
        """
        初始化比较器
        
        参数:
            tolerance: 数值比较容差（默认1e-6）
        """
        self.tolerance = tolerance
    
    def extract_exclude_object_data(self, gcode_path: Path, object_id: int = 0) -> List[str]:
        """
        从G-code文件中提取指定对象的EXCLUDE_OBJECT_START/END之间的数据
        
        参数:
            gcode_path: G-code文件路径
            object_id: 对象ID（默认为0）
            
        返回:
            List[str]: 对象数据行列表（不包含标记行）
        """
        data_lines: List[str] = []
        last_g1_line: Optional[str] = None
        
        with gcode_path.open("rb") as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                pos = 0
                current_object = None
                in_object = False
                
                while pos < len(mm):
                    # 查找换行符
                    nl = mm.find(b"\n", pos)
                    if nl == -1:
                        line_end = len(mm)
                    else:
                        line_end = nl
                    
                    line_bytes = mm[pos:line_end]
                    line = line_bytes.decode('utf-8', errors='ignore').strip()
                    
                    # 检查是否为EXCLUDE_OBJECT_START指令
                    start_match = self.EXCLUDE_OBJECT_START_RE.match(line_bytes)
                    if start_match:
                        # 提取对象ID
                        name_bytes = start_match.group("name")
                        obj_id = self._extract_object_id(name_bytes)
                        
                        if obj_id == object_id:
                            current_object = obj_id
                            in_object = True
                            last_g1_line = None
                            # 移动到下一行开始
                            pos = line_end + 1 if nl != -1 else len(mm)
                            continue
                    
                    # 检查是否为EXCLUDE_OBJECT_END指令
                    end_match = self.EXCLUDE_OBJECT_END_RE.match(line_bytes)
                    if end_match and in_object:
                        name_bytes = end_match.group("name")
                        obj_id = self._extract_object_id(name_bytes)
                        
                        if obj_id == current_object:
                            in_object = False
                            current_object = None
                            last_g1_line = None
                    
                    if in_object and line:
                        stripped = line.strip()
                        if stripped.startswith(";TYPE:Outer wall"):
                            if last_g1_line is not None:
                                data_lines.append(last_g1_line)
                        if not stripped.startswith(";"):
                            cmd, params = self._parse_gcode_line(stripped)
                            if cmd.upper() == "G1" and "X" in params and "Y" in params:
                                last_g1_line = stripped
                    
                    if nl == -1:
                        break
                    pos = nl + 1
        return data_lines
    
    def compare_exclude_object_data(
        self,
        baseline_gcode: Path,
        test_gcode: Path,
        object_id: int = 0
    ) -> Tuple[bool, Dict[str, any]]:
        """
        比较两个G-code文件中指定对象的EXCLUDE_OBJECT数据
        
        参数:
            baseline_gcode: 基准G-code文件路径
            test_gcode: 测试G-code文件路径
            object_id: 对象ID
            
        返回:
            Tuple[bool, Dict]: (是否匹配, 详细比较结果)
        """
        # 提取数据
        baseline_data = self.extract_exclude_object_data(baseline_gcode, object_id)
        test_data = self.extract_exclude_object_data(test_gcode, object_id)
        
        # 检查数据行数
        if len(baseline_data) != len(test_data):
            details = {
                "match": False,
                "error": f"数据行数不匹配: 基准 {len(baseline_data)} 行, 测试 {len(test_data)} 行",
                "baseline_lines": baseline_data,
                "test_lines": test_data
            }
            return False, details
        
        # 逐行比较
        mismatches = []
        for i, (baseline_line, test_line) in enumerate(zip(baseline_data, test_data)):
            if not self._compare_gcode_lines(baseline_line, test_line):
                mismatches.append({
                    "line_number": i + 1,
                    "baseline": baseline_line,
                    "test": test_line
                })
        
        # 构建结果
        match = len(mismatches) == 0
        details = {
            "match": match,
            "total_lines": len(baseline_data),
            "mismatch_count": len(mismatches),
            "mismatches": mismatches,
            "baseline_file": str(baseline_gcode),
            "test_file": str(test_gcode),
            "object_id": object_id
        }
        
        return match, details
    
    def parse_exclude_object_comparison(
        self,
        gcode_path: Path,
        baseline_gcode: Path,
        object_id: int = 0,
        expected_match: bool = True
    ) -> Tuple[bool, bool, Dict[str, any]]:
        """
        用于测试框架的解析函数
        
        参数:
            gcode_path: 测试G-code文件路径
            baseline_gcode: 基准G-code文件路径
            object_id: 对象ID
            expected_match: 期望是否匹配
            
        返回:
            Tuple[bool, bool, Dict]: (测试通过, 实际匹配, 详细信息)
        """
        actual_match, details = self.compare_exclude_object_data(baseline_gcode, gcode_path, object_id)
        ok = actual_match == expected_match
        
        return ok, actual_match, details
    
    def _extract_object_id(self, name_bytes: bytes) -> int:
        """从NAME字节中提取对象ID"""
        match = self.ID_FROM_NAME_RE.search(name_bytes)
        if match:
            try:
                return int(match.group(1))
            except Exception:
                pass
        # 如果无法提取ID，返回默认值0
        return 0
    
    def _compare_gcode_lines(self, line1: str, line2: str) -> bool:
        # print(f"[EXCLUDE_OBJECT_COMPARE] baseline='{line1}' test='{line2}'")
        """比较两个G-code指令行是否相同"""
        # 简单字符串比较（适用于非数值指令）
        if line1 == line2:
            return True
        
        # 解析G-code指令
        cmd1, params1 = self._parse_gcode_line(line1)
        cmd2, params2 = self._parse_gcode_line(line2)
        
        # 检查指令类型
        if cmd1 != cmd2:
            return False
        
        # 比较参数
        if set(params1.keys()) != set(params2.keys()):
            return False
        
        # 比较数值参数（考虑容差）
        for key in params1:
            if key in ['X', 'Y', 'Z', 'E', 'F']:
                try:
                    val1 = float(params1[key])
                    val2 = float(params2[key])
                    if abs(val1 - val2) > self.tolerance:
                        return False
                except (ValueError, TypeError):
                    if params1[key] != params2[key]:
                        return False
            else:
                if params1[key] != params2[key]:
                    return False
        
        return True
    
    def _parse_gcode_line(self, line: str) -> Tuple[str, Dict[str, str]]:
        """解析G-code指令行"""
        line = line.strip()
        if not line:
            return "", {}
        
        # 分离指令和参数
        parts = line.split()
        if not parts:
            return "", {}
        
        command = parts[0]
        params = {}
        
        for part in parts[1:]:
            if len(part) >= 2:
                key = part[0].upper()
                value = part[1:]
                params[key] = value
        
        return command, params


# 提供便捷的静态方法
@classmethod
def compare_exclude_object_data_static(
    cls,
    baseline_gcode: Path,
    test_gcode: Path,
    object_id: int = 0,
    tolerance: float = 1e-6
) -> Tuple[bool, Dict[str, any]]:
    """
    静态方法：比较两个G-code文件中指定对象的EXCLUDE_OBJECT数据
    
    参数:
        baseline_gcode: 基准G-code文件路径
        test_gcode: 测试G-code文件路径
        object_id: 对象ID
        tolerance: 数值比较容差
        
    返回:
        Tuple[bool, Dict]: (是否匹配, 详细比较结果)
    """
    comparator = cls(tolerance=tolerance)
    return comparator.compare_exclude_object_data(baseline_gcode, test_gcode, object_id)


# 将静态方法绑定到类
GCodeCompExcludeObject.compare_exclude_object_data_static = compare_exclude_object_data_static
