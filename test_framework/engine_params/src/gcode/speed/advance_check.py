# engine_params/src/gcode/speed/advance_check.py
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Dict, Tuple, Any

from engine_params.src.gcode.GCodeParserEx import GCodeParserEx, ConfigValue
from engine_params.src.gcode.constants import ExtrusionType, ACCEL_KEY
from engine_params.src.gcode.GCode import _VEL_KEYS_CANON

from dataclasses import dataclass, field
from enum import Enum
import ast
import math


# ---- 等价于 C++ 中的 _MM2INT 宏 ----
def _mm2int(n: float) -> int:
    # int(n * 1000 + 0.5 * sign(n))
    return int(n * 1000.0 + 0.5 * ((n > 0) - (n < 0)))


# ===== Limit 相关结构 =====
class LimitType(Enum):
    LIMIT_MESS = 0  # 这里沿用原拼写（mass/mess），逻辑不变
    LIMIT_HEIGHT = 1


@dataclass
class LimitData:
    # 区间端点（以“毫米*1000”整型存储，保持与原实现一致）
    value1: float = 0.0
    value2: float = 0.0
    # 两端的限制（线性插值使用）
    speed1: float = 0.0
    speed2: float = 0.0
    Acc1: float = 0.0
    Acc2: float = 0.0
    Temp1: float = 0.0
    Temp2: float = 0.0


# ====== FlowTempGraph 等价实现 ======
@dataclass
class FlowTempGraph:
    @dataclass
    class Datum:
        flow: float
        temp: float

    data: List['FlowTempGraph.Datum'] = field(default_factory=list)

    def init_limit(self, limit: str) -> None:
        """
        解析形如 [[3.5,200],[7.0,240]]
        """
        if not limit:
            return
        try:
            arr = ast.literal_eval(limit)
        except Exception:
            return
        if not isinstance(arr, list):
            return
        for item in arr:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                try:
                    f, t = float(item[0]), float(item[1])
                except Exception:
                    continue
                self.data.append(FlowTempGraph.Datum(f, t))

    def getTemp(self, flow: float,
                material_print_temperature: float,
                flow_dependent_temperature: bool) -> float:
        if (not flow_dependent_temperature) or (not self.data):
            return material_print_temperature
        if len(self.data) == 1:
            return self.data[0].temp
        if flow < self.data[0].flow:
            return self.data[0].temp
        last = self.data[0]
        for d in self.data[1:]:
            if d.flow >= flow:
                # 线性插值
                return last.temp + (d.temp - last.temp) * (flow - last.flow) / (d.flow - last.flow)
            last = d
        return self.data[-1].temp


# ====== 计算模型的重量 ======
def weight_from_gcode(
        total_extruded_len: float,
        filament_diameter_mm: float,
        filament_density_g_cm3: float,
) -> float:
    """
    计算 G-code 中正向挤出的重量（克），假设使用相对挤出模式 (M83)。
    - filament_diameter_mm: 耗材直径，默认 1.75 mm
    - filament_density_g_cm3: 耗材密度，默认 PLA 约 1.24 g/cm³
    """
    # 每毫米耗材的横截面积（mm²）与体积（mm³/mm）
    cross_section_mm2 = math.pi * (filament_diameter_mm ** 2) / 4.0

    # 体积 mm³ = 挤出总长度 mm × 横截面积 mm²
    volume_mm3 = total_extruded_len * cross_section_mm2
    # 重量 g = 体积 (mm³) × 密度 (g/cm³) / 1000
    weight_g = volume_mm3 * filament_density_g_cm3 / 1000.0
    return weight_g


# ====== SmoothSpeedAcc 等价实现 ======
class SmoothSpeedAcc:
    def __init__(self, parser,
                 acceleration_limit_mess_enable=None,
                 speed_limit_to_height_enable=None,
                 material_diameter: float | None = None,
                 material_density: float | None = None) -> None:
        """
        参数:
            parser: GCodeParserEx 实例（将用于 load_config()）
        """
        self.parser: GCodeParserEx = parser

        self.max_speed_limit_to_height: float = -1.0
        self.acceleration_limit_mess_enable: bool = acceleration_limit_mess_enable if acceleration_limit_mess_enable else False
        self.acceleration_limit_height_enable: bool = speed_limit_to_height_enable if speed_limit_to_height_enable else False
        # 耗材参数允许调用方直接传入；未提供时在 init_limit 中从配置读取
        self.material_diameter: float | None = material_diameter
        self.material_density: float | None = material_density

        self.vctacceleration_limit_mass: List[LimitData] = []
        self.vctacceleration_limit_height: List[LimitData] = []

        self.current_limit_speed: float = -1.0
        self.current_limit_Acc: float = -1.0
        self.current_limit_Temp: float = -1.0

    # ---- 配置读取辅助（兼容 ParsedConfig） ----
    def _load_cfg(self) -> Dict[str, Any]:
        try:
            return self.parser.load_config() or {}
        except Exception:
            return {}

    @staticmethod
    def _get_cfg_float(cfg: Dict[str, Any], key: str, default: float = 0.0) -> float:
        pc = cfg.get(key) or cfg.get(key.strip().lower())
        if pc is None:
            return default
        try:
            # ParsedConfig: .value 可能为 int/float/str
            v = getattr(pc, "value", pc)
            return float(v)
        except Exception:
            return default

    @staticmethod
    def _get_cfg_bool(cfg: Dict[str, Any], key: str, default: bool = False) -> bool:
        pc = cfg.get(key) or cfg.get(key.strip().lower())
        if pc is None:
            return default
        v = getattr(pc, "value", pc)
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return v != 0
        if isinstance(v, str):
            return v.strip().lower() in ("1", "true", "yes", "on")
        return default

    @staticmethod
    def _get_cfg_str(cfg: Dict[str, Any], key: str, default: str = "") -> str:
        pc = cfg.get(key) or cfg.get(key.strip().lower())
        if pc is None:
            return default
        v = getattr(pc, "raw", getattr(pc, "value", pc))
        return str(v)

    # ---- 与 C++ 同名：解析限速字符串 ----
    def paraseLimitStr(self,
                       s: str,
                       outData: List[LimitData],
                       init_limit_speed: float,
                       init_limit_acc: float,
                       init_limit_temp: float) -> None:
        """
        解析：
          [[0.5,1.0,100,6000,220],[1.0,1.5,80,5500,210], ...]
        每项为 [value1_mm, value2_mm, speed2, acc2, (temp2)]
        并为连续项自动继承前一项末端值作为本项的 speed1/Acc1/Temp1。
        """
        if not s:
            return
        try:
            arr = ast.literal_eval(s)
        except Exception:
            return
        if not isinstance(arr, list):
            return

        for item in arr:
            if not (isinstance(item, (list, tuple)) and 4 <= len(item) <= 5):
                continue
            try:
                v1_mm, v2_mm = float(item[0]), float(item[1])
                sp2, ac2 = float(item[2]), float(item[3])
                tp2 = float(item[4]) if len(item) == 5 else None
            except Exception:
                continue

            lim = LimitData()
            lim.value1 = _mm2int(v1_mm)
            lim.value2 = _mm2int(v2_mm)
            # 来自上一段的右端值，否则使用初始值
            if outData:
                lim.speed1 = outData[-1].speed2
                lim.Acc1 = outData[-1].Acc2
                lim.Temp1 = outData[-1].Temp2
            else:
                lim.speed1 = init_limit_speed
                lim.Acc1 = init_limit_acc
                lim.Temp1 = init_limit_temp

            lim.speed2 = sp2
            lim.Acc2 = ac2
            lim.Temp2 = tp2 if tp2 is not None else lim.Temp1  # 若没提供温度，延续

            outData.append(lim)

    # ---- 对外开关读取 ----
    def get_acceleration_limit_mess_enable(self) -> bool:
        return self.acceleration_limit_mess_enable

    def get_acceleration_limit_height_enable(self) -> bool:
        return self.acceleration_limit_height_enable

    # ---- 对速度/加速度的检测（封装） ----
    def detect_speed(self, speed: float, value_e: float, current_layer_z: float) -> float:
        if self.acceleration_limit_mess_enable or self.acceleration_limit_height_enable:
            if self.acceleration_limit_mess_enable:
                self.detect_limit_speed(LimitType.LIMIT_MESS, value_e, current_layer_z)
            if self.acceleration_limit_height_enable:
                self.detect_limit_speed(LimitType.LIMIT_HEIGHT, value_e, current_layer_z)
            if self.current_limit_speed > 0.0:
                speed = min(speed, self.current_limit_speed)
        return speed

    def detect_speed_min(self, speed: float, value_e: float, current_layer_z: float) -> float:
        if self.acceleration_limit_mess_enable or self.acceleration_limit_height_enable:
            if self.acceleration_limit_mess_enable:
                self.detect_limit_speed(LimitType.LIMIT_MESS, value_e, current_layer_z)
            if self.acceleration_limit_height_enable:
                self.detect_limit_speed(LimitType.LIMIT_HEIGHT, value_e, current_layer_z)
            if self.current_limit_speed > 0.0:
                speed = min(speed, self.current_limit_speed * 60.0)  # C++ *60.0f
        return speed

    def detect_acc(self, acc: float, value_e: float, current_layer_z: float) -> float:
        if self.acceleration_limit_mess_enable or self.acceleration_limit_height_enable:
            if self.acceleration_limit_mess_enable:
                self.detect_limit_acc(LimitType.LIMIT_MESS, value_e, current_layer_z)
            if self.acceleration_limit_height_enable:
                self.detect_limit_acc(LimitType.LIMIT_HEIGHT, value_e, current_layer_z)
            if self.current_limit_Acc > 0.0:
                acc = min(acc, self.current_limit_Acc)
        return acc

    # ---- 初始化限制（从配置读取） ----
    def init_limit(self, *,
                   speed_limit_to_height: str = None,
                   acceleration_limit_mess: str = None
                   ) -> None:
        """
        对应 C++: SmoothSpeedAcc::init_limit(const DynamicPrintConfig& setting)
        通过 parser.load_config() 读取所有需要的键。
        """
        cfg = self._load_cfg()

        # 默认使用配置中的耗材直径/密度；只有调用方未显式传入时才读取配置
        if self.material_diameter is None:
            self.material_diameter = self._get_cfg_float(cfg, "filament_diameter", 1.75)
        if self.material_density is None:
            self.material_density = self._get_cfg_float(cfg, "filament_density", 1.24)

        # 初始速度上限（从若干速度里取最大）
        init_limit_speed = 0.0
        init_limit_speed = max(init_limit_speed, self._get_cfg_float(cfg, "outer_wall_speed", 0.0))
        init_limit_speed = max(init_limit_speed, self._get_cfg_float(cfg, "inner_wall_speed", 0.0))
        # 其余速度项在原代码中被注释，这里保持一致

        # 初始加速度上限（从若干加速度里取最大）
        init_limit_acc = 0.0
        init_limit_acc = max(init_limit_acc, self._get_cfg_float(cfg, "default_acceleration", 0.0))
        init_limit_acc = max(init_limit_acc, self._get_cfg_float(cfg, "inner_wall_acceleration", 0.0))
        init_limit_acc = max(init_limit_acc, self._get_cfg_float(cfg, "outer_wall_acceleration", 0.0))

        # 温度初始值（原代码留空 0.0）
        init_limit_temp = 0.0

        # 质量（mess）限制
        if acceleration_limit_mess:
            self.paraseLimitStr(acceleration_limit_mess, self.vctacceleration_limit_mass,
                                init_limit_speed, init_limit_acc, init_limit_temp)

        # 高度限制
        if speed_limit_to_height:
            self.paraseLimitStr(speed_limit_to_height, self.vctacceleration_limit_height,
                                init_limit_speed, init_limit_acc, init_limit_temp)

        # 初始化当前限制为“未设置”
        self.current_limit_speed = -1.0
        self.current_limit_Acc = -1.0
        self.current_limit_Temp = -1.0

    # ---- 三类检测核心：线性插值并取更严格（更小）的限制 ----
    def _calc_value_for_type(self, limitType: LimitType,
                             value_e: float, current_layer_z: float) -> float:
        if limitType == LimitType.LIMIT_MESS:
            return value_e
        elif limitType == LimitType.LIMIT_HEIGHT:
            return current_layer_z * 1000.0
        return -1.0

    def _select_limit_vector(self, limitType: LimitType) -> List[LimitData]:
        if limitType == LimitType.LIMIT_MESS:
            return self.vctacceleration_limit_mass
        elif limitType == LimitType.LIMIT_HEIGHT:
            return self.vctacceleration_limit_height
        return []

    def detect_limit_acc(self, limitType: LimitType,
                         value_e: float, current_layer_z: float) -> bool:
        value = self._calc_value_for_type(limitType, value_e, current_layer_z)
        if value < 0:
            return False
        for lim in self._select_limit_vector(limitType):
            v1, v2 = lim.value1, lim.value2
            if v1 <= value <= v2:
                s1, s2 = lim.Acc1, lim.Acc2
                if (v2 - v1) != 0 and (s1 - s2) != 0:
                    a = (s2 - s1) / (v2 - v1)
                    b = s1 - a * v1
                    out = a * value + b
                    if out < self.current_limit_Acc or self.current_limit_Acc < 0.0:
                        self.current_limit_Acc = out
        return True

    def detect_limit_temp(self, limitType: LimitType,
                          value_e: float, current_layer_z: float) -> bool:
        value = self._calc_value_for_type(limitType, value_e, current_layer_z)
        if value < 0:
            return False
        for lim in self._select_limit_vector(limitType):
            v1, v2 = lim.value1, lim.value2
            if v1 <= value <= v2:
                s1, s2 = lim.Temp1, lim.Temp2
                if (v2 - v1) != 0 and (s1 - s2) != 0:
                    a = (s2 - s1) / (v2 - v1)
                    b = s1 - a * v1
                    out = a * value + b
                    if out < self.current_limit_Temp or self.current_limit_Temp < 0.0:
                        self.current_limit_Temp = out
        return True

    def detect_limit_speed(self, limitType: LimitType,
                           value_e: float, current_layer_z: float) -> bool:
        value = self._calc_value_for_type(limitType, value_e, current_layer_z)
        if value < 0:
            return False
        for lim in self._select_limit_vector(limitType):
            v1, v2 = lim.value1, lim.value2
            if v1 <= value <= v2:
                s1, s2 = lim.speed1, lim.speed2
                if (v2 - v1) != 0 and (s1 - s2) != 0:
                    a = (s2 - s1) / (v2 - v1)
                    b = s1 - a * v1
                    out = a * value + b
                    if out < self.current_limit_speed or self.current_limit_speed < 0.0:
                        self.current_limit_speed = out
        return True

    # ---- 和 C++ 同名：根据 height 表计算最大速度限制（保持原语义） ----
    def calculatMaxSpeedLimitToHeight(self, speed_limit_to_height: FlowTempGraph,
                                      current_layer_z: float) -> None:
        limit_data: List[Tuple[float, float]] = []
        for d in speed_limit_to_height.data:
            limit_data.append((d.flow, d.temp))

        # 排序：先按 flow 升序，同 flow 按 temp 降序
        limit_data.sort(key=lambda x: (x[0], -x[1]))

        for flow, temp in limit_data:
            if current_layer_z >= _mm2int(flow):
                self.max_speed_limit_to_height = temp


# ================== max_volumetric_extrusion_rate_slope ==================
def parse_max_volumetric_extrusion_rate_slope(
        gcode_path: Path | str,
        expected_value: float,
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    校验 max_volumetric_extrusion_rate_slope 是否开启：
    - 规则：最后一层 OUTER_WALL 的路径点数被细分。expected_value > 0 视为开启；=0 视为关闭。
    - 关闭：最后一层外墙路径点数应为 5（或不超过 5）。
    - 开启：最后一层至少有一条外墙路径点数 > 5。
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    # 仅关心外墙，跳过首层
    layers = parser.get_type_contours_per_layer(
        types=[ExtrusionType.OUTER_WALL],
        skip_layers=[0],
    )

    if not layers:
        details = {
            "expected": expected_value,
            "target_layer": None,
            "outer_paths_counts": [],
            "max_points": 0,
            "min_points": 0,
            "note": "No outer wall regions parsed.",
            "match": False,
        }
        return False, expected_value, details

    # 选取包含外墙的最高层
    last_layer = max(layers, key=lambda l: l.index)
    path_counts: List[int] = []
    for _oid, type_map in (last_layer.regions or {}).items():
        region = type_map.get(ExtrusionType.OUTER_WALL.value)
        if region is None:
            continue
        for path in region.paths or []:
            path_counts.append(len(path.points))

    if not path_counts:
        details = {
            "expected": expected_value,
            "target_layer": last_layer.index,
            "outer_paths_counts": [],
            "max_points": 0,
            "min_points": 0,
            "note": "No outer wall paths found on target layer.",
            "match": False,
        }
        return False, expected_value, details

    max_pts = max(path_counts)
    min_pts = min(path_counts)

    # 判断开启/关闭的预期与实际
    expect_enabled = expected_value > 0
    if expect_enabled:
        # 开启：至少有一条路径点数大于 5
        ok = max_pts > 5
        note = None if ok else f"expected enabled (points>5), got max_points={max_pts}"
    else:
        # 关闭：所有路径点数不应超过 5
        ok = max_pts <= 5
        note = None if ok else f"expected disabled (points<=5), got max_points={max_pts}"

    details: Dict[str, Any] = {
        "expected": expected_value,
        "target_layer": last_layer.index,
        "outer_paths_counts": path_counts,
        "max_points": max_pts,
        "min_points": min_pts,
        "expected_enabled": expect_enabled,
        "note": note,
        "match": ok,
    }
    return ok, expected_value, details


def parse_speed_limit_to_height_enable(
        gcode_path: Path | str,
        expected_speed_limit_to_height_enable: bool,
        speed_limit_to_height: str,
        speed_tolerance: float = 0.1,
        acc_tolerance: float = 2.0,
) -> Tuple[bool, bool, Dict[str, Any]]:
    """
    speed_limit_to_height_enable 校验：
    - 使用 SmoothSpeedAcc，按照传入的 speed_limit_to_height 初始化限速曲线；
    - 跳过首层，检查 OUTER_WALL/INNER_WALL/SPARSE_INFILL/INTERNAL_SOLID_INFILL 四类路径的点：
        * 速度：raw_speed 经 detect_speed 裁剪后，应与 point.f 匹配；
        * 加速度：raw_acc 经 detect_acc 裁剪后，应与 velocity_limits[ACCEL] 匹配。
    - 若所有点均符合裁剪结果，则视为开关状态匹配预期。
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    # 辅助函数：从 cfg 读取浮点
    def _cfg_float(cfg: Dict[str, Any], key: str, default: float = 0.0) -> float:
        pc = cfg.get(key) or cfg.get(key.strip().lower())
        if pc is None:
            return default
        try:
            v = getattr(pc, "value", pc)
            return float(v)
        except Exception:
            return default

    cfg = parser.load_config() or {}

    # 初始化 SmoothSpeedAcc，传入开关与限速曲线
    ssa = SmoothSpeedAcc(
        parser,
        speed_limit_to_height_enable=expected_speed_limit_to_height_enable,
    )
    ssa.init_limit(speed_limit_to_height=speed_limit_to_height)

    # 提取层高信息，便于传递当前 z
    layer_meta = parser.extract_layers()  # [(z, h), ...]

    # 目标挤出类型与对应的速度/加速度配置键
    target_types = [
        ExtrusionType.OUTER_WALL,
        ExtrusionType.INNER_WALL,
        ExtrusionType.SPARSE_INFILL,
        ExtrusionType.INTERNAL_SOLID_INFILL,
    ]
    speed_keys = {
        ExtrusionType.OUTER_WALL.value: "outer_wall_speed",
        ExtrusionType.INNER_WALL.value: "inner_wall_speed",
        ExtrusionType.SPARSE_INFILL.value: "sparse_infill_speed",
        ExtrusionType.INTERNAL_SOLID_INFILL.value: "internal_solid_infill_speed",
    }
    acc_keys = {
        ExtrusionType.OUTER_WALL.value: "outer_wall_acceleration",
        ExtrusionType.INNER_WALL.value: "inner_wall_acceleration",
        ExtrusionType.SPARSE_INFILL.value: "sparse_infill_acceleration",
        ExtrusionType.INTERNAL_SOLID_INFILL.value: "internal_solid_infill_acceleration",
    }
    default_acc = _cfg_float(cfg, "default_acceleration", 0.0)

    layers = parser.get_type_contours_per_layer(types=target_types, skip_layers=[0])

    mismatches_speed: List[Dict[str, Any]] = []
    mismatches_acc: List[Dict[str, Any]] = []
    missing_accel: List[Dict[str, Any]] = []
    checked_layers: List[int] = []

    for layer in layers:
        if layer.index == 0:
            continue
        checked_layers.append(layer.index)
        z = layer_meta[layer.index][0] if layer_meta and layer.index < len(layer_meta) else 0.0
        region_map = layer.regions or {}
        for oid, type_map in region_map.items():
            for tname, region in (type_map or {}).items():
                raw_speed = _cfg_float(cfg, speed_keys.get(tname, ""), 0.0)
                raw_acc = _cfg_float(cfg, acc_keys.get(tname, ""), default_acc)
                expected_speed = ssa.detect_speed(raw_speed, 0.0, z)
                expected_acc = ssa.detect_acc(raw_acc, 0.0, z)

                # 检查路径点速度
                for path_idx, path in enumerate(region.paths or []):
                    for point_idx, pt in enumerate(path.points or []):
                        actual_speed = float(pt.f) if pt.f is not None else None
                        if actual_speed is None or abs(actual_speed - expected_speed) > speed_tolerance:
                            mismatches_speed.append({
                                "layer": layer.index,
                                "object_id": oid,
                                "type": tname,
                                "path_idx": path_idx,
                                "point_idx": point_idx,
                                "expected_speed": expected_speed,
                                "actual_speed": actual_speed,
                                "tolerance": speed_tolerance,
                            })

                # 检查加速度（LayerRegion velocity_limits.ACCEL）
                accel_val = None
                if region.velocity_limits:
                    accel_val = region.velocity_limits.get(_VEL_KEYS_CANON[0])
                if accel_val is None:
                    missing_accel.append({
                        "layer": layer.index,
                        "object_id": oid,
                        "type": tname,
                    })
                else:
                    try:
                        actual_acc = float(accel_val)
                    except (TypeError, ValueError):
                        actual_acc = None
                    if actual_acc is None or abs(actual_acc - expected_acc) > acc_tolerance:
                        mismatches_acc.append({
                            "layer": layer.index,
                            "object_id": oid,
                            "type": tname,
                            "expected_acc": expected_acc,
                            "actual_acc": actual_acc,
                            "tolerance": acc_tolerance,
                        })

    ok = (not mismatches_speed) and (not mismatches_acc) and (not missing_accel)
    details = {
        "expected_enabled": expected_speed_limit_to_height_enable,
        "speed_limit_to_height": speed_limit_to_height,
        "checked_layers": sorted(set(checked_layers)),
        "speed_tolerance": speed_tolerance,
        "acc_tolerance": acc_tolerance,
        "mismatches_speed": mismatches_speed,
        "mismatches_acc": mismatches_acc,
        "missing_accel": missing_accel,
        "match": ok,
        "note": None if ok else "See mismatches for speed/acc comparisons.",
    }
    return ok, expected_speed_limit_to_height_enable, details


def parse_acceleration_limit_mess_enable(
        gcode_path: Path | str,
        expected_acceleration_limit_mess_enable: bool,
        acceleration_limit_mess: str,
        material_diameter: float,
        material_density: float,
        speed_tolerance: float = 0.1,
        acc_tolerance: float = 2.0,
) -> Tuple[bool, bool, Dict[str, Any]]:
    """
    acceleration_limit_mess_enable 校验：
    - 按重量插值限速：使用 SmoothSpeedAcc(acceleration_limit_mess_enable) + acceleration_limit_mess 曲线；
    - 不跳过首层：首层只用于汇总耗材重量（extrude 点的 e 累加后经 weight_from_gcode 转为重量）；
    - 校验从第 1 层开始，按挤出类型切分 BLOCK（遇到不同挤出类型即结束上一个 BLOCK）：
        * BLOCK 内速度 expected_speed = detect_speed(raw_speed, total_weight, z)，与 point.f 对比；
        * BLOCK 内加速度 expected_acc = detect_acc(raw_acc, total_weight, z)，与 velocity_limits.ACCEL 对比。
    - 每个 BLOCK 结束后累加该 BLOCK 的挤出耗材重量到 total_weight。
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    cfg = parser.load_config() or {}

    def _cfg_float(key: str, default: float = 0.0) -> float:
        pc = cfg.get(key) or cfg.get(key.strip().lower())
        if pc is None:
            return default
        try:
            v = getattr(pc, "value", pc)
            return float(v)
        except Exception:
            return default

    # 目标挤出类型
    target_types = {
        ExtrusionType.OUTER_WALL.value,
        ExtrusionType.INNER_WALL.value,
        ExtrusionType.SPARSE_INFILL.value,
        ExtrusionType.INTERNAL_SOLID_INFILL.value,
    }
    speed_keys = {
        ExtrusionType.OUTER_WALL.value: "outer_wall_speed",
        ExtrusionType.INNER_WALL.value: "inner_wall_speed",
        ExtrusionType.SPARSE_INFILL.value: "sparse_infill_speed",
        ExtrusionType.INTERNAL_SOLID_INFILL.value: "internal_solid_infill_speed",
    }
    acc_keys = {
        ExtrusionType.OUTER_WALL.value: "outer_wall_acceleration",
        ExtrusionType.INNER_WALL.value: "inner_wall_acceleration",
        ExtrusionType.SPARSE_INFILL.value: "sparse_infill_acceleration",
        ExtrusionType.INTERNAL_SOLID_INFILL.value: "internal_solid_infill_acceleration",
    }
    default_acc = _cfg_float("default_acceleration", 0.0)

    # 初始化 SmoothSpeedAcc，仅开启 mess 模式
    ssa = SmoothSpeedAcc(
        parser,
        acceleration_limit_mess_enable=expected_acceleration_limit_mess_enable,
        speed_limit_to_height_enable=False,
        material_diameter=material_diameter,
        material_density=material_density,
    )
    ssa.init_limit(acceleration_limit_mess=acceleration_limit_mess)

    # 读取所有路径点（不跳过首层，用于累计重量）
    motion = parser.get_motion_paths(start_layer=0, end_layer=10) or {}  # TODO

    # 预计算首层耗材重量（extrude 点的 e 累加）
    def _weight_from_layer(layer_points):
        e_sum = sum(pt.e for pt in layer_points if getattr(pt, "kind", None) == "extrude" and pt.e is not None)
        return weight_from_gcode(e_sum, ssa.material_diameter or material_diameter,
                                 ssa.material_density or material_density)

    total_weight = 0.0
    if 0 in motion:
        total_weight += _weight_from_layer(motion.get(0) or [])

    # 帮助函数：结束一个 BLOCK 时校验速度/加速度并累加耗材
    mismatches_speed: List[Dict[str, Any]] = []
    mismatches_acc: List[Dict[str, Any]] = []
    missing_accel: List[Dict[str, Any]] = []
    checked_layers: List[int] = []

    def _process_block(layer_idx: int, oid: int | None, tname: str | None, pts: List[Any]) -> None:
        # 处理同一挤出类型形成的一个 BLOCK，按照总重量裁剪速度/加速度并校验
        nonlocal total_weight
        if not tname or tname not in target_types or not pts:
            return
        z = pts[0].z if hasattr(pts[0], "z") else 0.0
        raw_speed = _cfg_float(speed_keys.get(tname, ""), 0.0)
        raw_acc = _cfg_float(acc_keys.get(tname, ""), default_acc)
        expected_speed = ssa.detect_speed(raw_speed, total_weight, z)
        expected_acc = ssa.detect_acc(raw_acc, total_weight, z)

        block_e_sum = 0.0
        for idx, pt in enumerate(pts):
            if getattr(pt, "kind", None) == "extrude" and pt.e is not None:
                block_e_sum += pt.e
            actual_speed = float(pt.f) if pt.f is not None else None
            if tname != ExtrusionType.INTERNAL_SOLID_INFILL.value and (actual_speed is None or abs(
                    actual_speed - expected_speed) > speed_tolerance):
                mismatches_speed.append({
                    "layer": layer_idx,
                    "object_id": oid,
                    "type": tname,
                    "point_idx": idx,
                    "expected_speed": expected_speed,
                    "actual_speed": actual_speed,
                    "tolerance": speed_tolerance,
                })

            accel_val = None
            if getattr(pt, "velocity_limits", None):
                accel_val = pt.velocity_limits.get(ACCEL_KEY)
            if accel_val is None:
                missing_accel.append({
                    "layer": layer_idx,
                    "object_id": oid,
                    "type": tname,
                })
            else:
                try:
                    actual_acc = float(accel_val)
                except (TypeError, ValueError):
                    actual_acc = None
                if actual_acc is None or abs(actual_acc - expected_acc) > acc_tolerance:
                    mismatches_acc.append({
                        "layer": layer_idx,
                        "object_id": oid,
                        "type": tname,
                        "expected_acc": expected_acc,
                        "actual_acc": actual_acc,
                        "tolerance": acc_tolerance,
                    })

        # BLOCK 结束后累加耗材重量
        if block_e_sum > 0:
            total_weight += weight_from_gcode(block_e_sum, ssa.material_diameter or material_diameter,
                                              ssa.material_density or material_density)

    # 按层处理（跳过首层的校验，但参与重量累计）
    for layer_idx in sorted(motion):
        pts_layer = motion[layer_idx] or []
        if layer_idx != 0 and layer_idx != 99:
            checked_layers.append(layer_idx)
            current_type = None
            current_block: List[Any] = []
            current_oid = None  # 无单独 oid，默认 None

            def flush_block():
                _process_block(layer_idx, current_oid, current_type, current_block)

            for pt in pts_layer:
                if pt.kind != "extrude":
                    continue
                tname = pt.extrusion_type
                if tname != current_type:
                    flush_block()
                    current_type = tname
                    current_block = [pt]
                else:
                    current_block.append(pt)
            flush_block()
        else:
            # 首层已在 total_weight 处理中，不校验
            continue

    ok = (not mismatches_speed) and (not mismatches_acc) and (not missing_accel)
    details = {
        "expected_enabled": expected_acceleration_limit_mess_enable,
        "acceleration_limit_mess": acceleration_limit_mess,
        "material_diameter": ssa.material_diameter or material_diameter,
        "material_density": ssa.material_density or material_density,
        "checked_layers": sorted(set(checked_layers)),
        "speed_tolerance": speed_tolerance,
        "acc_tolerance": acc_tolerance,
        "mismatches_speed": mismatches_speed,
        "mismatches_acc": mismatches_acc,
        "missing_accel": missing_accel,
        "final_total_weight": total_weight,
        "note": None if ok else "See mismatches for speed/acc or missing accel limits.",
        "match": ok,
    }
    return ok, expected_acceleration_limit_mess_enable, details


def parse_max_volumetric_extrusion_rate_slope_segment_length(
        gcode_path: Path | str,
        expected_segment_length: float,
        tolerance: float = 1e-6,
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    校验分段长度限制（基于全段统计，不再显式定义平滑段）：
    - 取含外墙的最高一层（跳过首层），收集 OUTER_WALL 所有相邻点的段长。
    - 拆分：<=阈值（expected_segment_length+tolerance）的“正常段”，>阈值的“超阈段”。
    - 计算正常段均值 AVG；对每个超阈段，若 (len-AVG)/AVG > 20% 则舍弃，否则视为违规。
    - 若超阈段全部被舍弃（或无超阈段）则通过；无正常段时提示可能检测算法不适用。
    """
    path_obj = Path(gcode_path)
    parser = GCodeParserEx(path_obj)

    layers = parser.get_type_contours_per_layer(
        types=[ExtrusionType.OUTER_WALL],
        skip_layers=[0],
    )

    if not layers:
        details = {
            "expected": expected_segment_length,
            "tolerance": tolerance,
            "target_layer": None,
            "max_segment_length": None,
            "violations": [],
            "normal_avg": None,
            "segments_total": 0,
            "note": "No outer wall regions parsed.",
            "match": False,
        }
        return False, expected_segment_length, details

    # 选取包含外墙的最高层
    last_layer = max(layers, key=lambda l: l.index)

    def _segment_lengths(path_points):
        pts = path_points or []
        return [((b.x - a.x) ** 2 + (b.y - a.y) ** 2) ** 0.5 for a, b in zip(pts, pts[1:])]

    all_segments: List[float] = []
    max_points_per_path = 0
    for type_map in (last_layer.regions or {}).values():
        region = type_map.get(ExtrusionType.OUTER_WALL.value)
        if region is None:
            continue
        for path in region.paths or []:
            pts = path.points or []
            max_points_per_path = max(max_points_per_path, len(pts))
            all_segments.extend(_segment_lengths(pts))

    # 若最高层外墙路径点数不足或无段可检，直接失败并提示
    if max_points_per_path <= 5:
        details = {
            "expected": expected_segment_length,
            "tolerance": tolerance,
            "target_layer": last_layer.index,
            "max_segment_length": None,
            "violations": [],
            "normal_avg": None,
            "segments_total": 0,
            "note": "Outer wall path points <= 5 on target layer; pressure equalizer likely disabled, length check skipped.",
            "match": False,
        }
        return False, expected_segment_length, details
    if not all_segments:
        details = {
            "expected": expected_segment_length,
            "tolerance": tolerance,
            "target_layer": last_layer.index,
            "violations": [],
            "normal_avg": None,
            "segments_total": 0,
            "note": "No segments found on target layer.",
            "match": False,
        }
        return False, expected_segment_length, details

    threshold = expected_segment_length + tolerance
    normal_segments = [s for s in all_segments if s <= threshold]
    abnormal_segments = [s for s in all_segments if s > threshold]

    if not normal_segments:
        details = {
            "expected": expected_segment_length,
            "tolerance": tolerance,
            "target_layer": last_layer.index,
            "violations": [],
            "normal_avg": None,
            "segments_total": len(all_segments),
            "note": "No normal segments detected!",
            "match": False,
        }
        return False, expected_segment_length, details

    normal_avg = sum(normal_segments) / len(normal_segments)
    # 如果正常段均值本身大于期望值，直接视为违规
    mean_violation = normal_avg > (expected_segment_length + tolerance)

    violations: List[Dict[str, Any]] = []
    discarded = 0
    for seg_len in abnormal_segments:
        ratio = (seg_len - normal_avg) / normal_avg if normal_avg > 0 else float("inf")
        if ratio > 0.2:
            discarded += 1  # 离群超阈段，忽略
            continue
        violations.append({
            "segment_length": seg_len,
            "normal_avg": normal_avg,
            "ratio": ratio,
            "expected_max": expected_segment_length,
            "tolerance": tolerance,
            "note": "Abnormal segment retained (within 20% of avg).",
        })

    ok = not violations and not mean_violation
    details = {
        "expected": expected_segment_length,
        "tolerance": tolerance,
        "target_layer": last_layer.index,
        "violations": violations,
        "normal_avg": normal_avg,
        "segments_total": len(all_segments),
        "segments_normal": len(normal_segments),
        "segments_abnormal": len(abnormal_segments),
        "segments_abnormal_discarded": discarded,
        "match": ok,
        "note": None if ok else ("Normal segment mean exceeds expected max." if mean_violation
                                 else "Abnormal segments remain (check detection/tolerance logic)."),
    }
    return ok, expected_segment_length, details


if __name__ == "__main__":
    parser = GCodeParserEx(r"C:\Users\118388\Desktop\automation\test_m_v.gcode")
    ssa = SmoothSpeedAcc(parser, True, False,
                         material_diameter=1.75, material_density=100)

    speed_limit_to_height = "[[0,10,66,666]]"
    acceleration_limit_mess = "[[0,0.1,30,6000]]"
    ssa.init_limit(
        speed_limit_to_height=speed_limit_to_height,
        acceleration_limit_mess=acceleration_limit_mess
    )  # 从 gcode 的 CONFIG 区读取所需参数

    v = 0.12  # 示例：单位与原 C++一致，作为 "value_e"
    z = 0.6  # 当前层高（mm）
    spd = ssa.detect_speed(300, v, z)  # 返回受限后的速度
    acc = ssa.detect_acc(5000.0, v, z)  # 返回受限后的加速度
    pass
