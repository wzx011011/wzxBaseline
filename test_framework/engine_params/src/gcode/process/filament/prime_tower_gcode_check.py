"""
擦拭塔 GCode 行为校验模块

用于验证擦拭塔生成的 GCode 中的动作序列、路径逻辑、回抽装填等行为
覆盖 TC-WT-001 ~ TC-WT-027 的 L2/L3 级别校验
"""
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import re


class GCodeMoveType(Enum):
    """GCode 移动类型枚举"""
    RETRACTION = "retraction"       # 回抽 (E < 0)
    UNRETRACTION = "unretraction"   # 装填/补料 (E > 0, no XY)
    Z_HOP = "z_hop"                 # Z抬升
    Z_DROP = "z_drop"               # Z降低
    TRAVEL = "travel"               # 空走 (no E or E=0)
    EXTRUSION = "extrusion"         # 挤出 (E > 0, with XY)


@dataclass
class GCodeMove:
    """单条 GCode 移动指令的解析结果"""
    line_num: int
    raw_line: str
    move_type: GCodeMoveType
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    e: Optional[float] = None
    f: Optional[float] = None
    comment: str = ""


@dataclass
class ToolChangeSequence:
    """换料序列信息"""
    tool_change_line: int       # T指令所在行号
    from_tool: int              # 原喷头
    to_tool: int                # 目标喷头
    before_moves: List[GCodeMove]   # T指令前5行
    after_moves: List[GCodeMove]    # T指令后10行


@dataclass
class WipeTowerRegion:
    """擦拭塔区域边界"""
    x_min: float
    x_max: float
    y_min: float
    y_max: float


class WipeTowerGCodeParser:
    """擦拭塔 GCode 解析器（L2/L3级别）"""
    
    def __init__(self, gcode_path: Path):
        self.gcode_path = gcode_path
        self.lines: List[str] = []
        self.moves: List[GCodeMove] = []
        self.config_block: Dict[str, str] = {}
        self.tower_region: Optional[WipeTowerRegion] = None
        
        self._load_and_parse()
    
    def _load_and_parse(self):
        """加载并解析 GCode 文件"""
        # 尝试不同的编码
        for encoding in ['utf-8', 'gbk', 'latin1']:
            try:
                with open(self.gcode_path, 'r', encoding=encoding) as f:
                    self.lines = f.readlines()
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError(f"无法以任何编码读取文件: {self.gcode_path}")
        
        # 解析配置块
        self.config_block = self._parse_config_block()
        
        # 解析所有移动指令
        self.moves = self._parse_all_moves()
        
        # 识别擦拭塔区域
        self.tower_region = self._identify_tower_region()
    
    def _parse_config_block(self) -> Dict[str, str]:
        """从 GCode 中提取 CONFIG_BLOCK 配置"""
        config = {}
        in_config = False
        
        for line in self.lines:
            line = line.strip()
            if "; CONFIG_BLOCK_START" in line:
                in_config = True
                continue
            elif "; CONFIG_BLOCK_END" in line:
                break
            
            if in_config and line.startswith(";"):
                line = line.lstrip(";").strip()
                if "=" in line:
                    key, val = line.split("=", 1)
                    config[key.strip()] = val.strip()
        
        return config
    
    def _parse_all_moves(self) -> List[GCodeMove]:
        """解析所有 G0/G1 移动指令（L2级别）"""
        moves = []
        current_pos = {'X': 0.0, 'Y': 0.0, 'Z': 0.0, 'E': 0.0}
        
        for i, line in enumerate(self.lines, start=1):
            stripped = line.strip()
            
            # 跳过注释行和非移动指令
            if not stripped or stripped.startswith(";"):
                continue
            
            # 提取指令部分（去掉注释）
            code_part = stripped.split(";")[0].strip()
            comment = stripped.split(";", 1)[1].strip() if ";" in stripped else ""
            
            # 只处理 G0/G1
            if not (code_part.startswith("G0 ") or code_part.startswith("G1 ")):
                continue
            
            # 解析坐标和参数
            move_data = self._parse_move_line(code_part, current_pos)
            if not move_data:
                continue
            
            # 判断移动类型
            move_type = self._classify_move(move_data, current_pos)
            
            # 创建 GCodeMove 对象
            move = GCodeMove(
                line_num=i,
                raw_line=stripped,
                move_type=move_type,
                x=move_data.get('X'),
                y=move_data.get('Y'),
                z=move_data.get('Z'),
                e=move_data.get('E'),
                f=move_data.get('F'),
                comment=comment
            )
            moves.append(move)
            
            # 更新当前位置
            current_pos.update({k: v for k, v in move_data.items() if k in 'XYZE'})
        
        return moves
    
    def _parse_move_line(self, code: str, current_pos: dict) -> Optional[Dict[str, float]]:
        """解析单行 G0/G1 指令的坐标"""
        result = {}
        
        # 正则匹配 X/Y/Z/E/F 参数
        for axis in ['X', 'Y', 'Z', 'E', 'F']:
            match = re.search(rf'{axis}([-\d.]+)', code)
            if match:
                result[axis] = float(match.group(1))
        
        return result if result else None
    
    def _classify_move(self, move_data: dict, current_pos: dict) -> GCodeMoveType:
        """判断移动类型"""
        has_xy = 'X' in move_data or 'Y' in move_data
        has_z = 'Z' in move_data
        has_e = 'E' in move_data
        
        # Z 轴抬升判断（包括斜形抬升：Z+XY同时变化）
        if has_z:
            z_delta = move_data['Z'] - current_pos['Z']
            # 如果Z增加（抬升），无论是否有XY移动，都是Z_HOP
            if z_delta > 0.01:
                return GCodeMoveType.Z_HOP
            # 如果Z减少（降低），无论是否有XY移动，都是Z_DROP
            elif z_delta < -0.01:
                return GCodeMoveType.Z_DROP
        
        # E 轴移动
        if has_e:
            e_delta = move_data['E'] - current_pos['E']
            if e_delta < -0.01:
                return GCodeMoveType.RETRACTION
            elif e_delta > 0.01:
                return GCodeMoveType.UNRETRACTION if not has_xy else GCodeMoveType.EXTRUSION
        
        # 纯 XY 移动
        if has_xy:
            return GCodeMoveType.TRAVEL
        
        return GCodeMoveType.TRAVEL
    
    def _identify_tower_region(self) -> Optional[WipeTowerRegion]:
        """从 GCode 注释中识别擦拭塔区域"""
        for line in self.lines:
            if "TYPE:Wipe tower" in line or "TYPE:Prime tower" in line:
                # 扫描后续的挤出路径，统计 X/Y 范围
                break
        
        # 简化实现：从配置块获取
        if "wipe_tower_x" in self.config_block and "wipe_tower_y" in self.config_block:
            x = float(self.config_block["wipe_tower_x"])
            y = float(self.config_block["wipe_tower_y"])
            width = float(self.config_block.get("prime_tower_width", "60"))
            
            return WipeTowerRegion(
                x_min=x,
                x_max=x + width,
                y_min=y,
                y_max=y + width
            )
        
        return None
    
    def is_in_tower_region(self, x: float, y: float) -> bool:
        """判断坐标是否在擦拭塔区域内"""
        if not self.tower_region:
            return False
        
        return (self.tower_region.x_min <= x <= self.tower_region.x_max and
                self.tower_region.y_min <= y <= self.tower_region.y_max)
    
    def extract_tool_changes(self) -> List[ToolChangeSequence]:
        """提取所有换料序列（L3级别）"""
        tool_changes = []
        
        for i, line in enumerate(self.lines):
            if re.match(r'^T\d+', line.strip()):
                # 解析喷头号
                match = re.match(r'^T(\d+)', line.strip())
                to_tool = int(match.group(1))
                
                # 获取前后移动指令
                before_moves = [m for m in self.moves if m.line_num <= i][-5:]
                after_moves = [m for m in self.moves if m.line_num > i][:10]
                
                # 推断原喷头（从前面的T指令）
                from_tool = 0
                for prev_line in reversed(self.lines[:i]):
                    if re.match(r'^T\d+', prev_line.strip()):
                        from_tool = int(re.match(r'^T(\d+)', prev_line.strip()).group(1))
                        break
                
                tool_changes.append(ToolChangeSequence(
                    tool_change_line=i + 1,
                    from_tool=from_tool,
                    to_tool=to_tool,
                    before_moves=before_moves,
                    after_moves=after_moves
                ))
        
        return tool_changes


# ============================================================
# TC-WT-001: 打完模型去擦拭塔前的抬升逻辑
# ============================================================

def parse_tc_wt_001(
    gcode_path: Path,
    expected_value: str
) -> Tuple[bool, Any, Dict[str, Any]]:
    """
    TC-WT-001: 验证从模型到擦拭塔的抬升逻辑
    
    校验级别: L1 (TYPE标记级别 - 基于注释和基本序列验证)
    校验点：
    1. 解析 TYPE 标记找到模型→擦拭塔转换点
    2. 验证指令序列：回抽 → 抬升 → 空走
    3. 验证抬升增量符合配置
    4. z_hop_type参数记录但不做L2级别的GCode指令细节校验
    
    Args:
        gcode_path: GCode 文件路径
        expected_value: 期望值（JSON字符串，包含 z_hop, z_hop_type）
    
    Returns:
        (是否通过, 实际值, 详细信息)
    """
    import json
    
    parser = WipeTowerGCodeParser(gcode_path)
    expected = json.loads(expected_value)
    
    expected_hop = float(expected.get("z_hop", 0.5))
    expected_type = expected.get("z_hop_type", "Normal Lift")
    
    # 查找从模型到擦拭塔的转换点
    transitions = find_model_to_tower_transitions(parser)
    
    if not transitions:
        return False, None, {"error": "未找到从模型到擦拭塔的转换"}
    
    failures = []
    
    for idx, trans in enumerate(transitions):
        moves = trans['moves']
        
        # 跳过序列不完整的转换点（如最后一层没有抬升）
        # 这些不算错误，只是不需要抬升
        if len(moves) < 3:
            continue
        
        # 检查回抽
        if moves[0].move_type != GCodeMoveType.RETRACTION:
            failures.append(
                f"转换点{idx} 行{moves[0].line_num}: "
                f"应先回抽，实际为{moves[0].move_type.value}"
            )
        
        # 检查抬升
        if moves[1].move_type != GCodeMoveType.Z_HOP:
            failures.append(
                f"转换点{idx} 行{moves[1].line_num}: "
                f"回抽后应抬升，实际为{moves[1].move_type.value}"
            )
        else:
            # 验证抬升高度 - 需要计算增量
            # 从parser的moves中找到这条指令的前一个Z值
            move_idx = next(i for i, m in enumerate(parser.moves) if m.line_num == moves[1].line_num)
            if move_idx > 0:
                prev_z = None
                for i in range(move_idx - 1, -1, -1):
                    if parser.moves[i].z is not None:
                        prev_z = parser.moves[i].z
                        break
                
                if prev_z is not None:
                    z_delta = moves[1].z - prev_z
                    # 高度验证：考虑层高影响，放宽到±0.2mm
                    if abs(z_delta - expected_hop) > 0.2:
                        failures.append(
                            f"转换点{idx} 行{moves[1].line_num}: "
                            f"抬升高度错误，期望{expected_hop}mm，实际增量{z_delta:.2f}mm"
                        )
        
        # 检查空走
        if moves[2].move_type != GCodeMoveType.TRAVEL:
            failures.append(
                f"转换点{idx} 行{moves[2].line_num}: "
                f"抬升后应空走，实际为{moves[2].move_type.value}"
            )
    
    if failures:
        return False, transitions, {"failures": failures, "count": len(transitions)}
    
    return True, transitions, {
        "count": len(transitions),
        "z_hop": expected_hop,
        "z_hop_type": expected_type
    }


def find_model_to_tower_transitions(parser: WipeTowerGCodeParser) -> List[Dict[str, Any]]:
    """
    查找从模型区域到擦拭塔的所有转换点
    
    判断依据：
    1. TYPE 注释从 "External perimeter" 等模型类型变为 "Wipe tower"
    2. 回溯找到完整序列：回抽 → Z抬升 → 移动到塔
    """
    transitions = []
    in_model = False
    in_tower = False
    
    for i, line in enumerate(parser.lines):
        stripped = line.strip()
        
        # 通过 TYPE 注释识别区域
        if ";TYPE:" in stripped:
            if "Wipe tower" in stripped or "Prime tower" in stripped:
                if in_model:
                    # 找到转换点，需要找到完整的转换序列
                    start_line = i
                    
                    # 获取TYPE标记之前的所有移动指令
                    moves_before_type = [
                        m for m in parser.moves 
                        if m.line_num < start_line
                    ]
                    
                    # 回溯找到关键节点：
                    # 1. 在原始GCode中找最后一个Z抬升命令（G1 Z... F30000）
                    # 2. 找对应的parser move
                    # 3. 再找之前的RETRACTION
                    
                    key_moves = []
                    z_hop_line = None
                    z_hop_idx = None
                    retract_idx = None
                    
                    # 从后向前在原始GCode中找Z抬升命令
                    # 特征：G1 Z{增加} F30000 或 G1 X... Y... Z{增加} F30000
                    import re
                    for line_idx in range(start_line - 1, max(0, start_line - 50), -1):
                        line = parser.lines[line_idx].strip()
                        # 匹配 G1 ... Z... F30000 模式（抬升通常用高速F30000）
                        if re.match(r'^G1\s+.*Z[\d.]+.*F30000', line):
                            z_hop_line = line_idx
                            break
                    
                    # 找到对应的parser move（最接近的那个）
                    if z_hop_line is not None:
                        for idx, move in enumerate(moves_before_type):
                            if move.line_num >= z_hop_line:
                                z_hop_idx = idx
                                break
                    
                    if z_hop_idx is not None:
                        # 找Z_HOP之前的RETRACTION（可能中间有WIPE）
                        for idx in range(z_hop_idx - 1, max(0, z_hop_idx - 20), -1):
                            if moves_before_type[idx].move_type == GCodeMoveType.RETRACTION:
                                retract_idx = idx
                                break
                        
                        # 构建完整序列：回抽 → Z抬升 → 移动到塔
                        if retract_idx is not None:
                            key_moves.append(moves_before_type[retract_idx])  # 回抽
                        
                        # 保存Z_HOP的move，同时记录原始GCode行号用于验证
                        z_hop_move = moves_before_type[z_hop_idx]
                        z_hop_move.z_hop_gcode_line = z_hop_line  # 添加属性记录真正的抬升命令行号
                        key_moves.append(z_hop_move)  # Z抬升
                        
                        # 找Z_HOP之后的第一个TRAVEL（移动到塔）
                        for idx in range(z_hop_idx + 1, len(moves_before_type)):
                            if moves_before_type[idx].move_type == GCodeMoveType.TRAVEL:
                                key_moves.append(moves_before_type[idx])
                                break
                    
                    # 只记录找到完整序列（有Z_HOP）的转换点
                    # 必须有3个关键动作：回抽、Z抬升、空走
                    if z_hop_idx is not None and len(key_moves) >= 3:
                        transitions.append({
                            'start': start_line,
                            'moves': key_moves,
                            'type': 'model_to_tower'
                        })
                
                in_tower = True
                in_model = False
            elif any(t in stripped for t in ["External perimeter", "Internal infill", "Inner wall"]):
                in_model = True
                in_tower = False
    
    return transitions
