# 擦拭塔功能测试用例设计文档

**文档版本**: 2.0  
**生成日期**: 2026-01-27  
**基于Bug数量**: 78  
**测试范围**: Creality Print 擦拭塔功能（Bug来源版本未知，参考版本6.2.0为正确基线）  
**Bug来源**: 禅道系统 (https://zentao.creality.com)

---

## 1. 测试概述

本测试用例文档基于78个已记录的擦拭塔相关Bug，覆盖层内换色、层间换色、不同耗材类型、擦拭塔结构等多个维度的测试场景。

### 1.1 测试目标
- 验证擦拭塔打印路径的正确性
- 验证回抽/装填逻辑的准确性
- 验证抬升/降Z动作的合理性
- 验证不同换色场景下的行为一致性
- 验证特殊配置下的边界情况

### 1.2 源码分析基础

**核心源文件**：
- `WipeTowerCreality.cpp/hpp` - Creality擦拭塔实现
- `WipeTowerCrealityCFS.cpp/hpp` - CFS机型特殊实现
- `WipeTower.hpp` - 基类定义（ToolChangeResult结构）
- `PrintConfig.cpp` - 配置参数定义

**关键函数调用链**：
```
tool_change()
  ↓
toolchange_Unload()    // 卸载当前材料（回抽）
  ↓
toolchange_Change()    // 执行换料指令（T0/T1）
  ↓
toolchange_Wipe()      // 擦拭塔填充和外墙打印
  ↓
construct_tcr()        // 构造ToolChangeResult返回GCode
```

**核心配置参数**（from PrintConfig.cpp）：
- `retraction_length` - 回抽长度
- `z_hop` / `z_hop_types` - 抬升高度和方式
- `wipe_tower_no_sparse_layers` - 无稀疏层开关
- `retract_length_toolchange` - 换料时回抽长度

### 1.3 测试分类

| 类别 | Bug数量 | 校验级别 | Bug严重度 |
|------|---------|----------|-----------|
| 抬升/降Z逻辑 | 18 | L2/L3 | P0（致命/严重） |
| 回抽/装填逻辑 | 25 | L2/L3 | P0（致命/严重） |
| 路径规划 | 12 | L2 | P1（一般） |
| 换色场景 | 15 | L3 | P0（严重） |
| 速度/参数控制 | 5 | L1 | P2（轻微） |
| 特殊配置 | 3 | L2 | P1（一般） |

**校验级别说明**：
- **L1**（简单对比）：从CONFIG_BLOCK提取参数值直接对比
- **L2**（GCode解析）：解析GCode指令（G0/G1、E值、F值、坐标）
- **L3**（复杂逻辑）：跨层分析、状态机追踪、序列验证

**Bug严重度说明**：
- **P0（致命/严重）**：导致打印失败、碰撞、质量极差
- **P1（一般）**：影响效率或局部质量，但能完成
- **P2（轻微）**：优化项，不影响基本功能

### 1.4 测试用例与Bug映射表

| 测试用例 | 覆盖Bug数 | Bug ID列表 | 主要问题 |
|---------|----------|-----------|---------|
| **TC-WT-001** | 5 | 10735, 11182, 11193, 11320, 13826 | 模型到擦拭塔外墙时无抬升 |
| **TC-WT-002** | 1 | 10736 | 换料后到擦拭塔缺少Z高度保护 |
| **TC-WT-003** | 4 | 11320, 13570, 13826, 13813 | 擦拭塔到模型的抬升逻辑错误 |
| **TC-WT-004** | 5 | 11457, 13346, 13364, 13366, 13851 | 多余抬升（不应抬升的场景） |
| **TC-WT-005** | 5 | 10737, 10754, 11279, 11340, 11464 | 重复回抽问题 |
| **TC-WT-006** | 6 | 10753, 11184, 11473, 13277, 13334, 13533 | 重复装填或缺少装填 |
| **TC-WT-007** | 9 | 11460, 11462, 11463, 13303, 13309, 13379, 13534, 13537, 13555 | 不同耗材类型回抽/装填量错误 |
| **TC-WT-008** | 2 | 10738, 11185 | 回抽速度错误 |
| **TC-WT-009** | 1 | 13283 | 擦嘴线回抽装填问题 |
| **TC-WT-010** | 8 | 11183, 11187, 11189, 11272, 11467, 13279, 13285, 13349 | 多余路径/路径冗余 |
| **TC-WT-011** | 3 | 11188, 11190, 13655 | 擦嘴动作和擦嘴线缺失 |
| **TC-WT-012** | 1 | 11339 | Z轴保护动作位置错误 |
| **TC-WT-013** | 1 | 13653 | 擦拭塔内部空走速度未设置 |
| **TC-WT-014** | 13 | 11182~11194, 13277~13285 | 层内换色综合问题 |
| **TC-WT-015** | 19 | 10753~10755, 11193, 11471, 13334~13851 | 层间换色综合问题 |
| **TC-WT-016** | 12 | 11460~11464, 13303~13384 | 不同耗材类型换色问题 |
| **TC-WT-017** | 5 | 11329, 13364, 13366, 13533, 13826 | 无稀疏层配置问题 |
| **TC-WT-018** | 3 | 13570, 13607, 13851 | 关闭擦拭塔缺口问题 |
| **TC-WT-019** | 2 | 13275, 13276 | CFS-C机型特殊问题 |
| **TC-WT-020** | 5 | 11280, 11459, 13344, 13377, 13381 | 回抽擦拭位置和时机错误 |
| **TC-WT-021** | 3 | 11471, 13352, 13282 | 擦拭塔打印顺序错误 |
| **TC-WT-022** | 2 | 11192, 11194 | 擦拭塔分区打印问题 |
| **TC-WT-023** | 3 | 10735, 11456, 11461 | 抬升方式参数不生效 |
| **TC-WT-024** | 1 | 13395 | T指令拆解自定义GCode失效 |
| **TC-WT-025** | 1 | 13511 | 回抽量参数修改不生效 |
| **TC-WT-026** | 3 | 13278, 13496, 13624 | 换料前回抽动作异常 |
| **TC-WT-027** | 3 | 13608, 13621, 13704 | 装填逻辑错误 |
| **总计** | **27用例** | **78个Bug** | **100%覆盖** |

**Bug覆盖统计**：
- 抬升/降Z逻辑：18个Bug → TC-WT-001~004（4个用例）
- 回抽/装填逻辑：25个Bug → TC-WT-005~009（5个用例）
- 路径规划：12个Bug → TC-WT-010~013（4个用例）
- 换色场景：15个Bug → TC-WT-014~016（3个用例）
- 特殊配置：6个Bug → TC-WT-017~019（3个用例）
- 回抽擦拭：5个Bug → TC-WT-020（1个用例）
- 打印顺序：5个Bug → TC-WT-021~022（2个用例）
- 参数控制：5个Bug → TC-WT-023~025（3个用例）
- 边界异常：6个Bug → TC-WT-026~027（2个用例）

**重点关注**（P0级别，多Bug聚集）：
- 🔴 TC-WT-015：层间换色（19个Bug）
- 🔴 TC-WT-014：层内换色（13个Bug）
- 🔴 TC-WT-016：不同耗材换色（12个Bug）
- 🔴 TC-WT-007：回抽/装填量计算（9个Bug）
- 🔴 TC-WT-010：多余路径（8个Bug）

---

## 2. GCode解析工具类设计

### 2.1 核心解析类

```python
"""
擦拭塔GCode解析工具类
基于WipeTowerCreality源码逻辑设计
"""
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class GCodeMoveType(Enum):
    """移动类型枚举"""
    TRAVEL = "travel"          # 空走（G0）
    EXTRUSION = "extrusion"    # 挤出打印（G1 with E+）
    RETRACTION = "retraction"  # 回抽（G1 with E-）
    UNRETRACTION = "unretraction"  # 装填（G1 with E+但不移动XY）
    Z_HOP = "z_hop"            # Z轴抬升（G0/G1 with Z+）
    Z_DROP = "z_drop"          # Z轴下降（G0/G1 with Z-）

@dataclass
class GCodeMove:
    """单条GCode移动指令"""
    line_num: int
    command: str       # G0/G1
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    e: Optional[float] = None  # 挤出量（相对值）
    f: Optional[float] = None  # 速度(mm/min)
    comment: str = ""
    
    @property
    def move_type(self) -> GCodeMoveType:
        """识别移动类型"""
        if self.e is not None:
            if self.e < 0:
                return GCodeMoveType.RETRACTION
            elif self.x is None and self.y is None:
                return GCodeMoveType.UNRETRACTION
            else:
                return GCodeMoveType.EXTRUSION
        elif self.z is not None:
            return GCodeMoveType.Z_HOP if self.z > 0 else GCodeMoveType.Z_DROP
        else:
            return GCodeMoveType.TRAVEL
    
    @property
    def xy_distance(self) -> float:
        """XY平面移动距离"""
        if self.x is None or self.y is None:
            return 0.0
        return ((self.x ** 2) + (self.y ** 2)) ** 0.5

@dataclass
class WipeTowerRegion:
    """擦拭塔区域定义（from WipeTower::box_coordinates）"""
    ld: Tuple[float, float]  # left down
    rd: Tuple[float, float]  # right down
    lu: Tuple[float, float]  # left up
    ru: Tuple[float, float]  # right up
    
    def contains(self, x: float, y: float) -> bool:
        """判断点是否在擦拭塔区域内"""
        return (self.ld[0] <= x <= self.rd[0] and 
                self.ld[1] <= y <= self.lu[1])

@dataclass
class ToolChangeSequence:
    """换料序列（对应WipeTower::ToolChangeResult）"""
    layer_num: int
    z_height: float
    old_tool: int
    new_tool: int
    start_line: int
    end_line: int
    moves: List[GCodeMove]
    
    # 关键位置索引
    retract_before_change: Optional[int] = None
    tool_change_line: Optional[int] = None
    unretract_after_change: Optional[int] = None
    
    def get_phase_moves(self, phase: str) -> List[GCodeMove]:
        """获取特定阶段的移动序列
        
        phase可选值:
        - 'unload': toolchange_Unload阶段
        - 'change': toolchange_Change阶段
        - 'wipe': toolchange_Wipe阶段（填充+外墙）
        """
        # 根据源码中的注释标记划分
        # ";toolchange_change ################"
        pass

class WipeTowerGCodeParser:
    """擦拭塔GCode解析器"""
    
    def __init__(self, gcode_path: Path):
        self.gcode_path = gcode_path
        self.lines = self._load_gcode()
        self.moves: List[GCodeMove] = []
        self.tower_region: Optional[WipeTowerRegion] = None
        self.tool_changes: List[ToolChangeSequence] = []
        
    def _load_gcode(self) -> List[str]:
        """加载GCode文件"""
        with open(self.gcode_path, 'r', encoding='utf-8') as f:
            return f.readlines()
    
    def parse_config_block(self) -> Dict[str, any]:
        """L1级别：解析CONFIG_BLOCK
        
        提取关键参数：
        - retraction_length[T0/T1]
        - z_hop[T0/T1]
        - wipe_tower_no_sparse_layers
        """
        config = {}
        in_config = False
        
        for line in self.lines:
            if "; CONFIG_BLOCK_START" in line:
                in_config = True
            elif "; CONFIG_BLOCK_END" in line:
                break
            elif in_config and "=" in line:
                key, value = line.strip("; \n").split("=", 1)
                config[key] = value
        
        return config
    
    def parse_all_moves(self) -> List[GCodeMove]:
        """L2级别：解析所有移动指令"""
        moves = []
        current_pos = {'x': 0.0, 'y': 0.0, 'z': 0.0, 'e': 0.0}
        
        for line_num, line in enumerate(self.lines, 1):
            line = line.strip()
            if not line or line.startswith(';'):
                continue
            
            # 分离指令和注释
            parts = line.split(';', 1)
            cmd_part = parts[0].strip()
            comment = parts[1].strip() if len(parts) > 1 else ""
            
            if not cmd_part.startswith(('G0', 'G1')):
                continue
            
            # 解析坐标和E值
            move = self._parse_move_line(line_num, cmd_part, current_pos, comment)
            if move:
                moves.append(move)
                # 更新当前位置
                if move.x is not None:
                    current_pos['x'] = move.x
                if move.y is not None:
                    current_pos['y'] = move.y
                if move.z is not None:
                    current_pos['z'] = move.z
                if move.e is not None:
                    current_pos['e'] += move.e  # E是相对值
        
        self.moves = moves
        return moves
    
    def _parse_move_line(self, line_num: int, cmd: str, 
                         current_pos: Dict, comment: str) -> Optional[GCodeMove]:
        """解析单条移动指令"""
        import re
        
        command = cmd.split()[0]  # G0 or G1
        
        # 提取坐标和速度
        x = self._extract_value(cmd, 'X', current_pos['x'])
        y = self._extract_value(cmd, 'Y', current_pos['y'])
        z = self._extract_value(cmd, 'Z', current_pos['z'])
        e = self._extract_value(cmd, 'E', None, relative=True)
        f = self._extract_value(cmd, 'F', None, relative=False)
        
        return GCodeMove(
            line_num=line_num,
            command=command,
            x=x, y=y, z=z, e=e, f=f,
            comment=comment
        )
    
    def _extract_value(self, cmd: str, axis: str, default: Optional[float], 
                       relative: bool = False) -> Optional[float]:
        """从指令中提取轴值"""
        import re
        match = re.search(f'{axis}([-+]?\\d*\\.?\\d+)', cmd)
        if match:
            value = float(match.group(1))
            return value if relative else value
        return default if not relative else None
    
    def identify_tower_region(self) -> WipeTowerRegion:
        """识别擦拭塔区域坐标
        
        方法：查找注释中的擦拭塔标记
        "; CP TOOLCHANGE START"
        ";--------------------"
        """
        # 从第一次换料的坐标推断擦拭塔位置
        for i, line in enumerate(self.lines):
            if "; CP TOOLCHANGE START" in line:
                # 找到换料起始位置
                for j in range(i, min(i+20, len(self.lines))):
                    if self.moves and j < len(self.moves):
                        move = self.moves[j]
                        if move.x and move.y:
                            # 假设擦拭塔大小为30x30（默认值）
                            self.tower_region = WipeTowerRegion(
                                ld=(move.x - 15, move.y - 15),
                                rd=(move.x + 15, move.y - 15),
                                lu=(move.x - 15, move.y + 15),
                                ru=(move.x + 15, move.y + 15)
                            )
                            return self.tower_region
        
        return None
    
    def extract_tool_changes(self) -> List[ToolChangeSequence]:
        """L3级别：提取所有换料序列
        
        识别标记：
        - "; CP TOOLCHANGE START"
        - " toolchange #X"
        - "; CP TOOLCHANGE END"
        """
        sequences = []
        current_seq = None
        
        for i, line in enumerate(self.lines):
            if "; CP TOOLCHANGE START" in line:
                # 开始新的换料序列
                current_seq = {
                    'start_line': i,
                    'moves': [],
                    'layer': None,
                    'z': None
                }
            elif "; CP TOOLCHANGE END" in line and current_seq:
                # 结束当前序列
                current_seq['end_line'] = i
                sequences.append(current_seq)
                current_seq = None
            elif current_seq and i < len(self.moves):
                # 收集序列内的移动
                current_seq['moves'].append(self.moves[i])
        
        # 转换为ToolChangeSequence对象
        self.tool_changes = [
            ToolChangeSequence(
                layer_num=seq.get('layer', 0),
                z_height=seq.get('z', 0.0),
                old_tool=-1,  # 需要从T指令解析
                new_tool=-1,
                start_line=seq['start_line'],
                end_line=seq['end_line'],
                moves=seq['moves']
            )
            for seq in sequences
        ]
        
        return self.tool_changes
    
    def find_retractions_at(self, position: str, 
                            window: int = 10) -> List[GCodeMove]:
        """查找特定位置的回抽动作
        
        position可选值:
        - 'before_tool_change': 换料前
        - 'after_infill': 填充后
        - 'after_wall': 外墙后
        - 'before_model': 返回模型前
        """
        retractions = []
        
        for move in self.moves:
            if move.move_type == GCodeMoveType.RETRACTION:
                # 根据position判断是否符合条件
                context = self._get_move_context(move, window)
                if self._match_position(context, position):
                    retractions.append(move)
        
        return retractions
    
    def _get_move_context(self, move: GCodeMove, window: int) -> Dict:
        """获取移动的上下文（前后window行）"""
        idx = self.moves.index(move)
        return {
            'before': self.moves[max(0, idx-window):idx],
            'after': self.moves[idx+1:min(len(self.moves), idx+window+1)]
        }
    
    def _match_position(self, context: Dict, position: str) -> bool:
        """匹配位置条件"""
        # 根据context中的注释和移动模式判断
        # 例如：找到"tool_change"注释表示换料位置
        pass
    
    def count_retractions_between(self, start_line: int, end_line: int) -> int:
        """统计指定行范围内的回抽次数（L2验证）"""
        count = 0
        for move in self.moves:
            if (start_line <= move.line_num <= end_line and 
                move.move_type == GCodeMoveType.RETRACTION):
                count += 1
        return count
    
    def verify_retraction_amount(self, tool: int, 
                                 expected: float, 
                                 tolerance: float = 0.1) -> bool:
        """验证回抽量是否匹配配置（L2验证）"""
        config = self.parse_config_block()
        actual = float(config.get(f'retraction_length[{tool}]', 0))
        return abs(actual - expected) <= tolerance
    
    def verify_sequence(self, sequence_name: str) -> bool:
        """L3级别：验证动作序列
        
        sequence_name可选值:
        - 'retract_lift_travel': 回抽→抬升→空走
        - 'travel_drop_unretract': 空走→降Z→装填
        - 'unload_change_wipe': 卸载→换料→擦拭
        """
        expected_sequences = {
            'retract_lift_travel': [
                GCodeMoveType.RETRACTION,
                GCodeMoveType.Z_HOP,
                GCodeMoveType.TRAVEL
            ],
            'travel_drop_unretract': [
                GCodeMoveType.TRAVEL,
                GCodeMoveType.Z_DROP,
                GCodeMoveType.UNRETRACTION
            ]
        }
        
        if sequence_name not in expected_sequences:
            return False
        
        expected = expected_sequences[sequence_name]
        
        # 在所有移动中查找匹配的序列
        for i in range(len(self.moves) - len(expected) + 1):
            window = self.moves[i:i+len(expected)]
            types = [m.move_type for m in window]
            if types == expected:
                return True
        
        return False
    
    def analyze_path_redundancy(self, start: GCodeMove, 
                                end: GCodeMove) -> float:
        """L2级别：分析路径冗余度
        
        返回：(实际路径长度 - 直线距离) / 直线距离
        """
        import math
        
        # 直线距离
        direct_dist = math.sqrt(
            (end.x - start.x)**2 + (end.y - start.y)**2
        )
        
        # 实际路径长度
        start_idx = self.moves.index(start)
        end_idx = self.moves.index(end)
        
        actual_dist = 0.0
        for i in range(start_idx, end_idx):
            m1, m2 = self.moves[i], self.moves[i+1]
            if m1.x and m1.y and m2.x and m2.y:
                actual_dist += math.sqrt(
                    (m2.x - m1.x)**2 + (m2.y - m1.y)**2
                )
        
        if direct_dist == 0:
            return 0.0
        
        redundancy = (actual_dist - direct_dist) / direct_dist
        return redundancy
```

### 2.2 辅助验证函数

```python
def verify_lift_before_travel(parser: WipeTowerGCodeParser, 
                              context: str = "model_to_tower") -> bool:
    """验证抬升时机（TC-WT-001）
    
    检查：从模型到擦拭塔时是否先回抽→抬升→再空走
    """
    # 找到从模型区域到擦拭塔区域的空走
    for i, move in enumerate(parser.moves[:-1]):
        next_move = parser.moves[i+1]
        
        # 判断是否从模型到擦拭塔
        if (not parser.tower_region.contains(move.x, move.y) and
            parser.tower_region.contains(next_move.x, next_move.y)):
            
            # 检查前面的动作序列
            if i >= 2:
                retract = parser.moves[i-2]
                lift = parser.moves[i-1]
                
                if (retract.move_type == GCodeMoveType.RETRACTION and
                    lift.move_type == GCodeMoveType.Z_HOP and
                    move.move_type == GCodeMoveType.TRAVEL):
                    return True
    
    return False

def verify_material_switch_params(parser: WipeTowerGCodeParser,
                                  from_material: str, 
                                  to_material: str,
                                  expected_retract: Dict[str, float]) -> bool:
    """验证耗材切换时参数应用（TC-WT-007）
    
    检查：切换前最后一次回抽量 = from_material参数
          切换后第一次装填量 = to_material参数
    """
    # 找到T指令（换料点）
    tool_change_line = None
    for i, line in enumerate(parser.lines):
        if line.strip() in ['T0', 'T1']:
            tool_change_line = i
            break
    
    if not tool_change_line:
        return False
    
    # 检查换料前的回抽
    for move in reversed(parser.moves[:tool_change_line]):
        if move.move_type == GCodeMoveType.RETRACTION:
            last_retract = abs(move.e)
            if abs(last_retract - expected_retract[from_material]) > 0.1:
                return False
            break
    
    # 检查换料后的装填
    for move in parser.moves[tool_change_line:]:
        if move.move_type == GCodeMoveType.UNRETRACTION:
            first_unretract = move.e
            if abs(first_unretract - expected_retract[to_material]) > 0.1:
                return False
            break
    
    return True

def verify_print_order(parser: WipeTowerGCodeParser, 
                       layer_num: int,
                       expected_order: List[str]) -> bool:
    """验证擦拭塔打印顺序（TC-WT-021）
    
    expected_order示例: ['purge_line', 'wall', 'infill']
    """
    # 提取该层的擦拭塔部分
    # 根据注释标记识别：
    # - "purge_line" / "PURGE LINE"
    # - "OUTER WALL" / "outer perimeter"
    # - "infill" / "INFILL"
    
    actual_order = []
    in_tower = False
    
    for line in parser.lines:
        # 层标记
        if f"wipe tower layer #{layer_num}" in line.lower():
            in_tower = True
        elif f"wipe tower layer #{layer_num+1}" in line.lower():
            break
        
        if in_tower:
            if "purge" in line.lower() or "擦嘴线" in line:
                if 'purge_line' not in actual_order:
                    actual_order.append('purge_line')
            elif "outer" in line.lower() or "perimeter" in line.lower():
                if 'wall' not in actual_order:
                    actual_order.append('wall')
            elif "infill" in line.lower() or "填充" in line:
                if 'infill' not in actual_order:
                    actual_order.append('infill')
    
    return actual_order == expected_order
```

---

## 3. 测试场景分类

### 3.1 抬升/降Z逻辑测试（P0 - 致命/严重）

#### TC-WT-001: 模型到擦拭塔外墙的抬升
**Bug ID**: 10735, 11182, 11193, 11320, 13826  
**校验级别**: L1（TYPE标记 + 基本序列验证）  
**测试目的**: 验证从模型区域移动到擦拭塔外墙时的抬升行为（关注是否抬升、抬升高度，不区分抬升方式的实现细节）

**源码依据**：
```cpp
// WipeTowerCreality.cpp - tool_change()
// 期望序列:
writer.retract(-retract_length, retract_speed);          // 1. 回抽
writer.z_hop(z_hop_height, z_hop_speed);                 // 2. 抬升
writer.travel(tower_x, tower_y, travel_speed);           // 3. 空走到擦拭塔
writer.z_hop_reset();                                     // 4. 降Z
writer.retract(+retract_length, retract_speed);          // 5. 装填
```

**前置条件**:
- 启用擦拭塔外墙打印
- 设置抬升方式参数（`z_hop_types`: 垂直/梯形）
- 配置抬升高度（`z_hop`参数）

**测试步骤**:
```python
def test_lift_from_model_to_tower():
    parser = WipeTowerGCodeParser(gcode_file)
    parser.parse_all_moves()
    parser.identify_tower_region()
    
    # 1. 找到从模型到擦拭塔的转换点
    transitions = find_model_to_tower_transitions(parser)
    
    for trans in transitions:
        # 2. 验证序列：回抽 → 抬升 → 空走
        moves = parser.moves[trans['start']-3:trans['start']+1]
        
        assert moves[0].move_type == GCodeMoveType.RETRACTION, \
            f"Line {moves[0].line_num}: 应先回抽"
        
        assert moves[1].move_type == GCodeMoveType.Z_HOP, \
            f"Line {moves[1].line_num}: 回抽后应抬升Z"
        
        assert moves[2].move_type == GCodeMoveType.TRAVEL, \
            f"Line {moves[2].line_num}: 抬升后应空走"
        
        # 3. 验证抬升高度
        config = parser.parse_config_block()
        expected_hop = float(config['z_hop[0]'])  # 假设T0
        actual_hop = moves[1].z
        
        assert abs(actual_hop - expected_hop) < 0.1, \
            f"抬升高度错误: 期望{expected_hop}, 实际{actual_hop}"
```

**期望结果**:
```gcode
G1 E-5.0 F2400           ; 回抽
G0 Z{current_z + hop}    ; 抬升
G0 X{tower_x} Y{tower_y} ; 空走到擦拭塔
```

**测试数据**:
| 参数 | 值1 | 值2 | 值3 |
|------|-----|-----|-----|
| z_hop | 0.5mm | 1.0mm | 2.0mm |
| z_hop_types | vertical | contour | - |
| 模型高度 | 10mm | 50mm | 100mm |

**验证点矩阵**:

| 验证点 | 检查方法 | 期望值 |
|--------|----------|--------|
| 回抽时机 | 检查E值<0的指令位置 | 空走前1-2行 |
| 抬升时机 | 检查Z值增加的指令 | 回抽后立即 |
| 抬升高度 | Z_new - Z_old | = z_hop配置 |
| 抬升方式 | XY坐标是否变化 | 垂直=不变，梯形=变化 |
| 空走目标 | XY坐标 | 在擦拭塔区域内 |

---

#### TC-WT-002: 换料后到擦拭塔的Z高度保护
**Bug ID**: 10736  
**校验级别**: L3（跨区域路径验证）  
**测试目的**: 验证换料完成后移动到擦拭塔前的高度保护动作

**源码依据**：
```cpp
// WipeTowerCreality.cpp - toolchange_Change()
// Bug修复注释：
// "固件bug,临时抬升0.4,防止Z高度错误导致的移动到擦拭塔时产生剐蹭"
writer.relative_zhop(0.4f + m_z_offset, 1200.0f, 
                     "relative_zhop_up_for_firmware G0");
```

**测试步骤**:
```python
def test_lift_after_tool_change():
    parser = WipeTowerGCodeParser(gcode_file)
    tool_changes = parser.extract_tool_changes()
    
    for tc in tool_changes:
        # 找到T指令后的第一个Z抬升
        t_line = tc.tool_change_line
        
        # 检查T指令后5行内是否有Z抬升
        has_lift = False
        for move in parser.moves[t_line:t_line+5]:
            if move.move_type == GCodeMoveType.Z_HOP:
                has_lift = True
                # 验证抬升量 >= 0.4mm (固件保护值)
                assert move.z >= 0.4, \
                    f"Line {move.line_num}: 换料后保护抬升不足"
                break
        
        assert has_lift, f"换料后缺少Z高度保护"
```

**期望结果**:
```gcode
T1                        ; 换料指令
G0 Z{z + 0.4} F1200      ; 保护抬升
G0 X{tower_x} Y{tower_y} ; 平移到擦拭塔
G0 Z{tower_z}            ; 降Z到打印高度
```

**对比验证**:
| 版本 | 换料后动作序列 | 结果 |
|------|----------------|------|
| 6.2.0正确 | T1 → Z抬升 → XY平移 → Z降低 | ✓ |
| Bug版本 | T1 → XY平移（无抬升） | ✗ 可能碰撞 |

---

#### TC-WT-003: 擦拭塔到模型的抬升逻辑
**Bug ID**: 11320, 13570, 13826, 13813  
**校验级别**: L3（路径投影分析）  
**测试目的**: 验证从擦拭塔返回模型区域时的抬升行为

**源码分析**：
```cpp
// Bug 13813根因：当前位置未加上擦拭距离
// 导致抬升坐标计算错误，投影变成折线而非直线

// 正确逻辑应该是：
Vec2f current_pos = writer.pos() + wipe_distance;  // 加上擦拭距离
writer.retract(retract_length, retract_speed);
writer.travel_with_lift(model_pos, lift_height);   // 抬升+空走
```

**测试步骤**:
```python
def test_lift_from_tower_to_model():
    parser = WipeTowerGCodeParser(gcode_file)
    
    # 找到从擦拭塔到模型的转换
    transitions = find_tower_to_model_transitions(parser)
    
    for trans in transitions:
        moves = trans['moves']
        
        # 1. 验证回抽动作存在
        assert moves[0].move_type == GCodeMoveType.RETRACTION
        
        # 2. 验证抬升动作
        assert moves[1].move_type == GCodeMoveType.Z_HOP
        
        # 3. 关键验证：抬升路径在XY平面的投影
        # 梯形抬升时，投影应该是直线
        if is_contour_lift(parser.parse_config_block()):
            # 检查抬升阶段的XY移动
            lift_moves = get_lift_phase_moves(moves)
            
            # 计算投影路径的线性度（R²值）
            linearity = calculate_path_linearity(lift_moves)
            
            assert linearity > 0.95, \
                f"抬升路径投影非直线（R²={linearity}），" \
                f"可能是坐标计算错误（Bug 13813）"

def calculate_path_linearity(moves: List[GCodeMove]) -> float:
    """计算路径的线性度（R²系数）"""
    import numpy as np
    from sklearn.metrics import r2_score
    
    x_coords = [m.x for m in moves if m.x]
    y_coords = [m.y for m in moves if m.y]
    
    if len(x_coords) < 2:
        return 1.0
    
    # 拟合直线
    coeffs = np.polyfit(x_coords, y_coords, 1)
    y_pred = np.polyval(coeffs, x_coords)
    
    # 计算R²
    r2 = r2_score(y_coords, y_pred)
    return r2
```

**特殊场景验证**:

| 配置 | 期望行为 | Bug表现 |
|------|----------|---------|
| 无稀疏层=开启 | 擦拭塔到模型仍需抬升 | ✓ 正确 |
| 缺口=关闭 + 方形塔=关闭 | 打完塔到模型无多余抬升 | ✗ 有多余抬升 |
| 梯形抬升 | XY投影为直线 | ✗ 投影为折线 |

---

#### TC-WT-004: 多余抬升的边界测试
**Bug ID**: 11457, 13346, 13364, 13366, 13851  
**校验级别**: L2（计数验证）  
**测试目的**: 验证不应该抬升的场景中没有多余抬升动作

**测试矩阵**:

| Bug ID | 场景 | 不应抬升的原因 | 验证方法 |
|--------|------|----------------|----------|
| 11457 | 擦拭塔上换料前 | 短距离移动 | 统计Z hop次数=0 |
| 13346 | 填充→模型 | 同层平面移动 | 检查Z值不变 |
| 13364 | 换料后→擦拭塔（无稀疏层） | 已有换料保护抬升 | 统计Z hop ≤ 1 |
| 13366 | 打完塔→模型（无稀疏层） | 同高度移动 | Z值不变 |
| 13851 | 换料后→擦拭塔（关闭缺口） | 直接打印无需抬升 | Z hop次数=0 |

**测试代码**:
```python
@pytest.mark.parametrize("bug_id,scene,max_hops", [
    (11457, "tower_before_tool_change", 0),
    (13346, "infill_to_model", 0),
    (13364, "after_tool_change_no_sparse", 1),
    (13366, "tower_to_model_no_sparse", 0),
    (13851, "after_tool_change_no_gap", 0),
])
def test_no_redundant_lift(gcode_file, bug_id, scene, max_hops):
    parser = WipeTowerGCodeParser(gcode_file)
    
    # 定位到特定场景的移动序列
    scene_moves = identify_scene_moves(parser, scene)
    
    # 统计Z抬升次数
    hop_count = sum(
        1 for m in scene_moves 
        if m.move_type == GCodeMoveType.Z_HOP
    )
    
    assert hop_count <= max_hops, \
        f"Bug {bug_id}: {scene}场景中有{hop_count}次多余抬升"
```



---

### 3.2 回抽/装填逻辑测试（P0 - 致命/严重）

#### TC-WT-005: 重复回抽问题验证
**Bug ID**: 10737, 10754, 11279, 11340, 11464  
**校验级别**: L2（GCode指令统计）  
**测试目的**: 验证回抽动作不会重复执行

**源码依据**：
```cpp
// WipeTowerCreality.cpp
// 正确的回抽只应在关键位置调用一次:
float retract_length = m_filpar[m_current_tool].retract_length;
float retract_speed  = m_filpar[m_current_tool].retract_speed * 60;
writer.retract(retract_length, retract_speed);  // 只调用一次

// Bug场景：可能在finish_layer后再次回抽
// 或在tool_change前已经回抽，换料时又回抽
```

**测试场景矩阵**:

| Bug ID | 场景 | 位置 | 期望回抽次数 | Bug表现 |
|--------|------|------|--------------|---------|
| 10737 | 打完填充+外墙后 | 擦拭塔 | 1次 | 连续2次回抽 |
| 10754 | 层间换色塔到模型 | 擦拭塔→模型 | 1次 | 连续2次回抽 |
| 11279 | 打完擦拭塔去模型前 | 擦拭塔→模型 | 1次 | 完全无回抽 |
| 11340 | 擦拭塔上换料时 | 换料点 | 1次（换料前） | 无回抽 |
| 11464 | 不同耗材换料前 | 换料位置 | 1次 | 连续2次回抽 |

**测试步骤**:
```python
@pytest.mark.parametrize("bug_id,scene,expected_count", [
    (10737, "after_tower_wall", 1),
    (10754, "tower_to_model_layer_change", 1),
    (11279, "tower_to_model", 1),
    (11340, "before_tool_change_on_tower", 1),
    (11464, "before_tool_change_different_material", 1),
])
def test_no_duplicate_retraction(gcode_file, bug_id, scene, expected_count):
    parser = WipeTowerGCodeParser(gcode_file)
    parser.parse_all_moves()
    
    # 定位场景的移动窗口
    scene_window = identify_scene_window(parser, scene)
    
    # 统计回抽次数
    retract_moves = [
        m for m in scene_window 
        if m.move_type == GCodeMoveType.RETRACTION
    ]
    
    actual_count = len(retract_moves)
    
    # 检查连续回抽（间隔<5行视为重复）
    if len(retract_moves) >= 2:
        for i in range(len(retract_moves) - 1):
            gap = retract_moves[i+1].line_num - retract_moves[i].line_num
            assert gap >= 5, \
                f"Bug {bug_id}: Line {retract_moves[i].line_num} 重复回抽(间隔{gap}行)"
    
    assert actual_count == expected_count, \
        f"Bug {bug_id}: {scene}场景回抽{actual_count}次，期望{expected_count}次"

def identify_scene_window(parser: WipeTowerGCodeParser, 
                          scene: str) -> List[GCodeMove]:
    """识别特定场景的移动窗口"""
    if scene == "after_tower_wall":
        # 找到外墙打印结束标记
        for i, line in enumerate(parser.lines):
            if "; OUTER WALL END" in line or "outer perimeter end" in line.lower():
                # 返回后续10行的移动
                return parser.moves[i:i+10]
    
    elif scene == "tower_to_model":
        # 找到从擦拭塔返回模型的转换
        for i, move in enumerate(parser.moves[:-1]):
            next_move = parser.moves[i+1]
            if (parser.tower_region.contains(move.x, move.y) and
                not parser.tower_region.contains(next_move.x, next_move.y)):
                return parser.moves[i-5:i+5]
    
    # ... 其他场景的识别逻辑
    return []
```

**期望结果**:
```gcode
; 正确的单次回抽
G1 E-5.0 F2400    ; 回抽一次
G0 Z{z+hop}       ; 后续动作
G0 X{x} Y{y}

; 错误的重复回抽
G1 E-5.0 F2400    ; 第一次回抽
G1 E-5.0 F2400    ; ✗ 重复回抽（Bug）
```

**验证点**:
- 每个关键位置只有一次回抽
- 回抽量符合参数设置：`abs(E值) == retraction_length[tool]`
- 回抽速度符合配置：`F值 == retraction_speed[tool] * 60`
- 连续回抽间隔 >= 5行（避免误判空走中的小回抽）

---

#### TC-WT-006: 重复装填问题验证
**Bug ID**: 10753, 11184, 11473, 13277, 13334, 13533  
**校验级别**: L2（GCode指令分析）  
**测试目的**: 验证装填动作的时机和次数正确

**源码依据**：
```cpp
// WipeTowerCreality.cpp - finish_layer() 和 tool_change()
// 正确的装填时序：
writer.travel(target_pos);                    // 1. 空走到目标
writer.retract(-retract_length, retract_speed); // 2. 装填（负回抽）
writer.extrude(next_pos, extrude_speed);      // 3. 开始打印

// Bug场景可能：
// - 在travel前就装填（导致空走时拉丝）
// - travel后忘记装填（导致开始打印时缺料）
// - 短距离移动重复装填
```

**场景分类**:

| Bug ID | 场景 | 位置 | 期望行为 | Bug表现 |
|--------|------|------|----------|---------|
| 10753 | 擦嘴线→擦拭塔（首层） | 擦拭塔入口 | 空走后装填1次 | 重复装填2次 |
| 13334 | 擦嘴线→擦拭塔（换色层） | 缺口位置 | 打印前装填1次 | 缺少装填 |
| 11184 | 模型→擦拭塔外墙 | 外墙起点 | 到达后装填 | 无装填 |
| 13277 | 层内换色模型→外墙 | 外墙起点 | 到达后装填 | 缺装填 |
| 11473 | 填充→外墙 | 擦拭塔内 | 正常装填 | 多余装填 |
| 13533 | 换料前模型→塔（无稀疏层） | 换料前 | 装填1次 | 重复装填2次 |

**测试步骤**:
```python
@pytest.mark.parametrize("bug_id,scene,check_point,expected_behavior", [
    (10753, "purge_to_tower_first_layer", "tower_entry", "unretract_once"),
    (13334, "purge_to_tower_change_layer", "gap_position", "unretract_once"),
    (11184, "model_to_tower_wall", "wall_start", "unretract_after_travel"),
    (11473, "infill_to_wall", "wall_start", "no_extra_unretract"),
    (13533, "model_to_tower_before_change", "before_tool_change", "unretract_once"),
])
def test_unretraction_timing(gcode_file, bug_id, scene, check_point, expected_behavior):
    parser = WipeTowerGCodeParser(gcode_file)
    parser.parse_all_moves()
    
    # 定位检查点
    checkpoint_moves = locate_checkpoint(parser, check_point)
    
    if expected_behavior == "unretract_once":
        # 验证只装填一次
        unretracts = [m for m in checkpoint_moves 
                     if m.move_type == GCodeMoveType.UNRETRACTION]
        assert len(unretracts) == 1, \
            f"Bug {bug_id}: {check_point}处装填{len(unretracts)}次，期望1次"
    
    elif expected_behavior == "unretract_after_travel":
        # 验证装填在空走之后
        sequence_types = [m.move_type for m in checkpoint_moves[:5]]
        
        # 查找 TRAVEL → UNRETRACTION 模式
        found_correct_sequence = False
        for i in range(len(sequence_types) - 1):
            if (sequence_types[i] == GCodeMoveType.TRAVEL and
                sequence_types[i+1] == GCodeMoveType.UNRETRACTION):
                found_correct_sequence = True
                break
        
        assert found_correct_sequence, \
            f"Bug {bug_id}: 未找到正确的'空走→装填'序列"
    
    elif expected_behavior == "no_extra_unretract":
        # 验证短距离移动不应装填
        for i, move in enumerate(checkpoint_moves[:-1]):
            next_move = checkpoint_moves[i+1]
            if move.move_type == GCodeMoveType.UNRETRACTION:
                # 检查装填后的移动距离
                travel_dist = ((next_move.x - move.x)**2 + 
                              (next_move.y - move.y)**2)**0.5
                assert travel_dist > 5.0, \
                    f"Bug {bug_id}: Line {move.line_num} 短距离({travel_dist:.2f}mm)多余装填"

def locate_checkpoint(parser: WipeTowerGCodeParser, 
                      checkpoint: str) -> List[GCodeMove]:
    """定位检查点的移动序列"""
    if checkpoint == "tower_entry":
        # 找到进入擦拭塔区域的第一个点
        for i, move in enumerate(parser.moves):
            if parser.tower_region.contains(move.x, move.y):
                return parser.moves[max(0, i-3):i+7]
    
    elif checkpoint == "wall_start":
        # 找到外墙打印起始标记
        for i, line in enumerate(parser.lines):
            if "; OUTER WALL START" in line or "outer perimeter" in line.lower():
                return parser.moves[i-5:i+5]
    
    elif checkpoint == "before_tool_change":
        # 找到T指令前的移动
        for i, line in enumerate(parser.lines):
            if line.strip() in ['T0', 'T1']:
                return parser.moves[max(0, i-10):i]
    
    return []
```

**期望结果时序图**:
```gcode
; 正确的装填时序
G1 E-5.0 F2400           ; 1. 回抽
G0 Z{z+hop}              ; 2. 抬升
G0 X{target} Y{target}   ; 3. 空走到目标（无E值）
G1 E5.0 F2400            ; 4. 装填（恢复回抽量）
G1 X{x} Y{y} E0.1234     ; 5. 开始打印（有挤出）

; 错误示例1：空走前装填
G1 E5.0 F2400            ; ✗ 过早装填
G0 X{target} Y{target}   ; 空走时会拉丝

; 错误示例2：忘记装填
G0 X{target} Y{target}   ; 空走
G1 X{x} Y{y} E0.1234     ; ✗ 直接打印，缺料

; 错误示例3：重复装填
G1 E5.0 F2400            ; 第一次装填
G1 E5.0 F2400            ; ✗ 重复装填
```

**边界条件**:
- 短距离移动（<5mm）可能不需要回抽装填
- 同一打印区域内部移动不需要装填
- 换料后的第一次装填应包含冲料量（可能>回抽量）

**装填量验证**:
```python
def verify_unretraction_amount(parser: WipeTowerGCodeParser,
                               tool: int,
                               context: str) -> bool:
    """验证装填量是否正确
    
    context:
    - 'normal': 普通装填 = 回抽量
    - 'after_tool_change': 换料后装填 = 回抽量 + 冲料量
    - 'after_infill': 填充后装填（可能需要额外补偿）
    """
    config = parser.parse_config_block()
    expected_base = float(config[f'retraction_length[{tool}]'])
    
    if context == 'after_tool_change':
        # 换料后可能有额外装填补偿
        extra = float(config.get(f'retract_restart_extra_toolchange[{tool}]', 0))
        expected = expected_base + extra
    else:
        expected = expected_base
    
    # 查找最近的装填动作
    unretracts = [m for m in parser.moves 
                 if m.move_type == GCodeMoveType.UNRETRACTION]
    
    for unretract in unretracts:
        if abs(unretract.e - expected) < 0.1:
            return True
    
    return False
```

---

#### TC-WT-007: 回抽量和装填量计算
**Bug ID**: 11460, 11462, 11463, 13303, 13309, 13379, 13534, 13537, 13555  
**校验级别**: L2/L3（参数验证 + 状态追踪）  
**测试目的**: 验证不同耗材类型和场景下回抽/装填量的正确性

**源码依据**：
```cpp
// WipeTowerCreality.cpp - set_extruder()
m_filpar[idx].retract_length = config.retraction_length.get_at(idx);
m_filpar[idx].retract_speed  = config.retraction_speed.get_at(idx);

// tool_change() 中使用当前工具的参数
float retract_length = m_filpar[m_current_tool].retract_length;  // 关键！

// Bug: 换料时可能使用了错误工具的参数
// 期望：T0→T1时，换料前用T0参数，换料后用T1参数
// 实际：可能全程使用T0参数
```

**测试矩阵**:

| 耗材组合 | 场景 | 期望回抽量 | 期望装填量 | 相关Bug |
|----------|------|------------|------------|---------|
| PLA+PLA | 层内换色 | 5.0mm | 5.0mm | - |
| PLA+TPU | 层内换色换料前 | 8.0mm (TPU) | - | 11460 |
| PLA+TPU | 擦拭塔填充 | 8.0mm (TPU) | 8.5mm (TPU+补偿) | 11462 |
| PLA+TPU | 擦嘴线处 | 8.0mm (TPU) | 8.5mm (TPU) | 11463 |
| PLA+PETG | 换料后打完填充 | 6.0mm (PETG) | 6.0mm | 13303 |
| PLA+PETG | 填充和外墙 | 6.0mm (PETG) | 6.0mm | 13309 |
| PETG+TPU | 换色前擦拭塔 | 当前工具参数 | - | 13534 |
| PLA+TPU | 层间换色换料前 | TPU参数 | - | 13555 |

**参数配置示例**:
```python
filament_params = {
    'PLA': {
        'retraction_length': 5.0,      # mm
        'retraction_speed': 40,         # mm/s
        'unretraction_extra': 0.0,
        'temperature': 210
    },
    'TPU': {
        'retraction_length': 8.0,      # 软性材料回抽量更大
        'retraction_speed': 20,         # 速度更慢
        'unretraction_extra': 0.5,     # 装填补偿
        'temperature': 220
    },
    'PETG': {
        'retraction_length': 6.0,
        'retraction_speed': 35,
        'unretraction_extra': 0.2,
        'temperature': 240
    }
}
```

**测试代码**:
```python
@pytest.mark.parametrize("bug_id,from_mat,to_mat,check_point,expected_param", [
    (11460, 'PLA', 'TPU', 'before_tool_change', 'retraction'),
    (11462, 'PLA', 'TPU', 'tower_infill', 'unretraction'),
    (11463, 'PLA', 'TPU', 'purge_line', 'unretraction'),
    (13555, 'PLA', 'TPU', 'before_tool_change_layer', 'retraction'),
])
def test_material_switch_params(gcode_file, filament_params,
                                bug_id, from_mat, to_mat, 
                                check_point, expected_param):
    parser = WipeTowerGCodeParser(gcode_file)
    parser.parse_all_moves()
    
    # 找到换料点
    tool_change_idx = find_tool_change_index(parser, from_mat, to_mat)
    
    if expected_param == 'retraction':
        # 检查换料前最后一次回抽
        for move in reversed(parser.moves[:tool_change_idx]):
            if move.move_type == GCodeMoveType.RETRACTION:
                actual = abs(move.e)
                # 应该使用from_mat的参数（当前工具）
                expected = filament_params[from_mat]['retraction_length']
                
                assert abs(actual - expected) < 0.1, \
                    f"Bug {bug_id}: 换料前回抽量{actual}mm，" \
                    f"期望{from_mat}参数{expected}mm"
                break
    
    elif expected_param == 'unretraction':
        # 检查换料后第一次装填
        for move in parser.moves[tool_change_idx:]:
            if move.move_type == GCodeMoveType.UNRETRACTION:
                actual = move.e
                # 应该使用to_mat的参数（新工具）
                expected_base = filament_params[to_mat]['retraction_length']
                expected_extra = filament_params[to_mat]['unretraction_extra']
                expected = expected_base + expected_extra
                
                assert abs(actual - expected) < 0.1, \
                    f"Bug {bug_id}: 换料后装填量{actual}mm，" \
                    f"期望{to_mat}参数{expected}mm"
                break

def find_tool_change_index(parser: WipeTowerGCodeParser,
                           from_mat: str, 
                           to_mat: str) -> int:
    """找到从from_mat到to_mat的换料指令索引"""
    # 简化逻辑：找到T指令
    for i, line in enumerate(parser.lines):
        stripped = line.strip()
        if stripped == 'T0' or stripped == 'T1':
            # 需要进一步判断是从哪个材料切换到哪个
            # 这里假设已知工具和材料的映射
            return i
    return -1

def test_retraction_amount_consistency():
    """TC-WT-007综合测试：验证整个打印过程中参数一致性"""
    parser = WipeTowerGCodeParser(gcode_file)
    parser.parse_all_moves()
    config = parser.parse_config_block()
    
    # 提取所有回抽动作
    retractions = [m for m in parser.moves 
                  if m.move_type == GCodeMoveType.RETRACTION]
    
    # 按工具分组验证
    current_tool = 0  # 初始工具
    tool_changes = find_all_tool_changes(parser)
    
    for retract in retractions:
        # 确定当前活动工具
        active_tool = get_active_tool_at_line(retract.line_num, tool_changes)
        
        # 获取期望参数
        expected = float(config[f'retraction_length[{active_tool}]'])
        actual = abs(retract.e)
        
        # 验证回抽量
        assert abs(actual - expected) < 0.1, \
            f"Line {retract.line_num}: 工具T{active_tool}回抽量{actual}，" \
            f"期望{expected}（参数retraction_length[{active_tool}]）"
```

**关键Bug根因分析**:

**Bug 11460** - 不同类型耗材层内换色，换料前回抽量错误
```
问题：PLA→TPU切换时，换料前应该用PLA参数回抽，但实际用了TPU参数
根因：m_current_tool在T指令前就被更新了
修复：应该在执行toolchange_Unload时仍使用old_tool参数
```

**Bug 13555** - 层间换色换料前回抽量错误（有4张截图）
```
验证点：
1. 找到"换料前"的注释标记
2. 找到前面的G1 E-X指令
3. 提取E值的绝对值
4. 对比当前工具（换料前）的retraction_length参数
```

**验证工具函数**:
```python
def extract_retraction_stats(parser: WipeTowerGCodeParser) -> Dict:
    """提取回抽统计信息用于调试
    
    返回格式:
    {
        'T0_retractions': [(line_num, e_value, location), ...],
        'T1_retractions': [...],
        'suspicious': [(line_num, reason), ...]  # 可疑的回抽
    }
    """
    stats = {
        'T0_retractions': [],
        'T1_retractions': [],
        'suspicious': []
    }
    
    config = parser.parse_config_block()
    t0_expected = float(config['retraction_length[0]'])
    t1_expected = float(config['retraction_length[1]'])
    
    current_tool = 0
    for i, move in enumerate(parser.moves):
        # 更新当前工具
        if i < len(parser.lines):
            line = parser.lines[i].strip()
            if line == 'T0':
                current_tool = 0
            elif line == 'T1':
                current_tool = 1
        
        # 检查回抽
        if move.move_type == GCodeMoveType.RETRACTION:
            e_val = abs(move.e)
            expected = t0_expected if current_tool == 0 else t1_expected
            
            location = "model" if not parser.tower_region.contains(move.x, move.y) else "tower"
            
            if current_tool == 0:
                stats['T0_retractions'].append((move.line_num, e_val, location))
            else:
                stats['T1_retractions'].append((move.line_num, e_val, location))
            
            # 检查是否可疑（偏差>10%）
            if abs(e_val - expected) / expected > 0.1:
                stats['suspicious'].append((
                    move.line_num,
                    f"T{current_tool}回抽{e_val}mm，期望{expected}mm"
                ))
    
    return stats
```


---

#### TC-WT-008: 回抽速度验证
**Bug ID**: 10738, 11185  
**校验级别**: L1/L2（配置对比 + 指令检查）  
**测试目的**: 验证回抽速度参数的正确应用

**源码依据**：
```cpp
// WipeTowerCreality.cpp
float retract_speed = m_filpar[m_current_tool].retract_speed * 60;
writer.retract(retract_length, retract_speed);

// Bug: 可能使用了错误的速度值（如打印速度）
// 期望：F值 = retraction_speed[tool] * 60 (转换为mm/min)
```

**测试步骤**:
```python
def test_retraction_speed():
    parser = WipeTowerGCodeParser(gcode_file)
    config = parser.parse_config_block()
    
    # L1: 从配置提取期望速度
    expected_speed_t0 = float(config['retraction_speed[0]']) * 60  # mm/s → mm/min
    
    # L2: 检查实际GCode中的F值
    retractions = [m for m in parser.moves 
                  if m.move_type == GCodeMoveType.RETRACTION]
    
    for retract in retractions:
        if retract.f:  # 有F值
            assert abs(retract.f - expected_speed_t0) < 60, \
                f"Line {retract.line_num}: 回抽速度F{retract.f}，" \
                f"期望{expected_speed_t0}"
```

**期望结果**:
```gcode
; 正确的回抽速度（假设参数为40mm/s）
G1 E-5.0 F2400  ; F = 40 * 60 = 2400 mm/min
```

**异常情况**:
| Bug表现 | 实际F值 | 原因 |
|---------|---------|------|
| 速度异常快 | F18000+ | 使用了打印速度 |
| 速度异常慢 | F300 | 使用了吐料速度 |
| 无F值 | 缺失 | 继承前一指令速度 |

---

#### TC-WT-009: 擦嘴线回抽装填
**Bug ID**: 13283  
**测试目的**: 验证擦嘴线区域的回抽和装填逻辑

**测试场景**:
- 打印擦嘴线前的装填
- 打印擦嘴线后的回抽
- 擦拭塔缺口处擦嘴线的特殊处理

**测试步骤**:
1. 启用擦拭塔缺口和擦嘴线
2. 观察缺口处擦嘴线打印前后的E轴动作
3. 对比缺口处和其他位置的差异

**期望结果**:
- 到达擦嘴线起点前应完成装填
- 打印完擦嘴线后应回抽
- 缺口处回抽装填量应与其他位置一致

---

### 2.3 路径规划测试（P1）

#### TC-WT-010: 多余路径检测
**Bug ID**: 11183, 11187, 11189, 11272, 11467, 13279, 13285, 13349  
**测试目的**: 验证擦拭塔相关路径中不存在冗余空走

**路径分类**:

| Bug ID | 路径描述 | 冗余表现 |
|--------|----------|----------|
| 11183 | 模型→擦拭塔外墙 | 空走路径多余 |
| 11187 | 擦拭塔外墙打印后 | 多余空走 |
| 11189 | 换料后→擦拭塔 | 空走路径逻辑错误 |
| 11272 | 换料后→擦拭塔 | 有多余路径 |
| 11467 | 层间换色换料后→擦拭塔 | 多余路径 |
| 13279 | 层内换色换料后 | 多余回抽和抬升 |
| 13285 | 层内换色第二层换料前 | 多余路径 |
| 13349 | 层间换色第二次换料前 | 多余路径 |

**测试方法**:
1. 可视化GCode路径（使用GCode查看器）
2. 测量路径长度
3. 识别往返运动或绕行
4. 计算最短路径并对比

**路径优化验证**:
```python
def analyze_path_redundancy(gcode, start_point, end_point):
    """分析路径冗余度"""
    actual_path = extract_xy_path(gcode)
    direct_distance = distance(start_point, end_point)
    actual_distance = calculate_path_length(actual_path)
    
    redundancy = (actual_distance - direct_distance) / direct_distance
    assert redundancy < 0.1, f"路径冗余度{redundancy*100:.1f}%，超过10%阈值"
```

---

#### TC-WT-011: 擦嘴动作和擦嘴线缺失
**Bug ID**: 11188, 11190, 13655  
**测试目的**: 验证擦嘴动作和擦嘴线的正确执行

**测试场景**:

**11188** - 打印完擦拭塔外墙后无擦拭
- 期望：打完外墙后应执行擦拭动作
- 验证：检查是否存在Y轴往复移动（擦拭动作）

**11190** - 完成换料后空走到擦拭塔缺口处没有擦嘴动作和擦嘴线
- 场景：层内换色场景
- 期望：换料后到缺口处应打印擦嘴线

**13655** - 打印擦嘴线前的路径问题
- 问题：先降Z再到擦嘴线起点
- 期望：先到擦嘴线起点再降Z

**测试步骤**:
1. 启用擦嘴功能和擦嘴线
2. 执行换料或打印完擦拭塔外墙
3. 检查是否存在擦拭动作（Y轴短距离往复）
4. 验证擦嘴线打印路径

**擦拭动作特征**:
```gcode
; 典型的擦拭动作
G1 Y{y+5} F3000   ; 快速移动5mm
G1 Y{y-5} F3000   ; 返回并继续往复
G1 Y{y+5} F3000
```

---

#### TC-WT-012: Z轴保护动作位置
**Bug ID**: 11339  
**测试目的**: 验证Z轴保护动作在正确的位置触发

**问题描述**:
- Z轴保护动作应在到达擦拭塔缺口前触发
- 实际表现：保护动作在缺口绕行路径之后

**测试步骤**:
1. 启用擦拭塔缺口
2. 打印需要换料的场景
3. 记录Z轴抬升指令的位置
4. 验证抬升位置在XY平面上的坐标

**期望结果**:
```gcode
; 正确的顺序
G0 Z{z + safe_height}  ; 先抬升保护
G0 X{gap_x} Y{gap_y}   ; 再移动到缺口
; 而非
G0 X{gap_x} Y{gap_y}   ; 先移动（错误）
G0 Z{z + safe_height}  ; 后抬升
```

---

#### TC-WT-013: 擦拭塔内部空走速度
**Bug ID**: 13653  
**测试目的**: 验证擦拭塔内部空走速度设置

**问题描述**:
- 擦拭塔内部空走速度未设置
- 建议：设置为前面打印路径的速度
- 注意：空走后的装填速度要恢复

**测试步骤**:
1. 打印包含擦拭塔填充的场景
2. 提取擦拭塔内部的空走指令（G0）
3. 检查F值是否已设置
4. 验证空走后装填速度是否恢复

**验证逻辑**:
```python
def verify_travel_speed_in_tower(gcode):
    in_tower = False
    last_print_speed = None
    
    for line in gcode:
        if is_in_wipe_tower(line):
            in_tower = True
        if in_tower and is_print_move(line):
            last_print_speed = extract_speed(line)
        if in_tower and is_travel_move(line):
            travel_speed = extract_speed(line)
            assert travel_speed is not None, "空走速度未设置"
            assert travel_speed <= last_print_speed * 1.5, "空走速度过快"
```

---

### 2.4 换色场景测试（P0）

#### TC-WT-014: 层内换色场景综合测试
**Bug涉及**: 11182-11194, 13277-13285  
**测试目的**: 验证层内换色场景下擦拭塔的完整工作流程

**测试配置**:
- 场景：单层内多次换色（如同一层T0→T1→T0）
- 模型：包含多色区域的简单几何体
- 擦拭塔：启用填充+外墙+缺口

**完整工作流程验证**:

```
阶段1：打印模型区域1（T0）
  ↓ [回抽]
  ↓ [抬升]
  ↓ [空走到换料点]
阶段2：执行换料（T0→T1）
  ↓ [抬升保护]
  ↓ [移动到擦拭塔缺口]
  ↓ [降Z]
阶段3：打印擦嘴线
  ↓ [装填]
  ↓ [打印擦嘴线]
  ↓ [回抽]
阶段4：打印擦拭塔外墙
  ↓ [抬升（如需要）]
  ↓ [移动到外墙起点]
  ↓ [装填]
  ↓ [打印外墙]
  ↓ [回抽]
阶段5：打印擦拭塔填充
  ↓ [移动到填充起点]
  ↓ [装填]
  ↓ [打印填充]
  ↓ [回抽]
阶段6：返回模型区域2（T1）
  ↓ [抬升]
  ↓ [空走到模型]
  ↓ [装填]
  ↓ [打印模型区域2]
```

**每个阶段的验证点**:

| 阶段 | 验证项 | 相关Bug |
|------|--------|---------|
| 模型→换料 | 回抽→抬升→空走 | 11182 |
| 换料→擦拭塔 | 保护抬升→缺口路径 | 11189, 11272 |
| 擦嘴线 | 装填→打印→回抽 | 11190, 13283 |
| 擦拭塔外墙 | 抬升→装填→打印→回抽 | 11184, 13277 |
| 擦拭塔填充 | 装填正确，无多余回抽 | 11462 |
| 返回模型 | 回抽→抬升→空走→装填 | 11279, 11320 |

---

#### TC-WT-015: 层间换色场景综合测试
**Bug涉及**: 10753-10755, 11193, 11471, 13334-13851  
**测试目的**: 验证层间换色场景下不同层之间的换色行为

**测试配置**:
- 场景：不同层使用不同颜色（如第1层T0，第2层T1，第3层T0）
- 模型：多层结构，每层包含实体部分
- 擦拭塔：启用填充+外墙

**关键测试点**:

**A. 换色层与非换色层的差异**
- 换色层：需要执行完整的换料流程
- 非换色层：继续使用当前喷头
- Bug 11471：换色层擦拭塔打印顺序错误

**B. 第一层特殊处理**
- Bug 10753：首层擦嘴线到擦拭塔重复装填
- Bug 13334：第一层打完擦嘴线缺装填

**C. 擦拭塔缺口处理**
- Bug 10755：缺口处擦嘴线路径悬空
- 原因：非换色层擦拭塔路径有较大间隙

**D. 换料前后的路径**
- Bug 13349：第二次换料前有多余路径
- Bug 13352：第二次换料前应先打印擦拭塔外墙

**测试步骤**:
1. 设计3层模型，配置层间换色（第1层T0，第2层T1，第3层T0）
2. 生成GCode并逐层分析
3. 验证每个换色层的完整流程
4. 对比换色层和非换色层的擦拭塔处理

**测试矩阵**:

| 层 | 喷头 | 是否换色 | 验证点 |
|----|------|----------|--------|
| 1 | T0 | - | 首层擦嘴线装填 |
| 2 | T1 | 是 | 完整换料流程 |
| 3 | T0 | 是 | 换料前打印外墙 |
| 4 | T0 | 否 | 无换料动作 |

---

#### TC-WT-016: 不同耗材类型换色测试
**Bug涉及**: 11460-11464, 13303-13384  
**测试目的**: 验证不同类型耗材组合下的换色行为

**耗材组合矩阵**:

| 组合 | T0 | T1 | 关键差异 | 相关Bug |
|------|----|----|----------|---------|
| 组合1 | PLA | PLA | 参数相同 | - |
| 组合2 | PLA | TPU | 回抽量差异大 | 11460, 11462, 11463, 11464 |
| 组合3 | PLA | PETG | 温度差异 | 13303, 13309 |
| 组合4 | PETG | TPU | 多项差异 | 13379, 13534, 13537 |

**参数差异对比**:

```python
# 典型参数设置
filament_params = {
    'PLA': {
        'retraction': 5.0,      # mm
        'retraction_speed': 40,  # mm/s
        'unretraction': 5.0,
        'unretraction_speed': 40,
        'temperature': 210
    },
    'TPU': {
        'retraction': 8.0,      # 回抽量更大
        'retraction_speed': 20, # 速度更慢
        'unretraction': 8.5,    # 装填补偿
        'unretraction_speed': 20,
        'temperature': 220
    }
}
```

**测试场景**:

**场景A：层内换色PLA→TPU**
- Bug 11460：换料前回抽量错误（应用TPU参数）
- Bug 11462：擦拭塔填充装填量错误
- Bug 11463：擦嘴线处装填量错误
- Bug 11464：换料前重复回抽

**场景B：层间换色PLA→PETG**
- Bug 13303：换料后打完擦拭塔填充回抽量错误
- Bug 13309：填充和外墙回抽量错误

**场景C：换色前后的擦拭塔**
- Bug 13534：换色前擦拭塔上回抽量错误
- Bug 13537：换色层换色前擦拭塔回抽量错误

**验证方法**:
```python
def verify_material_switch(gcode, from_material, to_material):
    """验证耗材切换时的参数应用"""
    switch_point = find_tool_change(gcode, from_material, to_material)
    
    # 验证切换前最后一次回抽
    last_retract_before = find_last_retraction(gcode, switch_point)
    assert_retraction_amount(last_retract_before, from_material)
    
    # 验证切换后第一次装填
    first_unretract_after = find_first_unretraction(gcode, switch_point)
    assert_unretraction_amount(first_unretract_after, to_material)
```

---

### 2.5 特殊配置测试（P1）

#### TC-WT-017: 无稀疏层配置测试
**Bug涉及**: 11329, 13364, 13366, 13533, 13826  
**测试目的**: 验证开启"无稀疏层"选项后的行为

**配置说明**:
- 无稀疏层：擦拭塔不打印填充部分，只打印外墙
- 目的：节省打印时间和材料

**测试场景**:

| Bug ID | 问题描述 | 场景 |
|--------|----------|------|
| 11329 | 装填错误 | 开启无稀疏层打印擦拭塔 |
| 13364 | 多余抬升 | 层间换色，换料后到擦拭塔 |
| 13366 | 多余抬升 | 层间换色，打完塔到模型 |
| 13533 | 重复装填 | 层间换色，换料前模型到塔 |
| 13826 | 无抬升 | 层间换色，擦拭塔到模型 |

**测试步骤**:
1. 启用"无稀疏层"选项
2. 配置层间换色场景
3. 验证擦拭塔只包含外墙打印
4. 检查各个路径切换点的动作

**期望行为**:
- 擦拭塔跳过填充部分直接打印外墙
- 路径切换逻辑与标准配置一致
- 不应因为缺少填充而引入额外问题

---

#### TC-WT-018: 关闭擦拭塔缺口测试
**Bug涉及**: 13570, 13607, 13851  
**测试目的**: 验证关闭擦拭塔缺口后的行为

**配置组合**:

| 配置 | 方形塔 | 缺口 | Bug表现 |
|------|--------|------|---------|
| 配置1 | 关闭 | 关闭 | 层内换色到模型无抬升 (13570) |
| 配置2 | 关闭 | 关闭 | 层内换色回抽量错误 (13607) |
| 配置3 | 开启 | 关闭 | 换料后打印塔前多余抬升 (13851) |

**测试重点**:
- 关闭缺口后不需要打印擦嘴线
- 换料后直接进入擦拭塔打印
- 路径规划应该更加直接

**测试步骤**:
1. 关闭擦拭塔缺口选项
2. 测试不同的方形塔配置
3. 验证换料后的路径
4. 检查是否仍然尝试访问不存在的缺口

---

#### TC-WT-019: CFS-C机型特殊测试
**Bug涉及**: 13275, 13276  
**测试目的**: 验证CFS-C机型的擦拭塔功能

**测试场景**:

**13275** - CFS-C机型输出gcode异常
- 验证：GCode文件完整性
- 验证：特殊指令的正确性

**13276** - CFS-C机型擦拭塔首层面积异常
- 验证：首层擦拭塔面积计算
- 对比：标准机型的首层面积
- 检查：是否考虑了机型特定的底板尺寸

**测试步骤**:
1. 选择CFS-C机型配置
2. 生成包含擦拭塔的GCode
3. 分析首层擦拭塔的XY坐标范围
4. 计算实际面积并与期望对比

---

### 2.6 回抽擦拭动作测试（P1）

#### TC-WT-020: 回抽擦拭位置和时机
**Bug涉及**: 11280, 11459, 13344, 13377, 13381  
**测试目的**: 验证回抽后擦拭动作的正确性

**测试场景**:

| Bug ID | 问题描述 | 关键点 |
|--------|----------|--------|
| 11280 | 打完外墙去打模型前擦拭路径偏移 | 擦拭位置错误 |
| 11459 | 打完擦拭塔到模型前的回抽擦拭悬空 | 擦拭在空中 |
| 13344 | 非换色层擦拭塔内远距离空走前无回抽擦拭 | 缺少擦拭 |
| 13377 | 非换色层打擦拭塔填充时缺回抽擦拭 | 填充内缺擦拭 |
| 13381 | 非换色层打完填充去打模型时缺回抽擦拭 | 缺擦拭 |

**擦拭动作的正确流程**:
```gcode
; 正确的回抽擦拭序列
G1 E-5.0 F2400           ; 1. 回抽
G1 X{x} Y{y+擦拭距离}    ; 2. 擦拭移动（XY平面，Z不变）
G0 Z{z+抬升高度}         ; 3. 抬升
G0 X{目标x} Y{目标y}     ; 4. 空走到目标
```

**常见错误**:
- 擦拭在抬升之后（导致悬空）
- 擦拭距离为0（未执行）
- 擦拭位置超出打印区域

**测试方法**:
```python
def verify_wipe_sequence(gcode, retract_pos):
    """验证回抽擦拭序列"""
    idx = find_retraction_index(gcode, retract_pos)
    
    # 检查回抽后的动作序列
    next_moves = gcode[idx+1:idx+5]
    
    # 应该是：回抽 → XY移动(擦拭) → Z抬升 → XY空走
    assert is_xy_move(next_moves[0]), "回抽后应先XY擦拭"
    assert is_z_lift(next_moves[1]), "擦拭后应Z抬升"
    assert is_xy_travel(next_moves[2]), "抬升后XY空走"
```

---

### 2.7 打印顺序测试（P1）

#### TC-WT-021: 擦拭塔打印顺序验证
**Bug涉及**: 11471, 13352, 13282  
**测试目的**: 验证擦拭塔各部分的打印顺序正确性

**标准打印顺序**:

```
方案A（先外墙后填充）:
1. 擦嘴线（缺口处）
2. 擦拭塔外墙
3. 擦拭塔填充

方案B（先填充后外墙）:
1. 擦嘴线（缺口处）
2. 擦拭塔填充
3. 擦拭塔外墙
```

**Bug场景分析**:

**11471** - 层间换色场景换色层擦拭塔打印顺序错误
- 3张截图说明
- 可能的错误：填充和外墙顺序颠倒

**13352** - 第二次换料前应先去打印擦拭塔外墙
- 2张截图说明
- 场景：多次换色
- 问题：换料前后的擦拭塔打印顺序不一致

**13282** - 擦拭塔外墙缺口处回抽装填量错误
- 涉及缺口位置的特殊处理

**测试步骤**:
1. 配置打印顺序参数（如果有）
2. 生成GCode并可视化
3. 标记擦拭塔各部分的打印起始位置
4. 验证打印顺序符合设置

**验证代码**:
```python
def verify_tower_print_order(gcode):
    """验证擦拭塔打印顺序"""
    tower_sections = extract_tower_sections(gcode)
    
    for layer in tower_sections:
        assert layer['order'] in [
            ['purge_line', 'wall', 'infill'],
            ['purge_line', 'infill', 'wall']
        ], f"第{layer['num']}层打印顺序错误"
```

---

#### TC-WT-022: 擦拭塔分区打印
**Bug涉及**: 11192, 11194  
**测试目的**: 验证擦拭塔的分区打印功能

**测试场景**:

**11192** - 擦拭塔中粘接性较差的耗材没有分区打印
- 2张截图说明
- 背景：TPU等软性材料需要分区打印增强稳定性

**11194** - 层间换色时层擦拭塔顶部未分区打印
- 场景：换色层的擦拭塔顶部

**分区打印逻辑**:
- 检测耗材类型（如TPU）
- 将填充区域分成多个小区域
- 逐个区域打印，增加层间结合

**测试步骤**:
1. 配置包含TPU的换色场景
2. 检查擦拭塔填充是否分区
3. 验证分区数量和大小合理
4. 测试顶部几层是否也分区

**验证点**:
- TPU填充应分成4-9个小区域
- 每个区域独立打印完成后再打印下一个
- 顶部3-5层也应分区

---

### 2.8 参数控制测试（P2）

#### TC-WT-023: 抬升方式参数控制
**Bug涉及**: 10735, 11456, 11461  
**测试目的**: 验证抬升方式参数的有效性

**参数选项**:
- 垂直抬升：先Z轴抬升到目标高度，再XY移动
- 梯形抬升：Z轴和XY轴同时移动，形成斜线路径

**测试场景**:

**10735** - 模型到擦拭塔外墙时抬升方式不受参数控制
**11456** - 模型到擦拭塔的抬升方式不受参数控制
**11461** - 擦拭塔抬升方式错误

**测试步骤**:
1. 设置抬升方式为"垂直抬升"
2. 生成GCode并分析路径
3. 验证Z轴先到达目标高度再进行XY移动
4. 重复测试"梯形抬升"

**验证逻辑**:
```python
def verify_lift_type(gcode, lift_type):
    """验证抬升方式"""
    lift_moves = extract_lift_sequences(gcode)
    
    for lift in lift_moves:
        if lift_type == 'vertical':
            # 垂直抬升：Z变化，XY不变
            assert lift[0].z != lift[-1].z
            assert lift[0].x == lift[-1].x and lift[0].y == lift[-1].y
        elif lift_type == 'contour':
            # 梯形抬升：Z和XY同时变化
            assert lift[0].z != lift[-1].z
            assert lift[0].x != lift[-1].x or lift[0].y != lift[-1].y
```

---

#### TC-WT-024: T指令拆解和自定义GCode
**Bug涉及**: 13395  
**测试目的**: 验证T指令拆解自定义gcode的功能

**问题描述**:
- T指令拆解自定义gcode失效
- 导致无法正常吐料

**测试步骤**:
1. 配置自定义换料GCode（如T0→T1时的吐料指令）
2. 生成包含换料的GCode
3. 检查T指令是否被正确拆解为自定义GCode
4. 验证吐料动作是否执行

**期望结果**:
```gcode
; 配置的自定义换料GCode
; T0_to_T1_start:
G1 E50 F300  ; 吐料50mm

; 实际GCode中T1指令应被替换为：
; T1
G1 E50 F300  ; 吐料指令应出现
```

---

#### TC-WT-025: 回抽量参数修改验证
**Bug涉及**: 13511  
**测试目的**: 验证修改回抽量参数后立即生效

**问题描述**:
- 修改回抽量不生效
- 2张截图说明

**测试步骤**:
1. 设置初始回抽量（如5mm）
2. 生成GCode并记录回抽值
3. 修改回抽量为新值（如6mm）
4. 立即重新生成GCode
5. 验证新GCode中的回抽值已更新

**验证点**:
- 参数修改应立即反映在新生成的GCode中
- 无需重启软件
- 所有回抽位置都应用新参数

---

### 2.9 边界和异常测试（P2）

#### TC-WT-026: 换料前回抽异常
**Bug涉及**: 13278, 13496, 13624  
**测试目的**: 验证换料前回抽动作的异常情况

**测试场景**:

**13278** - 换料前的回抽动作异常（层内换色）
- 2张截图说明

**13496** - 层间换色场景，换料前回抽动作异常

**13624** - 层间换色，换色层，打印完模型去换料前回抽动作异常

**异常类型**:
- 回抽量为0
- 回抽方向错误（正向变负向）
- 回抽速度异常
- 重复回抽

**测试步骤**:
1. 配置各种换色场景
2. 在换料指令(T0/T1)前定位
3. 检查前面的E轴动作
4. 验证回抽量和速度

---

#### TC-WT-027: 装填逻辑错误
**Bug涉及**: 13608, 13621, 13704  
**测试目的**: 验证特殊情况下的装填逻辑

**测试场景**:

**13608** - 层内换色，打完擦拭塔填充去打擦拭塔外墙时回抽量错误

**13621** - 层内换色，打完模型去打擦拭塔前回抽量错误

**13704** - 打完擦拭塔填充，打外墙前装填逻辑错误
- 问题：先装填再空走（应该先空走再装填）
- 根因：回抽结束后的空走位置丢失

**验证重点**:
- 填充→外墙：应先空走再装填
- 模型→擦拭塔：回抽量应匹配当前材料
- 擦拭塔内部移动：短距离不需要回抽装填

---

## 3. 测试数据准备

### 3.1 标准测试模型

| 模型名称 | 尺寸(mm) | 用途 | 层数 |
|----------|----------|------|------|
| 简单立方体 | 20×20×20 | 基础功能测试 | 20-50 |
| 多色塔 | 30×30×50 | 换色测试 | 50-100 |
| 薄壁模型 | 50×50×10 | 路径验证 | 10-20 |
| 复杂几何 | 40×40×30 | 综合测试 | 30-60 |

### 3.2 耗材参数配置

```json
{
  "PLA": {
    "retraction_length": 5.0,
    "retraction_speed": 40,
    "unretraction_extra": 0,
    "temperature": 210,
    "flow_rate": 100
  },
  "TPU": {
    "retraction_length": 8.0,
    "retraction_speed": 20,
    "unretraction_extra": 0.5,
    "temperature": 220,
    "flow_rate": 95
  },
  "PETG": {
    "retraction_length": 6.0,
    "retraction_speed": 35,
    "unretraction_extra": 0.2,
    "temperature": 240,
    "flow_rate": 100
  }
}
```

### 3.3 擦拭塔配置

```json
{
  "wipe_tower": {
    "enable": true,
    "position": [180, 180],
    "size": 30,
    "enable_wall": true,
    "enable_infill": true,
    "enable_gap": true,
    "gap_position": "front",
    "sparse_layer": false,
    "purge_line": true,
    "wipe_after_retract": true,
    "wipe_distance": 2.0
  }
}
```

---

## 4. 测试执行策略

### 4.1 自动化测试脚本

```python
"""
擦拭塔功能自动化测试框架
"""
import re
from pathlib import Path

class WipeTowerTestFramework:
    def __init__(self, gcode_file):
        self.gcode = self.load_gcode(gcode_file)
        self.layers = self.parse_layers()
        self.tower_regions = self.identify_tower_regions()
    
    def test_retraction_count(self, expected_positions):
        """TC-WT-005: 验证回抽次数"""
        retractions = self.find_retractions()
        for pos in expected_positions:
            count = self.count_retractions_at(pos, retractions)
            assert count == 1, f"位置{pos}回抽{count}次，期望1次"
    
    def test_lift_before_travel(self, travel_moves):
        """TC-WT-001: 验证抬升时机"""
        for travel in travel_moves:
            prev_move = self.get_previous_move(travel)
            assert prev_move['z'] > travel['start_z'], \
                f"空走前应先抬升Z"
    
    def test_material_switch_params(self, from_mat, to_mat):
        """TC-WT-007: 验证耗材切换参数"""
        switch_point = self.find_tool_change(from_mat, to_mat)
        
        # 检查切换前回抽量
        last_retract = self.find_last_retraction_before(switch_point)
        expected_retract = self.get_retraction_length(from_mat)
        assert abs(last_retract - expected_retract) < 0.1
        
        # 检查切换后装填量
        first_unretract = self.find_first_unretraction_after(switch_point)
        expected_unretract = self.get_unretraction_length(to_mat)
        assert abs(first_unretract - expected_unretract) < 0.1
    
    def test_path_redundancy(self, start, end, max_redundancy=0.1):
        """TC-WT-010: 验证路径冗余度"""
        actual_path = self.extract_path(start, end)
        direct_dist = self.euclidean_distance(start, end)
        actual_dist = self.path_length(actual_path)
        redundancy = (actual_dist - direct_dist) / direct_dist
        
        assert redundancy <= max_redundancy, \
            f"路径冗余度{redundancy:.1%}超过阈值{max_redundancy:.1%}"
    
    def test_print_order(self, layer_num, expected_order):
        """TC-WT-021: 验证打印顺序"""
        layer = self.layers[layer_num]
        tower_parts = self.identify_tower_parts(layer)
        actual_order = [p['type'] for p in tower_parts]
        
        assert actual_order == expected_order, \
            f"第{layer_num}层打印顺序: {actual_order}, 期望: {expected_order}"
    
    def generate_report(self):
        """生成测试报告"""
        return {
            'total_tests': len(self.test_results),
            'passed': sum(1 for r in self.test_results if r['passed']),
            'failed': sum(1 for r in self.test_results if not r['passed']),
            'details': self.test_results
        }
```

### 4.2 测试执行流程

```
1. 准备阶段
   ├─ 配置测试环境
   ├─ 准备测试模型
   └─ 设置耗材参数

2. 生成阶段
   ├─ 生成GCode文件
   ├─ 保存原始配置
   └─ 创建测试记录

3. 分析阶段
   ├─ 解析GCode结构
   ├─ 提取关键指令
   └─ 建立坐标映射

4. 验证阶段
   ├─ 执行测试用例
   ├─ 记录测试结果
   └─ 生成截图证据

5. 报告阶段
   ├─ 汇总测试结果
   ├─ 标记失败用例
   └─ 生成测试报告
```

---

## 5. Bug分类统计

### 5.1 按问题类型分类

| 问题类型 | Bug数量 | 占比 | 典型Bug ID |
|----------|---------|------|------------|
| 抬升/降Z异常 | 18 | 23% | 10735, 11320, 13826 |
| 回抽/装填错误 | 25 | 32% | 10737, 10754, 11460 |
| 路径冗余 | 12 | 15% | 11183, 11189, 13279 |
| 参数不生效 | 5 | 6% | 10735, 11456, 13511 |
| 换色逻辑 | 15 | 19% | 11471, 13352, 13555 |
| 其他 | 3 | 4% | 13275, 13276, 13395 |

### 5.2 按场景分类

| 场景 | Bug数量 | 典型问题 |
|------|---------|----------|
| 层内换色 | 28 | 回抽装填量错误、路径冗余 |
| 层间换色 | 32 | 换色层打印顺序、抬升缺失 |
| 不同耗材 | 12 | 参数未切换、回抽量错误 |
| 特殊配置 | 6 | 无稀疏层、关闭缺口 |

### 5.3 按严重程度分类（推断）

| 严重程度 | 数量 | 影响 | 优先级 |
|----------|------|------|--------|
| 致命 | 8 | 打印失败/碰撞 | P0 |
| 严重 | 35 | 打印质量严重下降 | P0 |
| 一般 | 25 | 打印质量轻微影响 | P1 |
| 轻微 | 10 | 效率影响、美观问题 | P2 |

---

## 6. 测试覆盖率矩阵

### 6.1 功能覆盖率

| 功能模块 | 测试用例 | Bug覆盖 | 覆盖率 |
|----------|----------|---------|--------|
| 抬升逻辑 | TC-WT-001~004 | 18/18 | 100% |
| 回抽装填 | TC-WT-005~009 | 25/25 | 100% |
| 路径规划 | TC-WT-010~013 | 12/12 | 100% |
| 换色场景 | TC-WT-014~016 | 15/15 | 100% |
| 特殊配置 | TC-WT-017~019 | 6/6 | 100% |
| 回抽擦拭 | TC-WT-020 | 5/5 | 100% |
| 打印顺序 | TC-WT-021~022 | 5/5 | 100% |
| 参数控制 | TC-WT-023~025 | 5/5 | 100% |
| 边界测试 | TC-WT-026~027 | 6/6 | 100% |

### 6.2 场景覆盖率

| 场景维度 | 覆盖情况 |
|----------|----------|
| 换色类型 | 层内换色 ✓、层间换色 ✓ |
| 耗材组合 | PLA+PLA ✓、PLA+TPU ✓、PLA+PETG ✓、PETG+TPU ✓ |
| 擦拭塔配置 | 填充+外墙 ✓、仅外墙 ✓、仅填充 ✓ |
| 缺口配置 | 开启 ✓、关闭 ✓ |
| 特殊选项 | 无稀疏层 ✓、分区打印 ✓ |
| 抬升方式 | 垂直 ✓、梯形 ✓ |
| 机型 | 标准 ✓、CFS-C ✓ |

---

## 7. 回归测试清单

### 7.1 核心功能回归（每次修改必测）

- [ ] TC-WT-001: 模型到擦拭塔外墙的抬升
- [ ] TC-WT-005: 重复回抽问题验证
- [ ] TC-WT-006: 重复装填问题验证
- [ ] TC-WT-007: 回抽量和装填量计算
- [ ] TC-WT-014: 层内换色场景综合测试
- [ ] TC-WT-015: 层间换色场景综合测试

### 7.2 扩展功能回归（重大修改必测）

- [ ] TC-WT-016: 不同耗材类型换色测试
- [ ] TC-WT-021: 擦拭塔打印顺序验证
- [ ] TC-WT-023: 抬升方式参数控制

### 7.3 边界情况回归（版本发布前必测）

- [ ] TC-WT-017: 无稀疏层配置测试
- [ ] TC-WT-018: 关闭擦拭塔缺口测试
- [ ] TC-WT-027: 装填逻辑错误边界测试

---

## 8. 测试报告模板

```markdown
# 擦拭塔功能测试报告

**测试版本**: Creality Print 6.x
**测试日期**: YYYY-MM-DD
**测试人员**: XXX

## 测试概要

| 项目 | 数量 |
|------|------|
| 总测试用例数 | 27 |
| 执行用例数 | XX |
| 通过用例数 | XX |
| 失败用例数 | XX |
| 跳过用例数 | XX |
| 通过率 | XX% |

## 失败用例详情

### TC-WT-XXX: 用例名称

**Bug ID**: XXXXX  
**失败原因**: XXX  
**重现步骤**: 
1. XXX
2. XXX

**期望结果**: XXX  
**实际结果**: XXX  
**截图/GCode**: [附件链接]

## 回归测试结果

| Bug ID | 状态 | 验证说明 |
|--------|------|----------|
| 10735 | ✓ 已修复 | 抬升方式受参数控制 |
| 10754 | ✗ 未修复 | 仍存在重复回抽 |
| ... | | |

## 风险评估

**高风险问题**: 
- XXX

**遗留问题**:
- XXX

**建议**:
- XXX
```

---

## 9. 附录

### 9.1 GCode指令参考

| 指令 | 说明 | 示例 |
|------|------|------|
| G1 | 线性移动（打印/回抽/装填） | G1 X10 Y10 E1.5 F3000 |
| G0 | 快速移动（空走） | G0 X100 Y100 Z1 |
| T0/T1 | 换工具头 | T1 |
| M104 | 设置挤出头温度 | M104 S210 T0 |
| M109 | 等待温度 | M109 S210 T0 |

### 9.2 关键坐标定义

```python
# 擦拭塔区域
TOWER_REGION = {
    'x_min': 170,
    'x_max': 200,
    'y_min': 170,
    'y_max': 200
}

# 擦拭塔缺口位置（前方）
TOWER_GAP = {
    'x': 185,
    'y': 170,
    'width': 10
}

# 模型区域（示例）
MODEL_REGION = {
    'x_min': 50,
    'x_max': 150,
    'y_min': 50,
    'y_max': 150
}
```

### 9.3 常用验证正则表达式

```python
# 回抽指令：G1 E-X.X
RETRACT_PATTERN = r'G1\s+E-(\d+\.?\d*)\s+F(\d+)'

# 装填指令：G1 EX.X（正值）
UNRETRACT_PATTERN = r'G1\s+E(\d+\.?\d*)\s+F(\d+)'

# Z轴抬升：G0/G1 Z提升
Z_LIFT_PATTERN = r'G[01]\s+Z(\d+\.?\d*)'

# 换工具头
TOOL_CHANGE_PATTERN = r'^T([01])$'
```

---

## 10. 测试用例优先级执行建议

### Sprint 1（P0 - 关键路径）
- Week 1: TC-WT-001, TC-WT-002, TC-WT-005
- Week 2: TC-WT-006, TC-WT-007, TC-WT-014
- Week 3: TC-WT-015, TC-WT-016
- Week 4: 回归测试 + Bug修复验证

### Sprint 2（P1 - 重要功能）
- Week 1: TC-WT-010, TC-WT-011, TC-WT-020
- Week 2: TC-WT-021, TC-WT-022, TC-WT-017
- Week 3: TC-WT-018, 回归测试
- Week 4: Bug修复验证 + 文档完善

### Sprint 3（P2 - 优化项）
- Week 1: TC-WT-023, TC-WT-024, TC-WT-025
- Week 2: TC-WT-026, TC-WT-027
- Week 3: 全面回归测试
- Week 4: 性能测试 + 发布准备

---

**文档结束**

*本文档基于78个真实Bug记录生成，涵盖擦拭塔功能的全面测试场景。建议在每次代码修改后执行对应的测试用例，确保功能稳定性。*
