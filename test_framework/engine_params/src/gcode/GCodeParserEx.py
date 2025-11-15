# engine_params/src/gcode/GCodeParserEx.py
# -*- coding: utf-8 -*-
from __future__ import annotations

import mmap
import re
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Iterable, Literal, Protocol, Any, Union

ConfigValue = Union[bool, int, float, str]


@dataclass(frozen=True)
class ParsedConfig:
    value: ConfigValue
    is_percent: bool
    raw: str


from engine_params.src.gcode.constants import ExtrusionType

# 语法/正则/轻解析工具（完全独立，不依赖旧 GCodeParser）
try:
    from .GCode import (
        HEADER_BEGIN, HEADER_END, THUMBNAIL_BEGIN, THUMBNAIL_END,
        EXEC_BEGIN, EXEC_END, CONFIG_BEGIN, CONFIG_END,
        LAYER_MARK, TYPE_PREFIX, WIPE_BEGIN, WIPE_END,
        OBJ_BEGIN_RE, OBJ_END_RE,
        ID_FROM_NAME_RE_B, COPY_FROM_NAME_RE_B,
        CFG_LINE_RE, Z_RE, H_RE,
        pre_comment, is_g1, arc_mode, has_x, has_y, has_e, has_z, has_f,
        parse_xy, parse_xy_loose, parse_e, parse_f, parse_ij, parse_r, classify_kind, build_arc_meta, ArcMeta, _Z_NUM_B,
        _RX_VEL_KV, _RX_SET_VEL, _VEL_KEYS_CANON
    )
except Exception:
    from GCode import (
        HEADER_BEGIN, HEADER_END, THUMBNAIL_BEGIN, THUMBNAIL_END,
        EXEC_BEGIN, EXEC_END, CONFIG_BEGIN, CONFIG_END,
        LAYER_MARK, TYPE_PREFIX, WIPE_BEGIN, WIPE_END,
        OBJ_BEGIN_RE, OBJ_END_RE,
        ID_FROM_NAME_RE_B, COPY_FROM_NAME_RE_B,
        CFG_LINE_RE, Z_RE, H_RE,
        pre_comment, is_g1, arc_mode, has_x, has_y, has_e, has_z, has_f,
        parse_xy, parse_xy_loose, parse_e, parse_f, parse_ij, parse_r, classify_kind, build_arc_meta, ArcMeta, _Z_NUM_B,
        _RX_VEL_KV, _RX_SET_VEL, _VEL_KEYS_CANON
    )


def _parse_z(body: bytes) -> Optional[float]:
    m = _Z_NUM_B.search(body)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None


# ===================== Point / Point3D 定义 =====================
@dataclass(frozen=True)
class Point:
    """
    旧的测试用了这个类，后面新的尽量都用 Point3D 类。
    """
    x: float
    y: float
    kind: Literal["extrude", "toolchange", "travel", "wipe"]
    f: Optional[float] = None  # 新增：逐点 F（mm/s），来自该点所在行最近一次出现的 F
    feedrate: Optional[float] = None  # mm/s，即TYPE挤出块下方找到的第一个F指令转化的速度
    has_z: bool = False
    has_f: bool = False
    has_e: bool = False
    offset: Optional[int] = None
    e: Optional[float] = None
    arc_direction: Optional[Literal["cw", "ccw"]] = None
    arc_center_offset: Optional[Tuple[float, float]] = None
    arc_center: Optional[Tuple[float, float]] = None
    arc_radius: Optional[float] = None
    arc_radius_deviation: Optional[float] = None


# ===================== Point / Point3D 定义 =====================
@dataclass(frozen=True)
class Point3D:
    x: float
    y: float
    z: float
    f: float
    kind: Literal["extrude", "travel", "wipe", "fanchange", "retract", "unretract"]
    extrusion_type: Optional[str] = None  # 规整后的类型名（与 ExtrusionType.value 对齐或 None）
    has_f: bool = False
    has_e: bool = False
    offset: Optional[int] = None
    e: Optional[float] = None
    feedrate: Optional[float] = None  # 记录的是切片参数中设置的区域级速度，mm/s，即TYPE挤出块下方找到的第一个F指令转化的速度
    arc_direction: Optional[Literal["cw", "ccw"]] = None
    arc_center_offset: Optional[Tuple[float, float]] = None
    arc_center: Optional[Tuple[float, float]] = None
    arc_radius: Optional[float] = None
    arc_radius_deviation: Optional[float] = None
    # —— 逐点携带“当前就近继承”的速度限制三键（SET_VELOCITY_LIMIT）
    #    字典键名统一为规范大写（ACCEL / ACCEL_TO_DECEL / SQUARE_CORNER_VELOCITY），值为 float。
    #    注意：这是一个“快照”（点生成时复制 current_limits），不会在 Point3D 内部再被修改。
    velocity_limits: Dict[str, float] = field(default_factory=dict)

    # ---- 打印相关 ----
    def __str__(self) -> str:
        # 默认 3 位小数
        return self._format_with_precision(".3f")

    def __repr__(self) -> str:
        # 在 REPL/容器里也更易读
        return f"Point3D<{self._format_with_precision('.3f')}>"

    def __format__(self, spec: str) -> str:
        """
        允许 f-string 精度控制：
          - f"{pt}"        -> 默认 .3f
          - f"{pt:.2f}"    -> 所有浮点两位小数
          - f"{pt:.0f}"    -> 整数样式
        """
        prec = spec if spec else ".3f"
        return self._format_with_precision(prec)

    # ---- 私有辅助 ----
    def _format_with_precision(self, prec: str) -> str:
        def ff(v):
            return format(v, prec) if v is not None else None

        parts = []

        # 基本：kind 与坐标
        parts.append(self.kind)
        parts.append(f"({ff(self.x)},{ff(self.y)},{ff(self.z)})")

        # 类型（如外墙/填充等）
        if self.extrusion_type:
            parts.append(f"[{self.extrusion_type}]")

        # 进给/速度：优先人类友好的 feedrate（mm/s），否则用原始 F（有则显示）
        if self.feedrate is not None:
            parts.append(f"v={ff(self.feedrate)} mm/s")
        elif self.has_f:
            parts.append(f"F={ff(self.f)}")

        # 挤出量（有 E 标记才显示）
        if self.has_e and self.e is not None:
            parts.append(f"E={ff(self.e)}")

        # 圆弧信息（如存在）
        if self.arc_direction:
            arc_bits = [f"arc={self.arc_direction}"]
            if self.arc_radius is not None:
                arc_bits.append(f"r={ff(self.arc_radius)}")
            if self.arc_center_offset is not None:
                cx, cy = self.arc_center_offset
                arc_bits.append(f"ctr_off=({ff(cx)},{ff(cy)})")
            if self.arc_center is not None:
                Cx, Cy = self.arc_center
                arc_bits.append(f"ctr=({ff(Cx)},{ff(Cy)})")
            if self.arc_radius_deviation is not None:
                arc_bits.append(f"dr={ff(self.arc_radius_deviation)}")
            parts.append(" ".join(arc_bits))

        return " ".join(parts)


# ===================== 数据 =====================
@dataclass
class ExtrusionPath:
    points: List[Point] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.points)

    def add(self, p: Point) -> None:
        self.points.append(p)

    def as_points(self) -> List[Point]:
        return self.points


@dataclass
class LayerRegion:
    extrusion_type: str
    paths: List[ExtrusionPath] = field(default_factory=list)
    feedrate: Optional[float] = None  # 局部的速度参数，mm/s。读取的是切片软件中设置的局部挤出块的速度参数。
    # —— 就近向上命中的 SET_VELOCITY_LIMIT
    velocity_limits: Dict[str, float] = field(default_factory=dict)

    def add_path(self, pts: Iterable[Point]) -> None:
        self.paths.append(ExtrusionPath(list(pts)))

    def ensure_path(self) -> ExtrusionPath:
        self.paths.append(ExtrusionPath([]))
        return self.paths[-1]


@dataclass
class Layer:
    index: int
    z: Optional[float] = None
    height: Optional[float] = None
    prev: Optional["Layer"] = None
    next: Optional["Layer"] = None
    regions: Dict[int, Dict[str, LayerRegion]] = field(default_factory=dict)

    def ensure_region(self, object_id: int, type_name: str) -> LayerRegion:
        mp = self.regions.setdefault(object_id, {})
        reg = mp.get(type_name)
        if reg is None:
            reg = LayerRegion(type_name)
            mp[type_name] = reg
        return reg

    def object_ids(self) -> List[int]:
        return sorted(self.regions.keys())

    def types_on_object(self, object_id: int) -> List[str]:
        return sorted((self.regions.get(object_id) or {}).keys())


# ===================== 进给解析接口 =====================
class FeedrateResolver(Protocol):
    def resolve_region_feedrate(
            self,
            mm: mmap.mmap,
            *,
            layer_start: int,
            layer_end: int,
            type_start: int,
            type_end: int,
            obj_seg_start: int,
            obj_seg_end: int,
    ) -> Optional[float]:
        ...


class DefaultFeedrateResolver:
    _RX_X = re.compile(br'\bX[ \t]*([+-]?(?:\d+(?:\.\d*)?|\.\d+))', re.IGNORECASE)
    _RX_Y = re.compile(br'\bY[ \t]*([+-]?(?:\d+(?:\.\d*)?|\.\d+))', re.IGNORECASE)

    def __init__(self, *, head_lookahead_lines: int = 6, allow_f_on_move_as_global: bool = False):
        self.head_lookahead_lines = int(head_lookahead_lines)
        self.allow_f_on_move_as_global = bool(allow_f_on_move_as_global)

    @staticmethod
    def _scan_after(mm: mmap.mmap, *, anchor: int, bound: int, accept) -> Optional[Tuple[int, Any]]:
        pos = mm.find(b"\n", anchor, bound)
        if pos == -1:
            return None
        pos += 1
        while pos < bound:
            nl = mm.find(b"\n", pos, bound)
            line_end = nl if nl != -1 else bound
            body = pre_comment(mm[pos:line_end])
            if body:
                val = accept(body, pos, line_end)
                if val is not None:
                    return (pos, val)
            if nl == -1:
                break
            pos = nl + 1
        return None

    @staticmethod
    def _scan_after_limited(mm: mmap.mmap, *, anchor: int, bound: int, accept, max_lines: int) -> Optional[
        Tuple[int, Any]]:
        pos = mm.find(b"\n", anchor, bound)
        if pos == -1:
            return None
        pos += 1
        lines = 0
        while pos < bound and lines < max_lines:
            nl = mm.find(b"\n", pos, bound)
            line_end = nl if nl != -1 else bound
            body = pre_comment(mm[pos:line_end])
            if body:
                val = accept(body, pos, line_end)
                if val is not None:
                    return (pos, val)
                lines += 1
            if nl == -1:
                break
            pos = nl + 1
        return None

    @staticmethod
    def _scan_between(mm: mmap.mmap, *, start: int, end: int, accept) -> Optional[Tuple[int, Any]]:
        pos = start
        while pos < end:
            nl = mm.find(b"\n", pos, end)
            line_end = nl if nl != -1 else end
            body = pre_comment(mm[pos:line_end])
            if body:
                val = accept(body, pos, line_end)
                if val is not None:
                    return (pos, val)
            if nl == -1:
                break
            pos = nl + 1
        return None

    @staticmethod
    def _scan_before(mm: mmap.mmap, *, bound: int, anchor: int, accept) -> Optional[Tuple[int, Any]]:
        pos = mm.rfind(b"\n", bound, anchor)
        if pos == -1:
            return None
        while pos >= bound:
            line_start = mm.rfind(b"\n", bound, pos)
            line_start = (line_start + 1) if line_start != -1 else bound
            body = pre_comment(mm[line_start:pos])
            if body:
                val = accept(body, line_start, pos)
                if val is not None:
                    return (line_start, val)
            pos = mm.rfind(b"\n", bound, line_start - 1)
            if line_start == bound and pos == -1:
                break
        return None

    @classmethod
    def _has_x_any(cls, body: bytes) -> bool:
        return bool(cls._RX_X.search(body))

    @classmethod
    def _has_y_any(cls, body: bytes) -> bool:
        return bool(cls._RX_Y.search(body))

    @staticmethod
    def _parse_f(body: bytes) -> Optional[float]:
        m = re.search(br'\bF([+-]?(?:\d+(?:\.\d*)?|\.\d+))\b', body, re.IGNORECASE)
        if not m:
            return None
        try:
            return float(m.group(1))
        except Exception:
            return None

    @classmethod
    def _accept_pure_f(cls, body: bytes, *_):
        if not is_g1(body):
            return None
        if not has_f(body):
            return None
        if has_e(body) or has_z(body) or cls._has_x_any(body) or cls._has_y_any(body):
            return None
        return cls._parse_f(body)

    @classmethod
    def _accept_f_on_move(cls, body: bytes, *_):
        if not is_g1(body) or not has_f(body):
            return None
        return cls._parse_f(body)

    def resolve_region_feedrate(
            self,
            mm: mmap.mmap,
            *,
            layer_start: int,
            layer_end: int,
            type_start: int,
            type_end: int,
            obj_seg_start: int,
            obj_seg_end: int,
    ) -> Optional[float]:
        s = max(layer_start, type_start, obj_seg_start)
        e = min(layer_end, type_end, obj_seg_end)
        if e <= s:
            return None

        found = self._scan_after_limited(
            mm, anchor=type_start, bound=e, accept=self._accept_pure_f,
            max_lines=self.head_lookahead_lines
        )
        if found is not None:
            _, fval = found
            return fval

        found = self._scan_between(mm, start=s, end=e, accept=self._accept_pure_f)
        if found is not None:
            _, fval = found
            return fval

        found = self._scan_before(mm, bound=max(layer_start, obj_seg_start), anchor=type_start,
                                  accept=self._accept_pure_f)
        if found is not None:
            _, fval = found
            return fval

        if self.allow_f_on_move_as_global:
            found = self._scan_after_limited(
                mm, anchor=type_start, bound=e, accept=self._accept_f_on_move,
                max_lines=self.head_lookahead_lines
            )
            if found is not None:
                _, fval = found
                return fval

        return None


# ===================== 解析器 =====================
class GCodeParserEx:
    """
    独立解析器（不依赖旧 GCodeParser）：
      - mmap 文件
      - 找 EXECUTABLE_BLOCK、按 ;LAYER_CHANGE 切层
      - 层内：按 EXCLUDE_OBJECT_START/END 切物体段，并加入“全局补集段”捕捉 Skirt/Brim/Prime Tower
      - 按 ;TYPE: 切挤出类型，剔除 WIPE 段
      - 扫描 G1/G2/G3，支持仅 X 或仅 Y 的写法；跟踪 F 并写入 Point.f
      - 对每个 (object_id, type) region：
          * 用 FeedrateResolver 解析“全局速度”；
          * 依据 ;TYPE: 位置，就近向上命中并携带全局 SET_VELOCITY_LIMIT（补全三键的快照）
    """

    PSEUDO_GLOBAL_OID = -1  # 全局补集段（未被 object 标签包围的部分）

    def __init__(self, gcode_path: str | Path, *, feedrate_resolver: Optional[FeedrateResolver] = None):
        self.path = Path(gcode_path)
        self._layers_cache_all: Optional[List[Layer]] = None
        # CONFIG 缓存（包含元信息，见 ParsedConfig）
        self._cfg_cache: Optional[Dict[str, ParsedConfig]] = None
        self._feedrate_resolver: FeedrateResolver = feedrate_resolver or DefaultFeedrateResolver()

        # —— 全局 SET_VELOCITY_LIMIT 索引（懒构建）
        self._vel_pos: Optional[List[int]] = None  # 记录每条指令所在“行起始位置”
        self._vel_fullsnap: Optional[List[Dict[str, float]]] = None  # 对应的“补全快照”

    # ---------- 基础扫描 ----------
    @staticmethod
    def _find_pair(mm: mmap.mmap, begin: bytes, end: bytes, start_from: int = 0) -> Tuple[int, int]:
        b = mm.find(begin, start_from)
        if b < 0:
            raise ValueError(f"marker not found: {begin!r}")
        b_nl = mm.find(b"\n", b)
        if b_nl < 0:
            raise ValueError("no newline after begin marker")
        e = mm.find(end, b_nl + 1)
        if e < 0:
            raise ValueError(f"marker not found: {end!r}")
        return b_nl + 1, e

    @staticmethod
    def _find_all(mm: mmap.mmap, token: bytes, start: int, end: int) -> List[int]:
        out: List[int] = []
        pos = start
        step = len(token)
        while True:
            i = mm.find(token, pos, end)
            if i < 0:
                break
            out.append(i)
            pos = i + step
        return out

    @staticmethod
    def _index_layers(mm: mmap.mmap, exe_beg: int, exe_end: int) -> List[Tuple[int, int]]:
        out: List[Tuple[int, int]] = []
        pos = exe_beg
        while True:
            i = mm.find(LAYER_MARK, pos, exe_end)
            if i < 0:
                break
            j = mm.find(LAYER_MARK, i + len(LAYER_MARK), exe_end)
            end = j if j >= 0 else exe_end
            out.append((i, end))
            if j < 0:
                break
            pos = j
        return out

    @staticmethod
    def _parse_type_name_at(mm: mmap.mmap, type_pos: int, bound: int) -> str:
        nl = mm.find(b"\n", type_pos, bound)
        line = mm[type_pos:(nl if nl >= 0 else bound)]
        return line[len(TYPE_PREFIX):].decode("utf-8", errors="ignore").strip()

    @staticmethod
    def _linear_pair_ranges(mm: mmap.mmap, start: int, end: int,
                            begin_tok: bytes, end_tok: bytes) -> List[Tuple[int, int]]:
        begins = GCodeParserEx._find_all(mm, begin_tok, start, end)
        ends = GCodeParserEx._find_all(mm, end_tok, start, end)
        out: List[Tuple[int, int]] = []
        ei = 0
        for bpos in begins:
            while ei < len(ends) and ends[ei] < bpos:
                ei += 1
            if ei < len(ends):
                epos = ends[ei]
                nl = mm.find(b"\n", epos, end)
                epos_full = (nl + 1) if nl != -1 else end
            else:
                epos_full = end
            out.append((bpos, epos_full))
            if ei < len(ends):
                ei += 1
        return out

    @staticmethod
    def _interval_subtract(base: Tuple[int, int], holes: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        s, e = base
        if not holes or e <= s:
            return [(s, e)] if e > s else []
        holes = [(max(s, h0), min(e, h1)) for (h0, h1) in holes if min(e, h1) > max(s, h0)]
        if not holes:
            return [(s, e)]
        holes.sort()
        cur = s
        out: List[Tuple[int, int]] = []
        for h0, h1 in holes:
            if h0 > cur:
                out.append((cur, h0))
            cur = max(cur, h1)
            if cur >= e:
                break
        if cur < e:
            out.append((cur, e))
        return out

    @staticmethod
    def _interval_intersect(a: Tuple[int, int], b: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        s = max(a[0], b[0])
        e = min(a[1], b[1])
        return (s, e) if e > s else None

    @staticmethod
    def _oid_from_name_bytes(name_b: bytes) -> int:
        m = ID_FROM_NAME_RE_B.search(name_b)
        if m:
            try:
                return int(m.group(1))
            except Exception:
                pass
        return zlib.crc32(name_b) & 0x7FFFFFFF  # 稳定伪 ID

    # ---------- 层内：物体窗口 ----------
    @staticmethod
    def _object_windows_in_layer(mm: mmap.mmap, layer_start: int, layer_end: int) -> Dict[int, List[Tuple[int, int]]]:
        out: Dict[int, List[Tuple[int, int]]] = {}
        pos = layer_start
        cur_oid: Optional[int] = None
        cur_seg_start: Optional[int] = None

        while pos < layer_end:
            nl = mm.find(b"\n", pos, layer_end)
            line_end = nl if nl != -1 else layer_end
            line = mm[pos:line_end]

            m_beg = OBJ_BEGIN_RE.match(line)
            m_end = OBJ_END_RE.match(line)

            if m_beg or m_end:
                if m_beg:
                    if cur_oid is not None and cur_seg_start is not None and cur_seg_start < pos:
                        out.setdefault(cur_oid, []).append((cur_seg_start, pos))
                    oid = GCodeParserEx._oid_from_name_bytes(m_beg.group("name"))
                    cur_oid = oid
                    cur_seg_start = (line_end + 1) if nl != -1 else layer_end
                else:
                    oid = GCodeParserEx._oid_from_name_bytes(m_end.group("name"))
                    if cur_oid == oid and cur_seg_start is not None and cur_seg_start < pos:
                        out.setdefault(oid, []).append((cur_seg_start, pos))
                    cur_oid = None
                    cur_seg_start = None

            if nl == -1:
                break
            pos = nl + 1

        if cur_oid is not None and cur_seg_start is not None and cur_seg_start < layer_end:
            out.setdefault(cur_oid, []).append((cur_seg_start, layer_end))
        return out

    @staticmethod
    def _merge_intervals(intervals: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        if not intervals:
            return []
        intervals.sort()
        merged = [intervals[0]]
        for s, e in intervals[1:]:
            ls, le = merged[-1]
            if s <= le:
                merged[-1] = (ls, max(le, e))
            else:
                merged.append((s, e))
        return merged

    @classmethod
    def _with_global_segments(cls, obj_map: Dict[int, List[Tuple[int, int]]],
                              layer_start: int, layer_end: int) -> Dict[int, List[Tuple[int, int]]]:
        covered: List[Tuple[int, int]] = []
        for segs in obj_map.values():
            covered.extend(segs)
        covered = cls._merge_intervals([(max(layer_start, s), min(layer_end, e))
                                        for (s, e) in covered if e > s])
        complement: List[Tuple[int, int]] = []
        cur = layer_start
        for (s, e) in covered:
            if s > cur:
                complement.append((cur, s))
            cur = max(cur, e)
        if cur < layer_end:
            complement.append((cur, layer_end))

        out = {k: list(v) for k, v in obj_map.items()}
        if complement:
            out.setdefault(cls.PSEUDO_GLOBAL_OID, []).extend(complement)
        if not out:
            out = {cls.PSEUDO_GLOBAL_OID: [(layer_start, layer_end)]}
        return out

    # ---------- 层内：TYPE 与 WIPE ----------
    @staticmethod
    def _scan_extrusions_and_wipes(mm: mmap.mmap, layer_start: int, layer_end: int
                                   ) -> Tuple[List[Tuple[str, int, int]], List[Tuple[int, int]]]:
        tpos = GCodeParserEx._find_all(mm, TYPE_PREFIX, layer_start, layer_end)
        types: List[Tuple[str, int, int]] = []
        for i, p in enumerate(tpos):
            name = GCodeParserEx._parse_type_name_at(mm, p, layer_end)
            end = tpos[i + 1] if i + 1 < len(tpos) else layer_end
            types.append((name, p, end))
        wipes = GCodeParserEx._linear_pair_ranges(mm, layer_start, layer_end, WIPE_BEGIN, WIPE_END)
        return types, wipes

    # ---------- 层元信息 ----------
    @staticmethod
    def _parse_layer_meta(blob: bytes) -> Tuple[Optional[float], Optional[float]]:
        z = h = None
        for line in blob.decode("utf-8", errors="ignore").splitlines():
            if z is None:
                mz = Z_RE.match(line)
                if mz:
                    try:
                        z = float(mz.group(1))
                    except ValueError:
                        pass
            if h is None:
                mh = H_RE.match(line)
                if mh:
                    try:
                        h = float(mh.group(1))
                    except ValueError:
                        pass
            if z is not None and h is not None:
                break
        return z, h

    # ---------- 类型名规整 ----------
    @staticmethod
    def _canon_type_name(name_raw: str) -> str:
        s = ExtrusionType.as_filter([name_raw])
        return next(iter(s)) if s else name_raw.strip()

    # ---------- 换刀锚点（回溯） ----------
    def _find_upward_toolchange(self, mm: mmap.mmap, seg_start: int, block_start: int
                                ) -> Optional[Tuple[float, float]]:
        if block_start <= seg_start:
            return None
        blob = mm[seg_start:block_start]

        last_xy: Optional[Tuple[float, float]] = None
        pos = 0
        end = len(blob)
        while pos < end:
            nl = blob.find(b"\n", pos)
            line_end = nl if nl != -1 else end
            body = pre_comment(blob[pos:line_end])
            if body:
                mode = arc_mode(body)
                # 旅行/换刀：有 X 或 Y 且无 E
                if (is_g1(body) or mode is not None) and (has_x(body) or has_y(body)) and (not has_e(body)):
                    xy = parse_xy_loose(body, last_xy)
                    if xy is not None:
                        last_xy = xy
            if nl == -1:
                break
            pos = nl + 1

        return last_xy

    # ---------- 轮廓首锚点（回溯，允许带 E；合并最近的 X/Y，返回 Point） ----------
    def _find_upward_contour_anchor(
        self, mm: mmap.mmap, seg_start: int, block_start: int
    ) -> Optional[Point]:
        """
        用于初始化 ;TYPE 挤出块的首个轮廓点锚：
        - 在 [seg_start, block_start) 区间内，自下向上回溯扫描；
        - 仅考虑 G1/G2/G3 行（是否带 E 均可）；
        - 允许某行只有 X 或只有 Y：分别记录“最近的 X”和“最近的 Y”，
          一旦两者都凑齐（可能来自不同的行），立刻返回 Point；
        - 若参与补全的任一行存在 E>0，则返回 kind='extrude' 并携带 e，否则 kind='toolchange'。
        """
        if block_start <= seg_start:
            return None

        blob = mm[seg_start:block_start]

        # 最近一次见到的 X/Y 值与来源信息（来源是否带 E>0）
        x_seen: Optional[float] = None
        y_seen: Optional[float] = None
        x_from_extrude: bool = False
        y_from_extrude: bool = False
        e_val_on_source: Optional[float] = None
        # 如果 X/Y 来自不同的行而仅有其中一行存在 E>0，我们把该行的 E 作为锚点的 e
        # 如果两行都存在 E>0，优先采用更靠近 block_start 的那行的 E（即先被记录的那个）

        pos = len(blob)
        while pos > 0:
            # 跳过尾部 CR/LF，避免空行导致 pos 不动
            while pos > 0 and blob[pos - 1:pos] in (b"\n", b"\r"):
                pos -= 1
            if pos <= 0:
                break

            prev_nl = blob.rfind(b"\n", 0, pos)
            line_start = 0 if prev_nl == -1 else (prev_nl + 1)
            raw = blob[line_start:pos]
            body = pre_comment(raw)

            if body:
                mode = arc_mode(body)
                if (is_g1(body) or mode is not None):
                    # 提取当前行是否有 E>0
                    cur_e_pos: Optional[float] = None
                    if has_e(body):
                        try:
                            ev = parse_e(body)
                            if ev is not None and ev > 0:
                                cur_e_pos = ev
                        except Exception:
                            cur_e_pos = None

                    # 提取 X、Y（如果存在且尚未记过）
                    if (x_seen is None) and DefaultFeedrateResolver._RX_X.search(body):
                        m = DefaultFeedrateResolver._RX_X.search(body)
                        if m:
                            try:
                                x_seen = float(m.group(1).decode("ascii", errors="ignore"))
                                if cur_e_pos is not None and not x_from_extrude:
                                    x_from_extrude = True
                                    # 如果两者都来自“挤出行”，优先更靠近 block_start 的值
                                    e_val_on_source = e_val_on_source if e_val_on_source is not None else cur_e_pos
                            except Exception:
                                pass
                    if (y_seen is None) and DefaultFeedrateResolver._RX_Y.search(body):
                        m = DefaultFeedrateResolver._RX_Y.search(body)
                        if m:
                            try:
                                y_seen = float(m.group(1).decode("ascii", errors="ignore"))
                                if cur_e_pos is not None and not y_from_extrude:
                                    y_from_extrude = True
                                    e_val_on_source = e_val_on_source if e_val_on_source is not None else cur_e_pos
                            except Exception:
                                pass

                    # 凑齐则返回 Point
                    if (x_seen is not None) and (y_seen is not None):
                        is_ex = (x_from_extrude or y_from_extrude)
                        if is_ex:
                            return Point(
                                x_seen, y_seen, "extrude",
                                has_z=False, has_f=False, has_e=True,
                                offset=None, e=e_val_on_source, f=None, feedrate=None
                            )
                        else:
                            return Point(
                                x_seen, y_seen, "toolchange",
                                has_z=False, has_f=False, has_e=False,
                                offset=None, e=None, f=None, feedrate=None
                            )

            if line_start == 0:
                break
            pos = line_start

        return None

    # ---------- CONFIG ----------
    @staticmethod
    def _norm_key(k: str) -> str:
        import re as _re
        return _re.sub(r"\s+", "_", k.strip().lower())

    @staticmethod
    def _parse_value_with_meta(raw: str) -> ParsedConfig:
        """
        - for load_config()
        - 返回 ParsedConfig，包含原始串/是否百分比/解析值
        """
        s = raw.strip()
        ls = s.lower()
        if ls in ("true", "false"):
            return ParsedConfig(ls == "true", False, raw)
        if ls.endswith("%"):
            try:
                num = float(s.rstrip("%").strip())
                return ParsedConfig(num / 100.0, True, raw)
            except ValueError:
                pass
        for caster in (int, float):
            try:
                return ParsedConfig(caster(s), False, raw)
            except ValueError:
                pass
        return ParsedConfig(s, False, raw)

    def load_config(self) -> Dict[str, ParsedConfig]:
        if self._cfg_cache is not None:
            return dict(self._cfg_cache)

        cfg: Dict[str, ParsedConfig] = {}
        with self.path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            beg, end = self._find_pair(mm, CONFIG_BEGIN, CONFIG_END, 0)
            text = mm[beg:end].decode("utf-8", errors="ignore")

        for line in text.splitlines():
            m = CFG_LINE_RE.match(line)
            if not m:
                continue
            k, v = m.group(1), m.group(2)
            norm_key = self._norm_key(k)
            parsed = self._parse_value_with_meta(v)
            cfg[norm_key] = parsed

        self._cfg_cache = dict(cfg)
        return cfg

    def get_config(self, key: str, default: Optional[ParsedConfig] = None) -> Optional[ParsedConfig]:
        """
        获取单个配置项（ParsedConfig）。若缓存不存在会先调用 load_config()。
        """
        if self._cfg_cache is None:
            self.load_config()
        if self._cfg_cache is None:
            return default
        norm_key = self._norm_key(key)
        return self._cfg_cache.get(norm_key, default)

    # 单位转换
    @staticmethod
    def _mm_per_min_to_mm_per_s(f: Optional[float]) -> Optional[float]:
        return (f / 60.0) if (f is not None) else None

    # ---------- 全局 SET_VELOCITY_LIMIT 索引构建与查询 ----------
    def _build_velocity_index(self, mm: mmap.mmap, exe_beg: int, exe_end: int) -> None:
        """一次性扫描 EXEC 区间的所有 SET_VELOCITY_LIMIT 行，
        为每条记录构造“向上补全”的三键快照，并缓存到 _vel_pos / _vel_fullsnap。
        """
        if self._vel_pos is not None and self._vel_fullsnap is not None:
            return

        pos_list: List[int] = []
        snap_list: List[Dict[str, float]] = []

        # 找到所有匹配位置（匹配到的是单词中的起点，我们再扩到行边界）
        hits = self._find_all(mm, b"SET_VELOCITY_LIMIT", exe_beg, exe_end)

        prev_full: Dict[str, float] = {}

        for h in hits:
            # 定位整行
            line_start = mm.rfind(b"\n", exe_beg, h)
            line_start = (line_start + 1) if line_start != -1 else exe_beg
            line_end = mm.find(b"\n", h, exe_end)
            line_end = line_end if line_end != -1 else exe_end

            raw = mm[line_start:line_end]
            body = pre_comment(raw)
            if not body:
                continue
            if not _RX_SET_VEL.search(body):
                continue

            # 抽取本行键值
            cur: Dict[str, float] = {}
            for k, v in _RX_VEL_KV.findall(body):
                k_norm = k.decode("ascii", errors="ignore").upper()
                try:
                    val = float(v.decode("ascii", errors="ignore"))
                except Exception:
                    continue
                cur[k_norm] = val

            # 向上补全：不覆盖本行已有键
            full = dict(prev_full)
            full.update({k: v for k, v in cur.items()})

            # 仅保留感兴趣的三键（并统一键名）
            full_canon: Dict[str, float] = {}
            for kk in _VEL_KEYS_CANON:
                if kk in full:
                    full_canon[kk] = full[kk]

            pos_list.append(line_start)
            snap_list.append(full_canon)

            # 更新 prev_full（用于下一条继承）
            prev_full = full

        self._vel_pos = pos_list
        self._vel_fullsnap = snap_list

    def _lookup_velocity_limits(self, *, anchor: int) -> Dict[str, float]:
        """在 _vel_pos 中就近向上（二分）查找 <= anchor 的最后一条，返回其补全快照。"""
        if not self._vel_pos:
            return {}
        lo, hi = 0, len(self._vel_pos) - 1
        ans = -1
        while lo <= hi:
            mid = (lo + hi) // 2
            if self._vel_pos[mid] <= anchor:
                ans = mid
                lo = mid + 1
            else:
                hi = mid - 1
        if ans < 0:
            return {}
        snap = self._vel_fullsnap[ans] or {}
        # 只返回三键，且键名为规范大写
        return {k: snap[k] for k in _VEL_KEYS_CANON if k in snap}

    # # ---------- 辅助：向下窥视“紧接着的 TYPE” ----------
    # @staticmethod
    # def _peek_next_type(mm: mmap.mmap, *, from_pos: int, layer_end: int) -> Optional[str]:
    #     """
    #     从 from_pos 向下扫描到 layer_end：
    #     - 跳过纯空行与非 TYPE 的注释行；
    #     - 若第一条遇到的是 ';TYPE:' 行，返回其规范化类型；
    #     - 若先遇到任何有指令体的行，则返回 None。
    #     """
    #     pos = from_pos
    #     while pos < layer_end:
    #         nl = mm.find(b"\n", pos, layer_end)
    #         line_end = nl if nl != -1 else layer_end
    #         raw = mm[pos:line_end]
    #
    #         stripped = raw.lstrip()
    #         if stripped.startswith(TYPE_PREFIX):
    #             tname = stripped[len(TYPE_PREFIX):].decode("utf-8", errors="ignore").strip()
    #             return GCodeParserEx._canon_type_name(tname)
    #
    #         body = pre_comment(raw)
    #         if body:
    #             return None
    #
    #         if nl == -1:
    #             break
    #         pos = nl + 1
    #     return None

    # ---------- 主入口：结构化轮廓 ----------
    def get_type_contours_per_layer(
            self,
            *,
            types: Optional[Sequence["ExtrusionType | str | bytes"]] = None,
            workers: int = 0,
            use_cache_when_all_types: bool = True,
            layer_indices: Optional[Sequence[int]] = None,
            start_layer: Optional[int] = None,
            end_layer: Optional[int] = None,
            layer_stride: int = 1,
            stride_offset: int = 0,
            skip_layers: Optional[Sequence[int]] = None,
            max_layers: Optional[int] = None,
    ) -> List[Layer]:
        no_layer_filter = (
                layer_indices is None and
                start_layer is None
                and end_layer is None
                and (layer_stride or 1) == 1
                and (stride_offset or 0) == 0
                and (not skip_layers)
                and (max_layers is None)
        )
        if types is None and use_cache_when_all_types and no_layer_filter and self._layers_cache_all is not None:
            return self._layers_cache_all

        whitelist: Optional[set[str]] = None if types is None else ExtrusionType.as_filter(types)
        if types is not None and not whitelist:
            return []

        layers: List[Layer] = []
        with self.path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            exe_beg, exe_end = self._find_pair(mm, EXEC_BEGIN, EXEC_END, 0)
            # —— 构建（或复用）全局 SET_VELOCITY_LIMIT 索引
            self._build_velocity_index(mm, exe_beg, exe_end)

            flat_layers = self._index_layers(mm, exe_beg, exe_end)
            L = len(flat_layers)

            def _build_selection() -> set[int]:
                sel: List[int]
                if layer_indices is not None:
                    sel = sorted({i for i in layer_indices if 0 <= i < L})
                else:
                    s0 = 0 if start_layer is None else max(0, start_layer)
                    e0 = (L - 1) if end_layer is None else min(L - 1, end_layer)
                    if e0 < s0:
                        return set()
                    step = max(1, int(layer_stride or 1))
                    off = int(stride_offset or 0)
                    sel = []
                    for i in range(s0, e0 + 1):
                        if ((i - s0 + off) % step) == 0:
                            sel.append(i)
                if skip_layers:
                    skip_set = {i for i in skip_layers if 0 <= i < L}
                    sel = [i for i in sel if i not in skip_set]
                if max_layers is not None and max_layers >= 0:
                    sel = sel[:max_layers]
                return set(sel)

            selected_layers: set[int] = _build_selection()

            for idx, (ls, le) in enumerate(flat_layers):
                z, h = self._parse_layer_meta(mm[ls:le])
                layers.append(Layer(index=idx, z=z, height=h))

            for i in range(L):
                if i > 0:
                    layers[i].prev = layers[i - 1]
                if i + 1 < L:
                    layers[i].next = layers[i + 1]

            for layer_idx, (ls, le) in enumerate(flat_layers):
                if (selected_layers) and (layer_idx not in selected_layers):
                    continue

                layer = layers[layer_idx]

                obj_map_raw = self._object_windows_in_layer(mm, ls, le)
                obj_map = self._with_global_segments(obj_map_raw, ls, le)

                type_windows, wipes = self._scan_extrusions_and_wipes(mm, ls, le)

                for (tname_raw, ts, te) in type_windows:
                    tname = self._canon_type_name(tname_raw)
                    if (whitelist is not None) and (tname not in whitelist):
                        continue

                    for oid, segs in obj_map.items():
                        paths_accum: List[ExtrusionPath] = []
                        region_feedrate: Optional[float] = None
                        region_limits: Optional[Dict[str, float]] = None

                        for (ss, se) in segs:
                            inter = self._interval_intersect((ts, te), (ss, se))
                            if not inter:
                                continue
                            bs, be = inter
                            pieces = self._interval_subtract((bs, be), wipes)
                            if not pieces:
                                continue

                            # —— 仅在首次命中该 (oid, type) 的有效片段时赋值：速度限制
                            if region_limits is None:
                                # 以 ;TYPE: 的位置作为“就近向上”的锚点
                                region_limits = self._lookup_velocity_limits(anchor=ts)

                            if region_feedrate is None:
                                region_feedrate_raw = self._feedrate_resolver.resolve_region_feedrate(
                                    mm,
                                    layer_start=ls, layer_end=le,
                                    type_start=ts, type_end=te,
                                    obj_seg_start=ss, obj_seg_end=se
                                )
                                region_feedrate = self._mm_per_min_to_mm_per_s(region_feedrate_raw)

                            # 使用新的“首锚点”查找：返回 Point（可能是 extrude 或 toolchange）
                            anchor_pt: Optional[Point] = self._find_upward_contour_anchor(mm, ss, bs)

                            current: Optional[ExtrusionPath] = None
                            pending_anchor: Optional[Tuple[float, float]] = None  # 片内 travel 的临时 XY
                            last_xy: Optional[Tuple[float, float]] = (
                                (anchor_pt.x, anchor_pt.y) if anchor_pt is not None else None
                            )
                            current_feed: Optional[float] = region_feedrate

                            def ensure_current():
                                nonlocal current, pending_anchor, current_feed
                                if current is not None:
                                    return
                                current = ExtrusionPath([])

                                # 1) 片内 pending_anchor 优先（始终作为“toolchange”起点）
                                if pending_anchor is not None:
                                    current.add(Point(
                                        pending_anchor[0], pending_anchor[1], "toolchange",
                                        has_z=False, has_f=(current_feed is not None), has_e=False,
                                        offset=None, e=None, f=current_feed, feedrate=region_feedrate
                                    ))
                                    pending_anchor = None
                                    return

                                # 2) 没有片内 pending_anchor，则落到“块外锚点 anchor_pt”
                                if anchor_pt is not None:
                                    if anchor_pt.kind == "extrude":
                                        # 若锚点来自挤出行：首点即为挤出点（避免插入虚拟 toolchange）
                                        current.add(Point(
                                            anchor_pt.x, anchor_pt.y, "extrude",
                                            has_z=False,
                                            has_f=(current_feed is not None) or anchor_pt.has_f,
                                            has_e=True,
                                            offset=anchor_pt.offset,
                                            e=anchor_pt.e,
                                            f=current_feed,                  # 点级 F
                                            feedrate=region_feedrate,        # 区域级
                                            arc_direction=anchor_pt.arc_direction,
                                            arc_center_offset=anchor_pt.arc_center_offset,
                                            arc_center=anchor_pt.arc_center,
                                            arc_radius=anchor_pt.arc_radius,
                                            arc_radius_deviation=anchor_pt.arc_radius_deviation,
                                        ))
                                    else:
                                        # 否则仍按“toolchange”处理
                                        current.add(Point(
                                            anchor_pt.x, anchor_pt.y, "toolchange",
                                            has_z=False, has_f=(current_feed is not None), has_e=False,
                                            offset=None, e=None, f=current_feed, feedrate=region_feedrate
                                        ))
                                # 若两种锚点都没有，就不写任何起点（保持原行为）

                            for (ps, pe) in pieces:
                                pos = ps
                                while pos < pe:
                                    nl = mm.find(b"\n", pos, pe)
                                    line_end = nl if nl != -1 else pe
                                    raw = mm[pos:line_end]
                                    body = pre_comment(raw)
                                    offset = pos

                                    if body:
                                        mode = arc_mode(body)
                                        is_move = bool(is_g1(body) or mode is not None)
                                        if has_f(body):
                                            fv = parse_f(body)
                                            if fv is not None:
                                                current_feed = self._mm_per_min_to_mm_per_s(fv)

                                        if is_move and (has_x(body) or has_y(body)):
                                            xy = parse_xy_loose(body, last_xy)
                                            if xy is not None:
                                                has_e_flag = has_e(body)
                                                e_val = parse_e(body) if has_e_flag else None
                                                hz = has_z(body)
                                                hf = (current_feed is not None)

                                                if has_e_flag and e_val is not None:
                                                    # extrude（包含 E>0 或 E<0? 这里只构建轮廓，保持与原逻辑一致：仅 E>0 作为挤出）
                                                    if e_val > 0:
                                                        ensure_current()
                                                        am = build_arc_meta(body, last_xy, xy)
                                                        current.add(Point(
                                                            xy[0], xy[1], "extrude",
                                                            has_z=hz, has_f=hf, has_e=True,
                                                            offset=offset, e=e_val,
                                                            f=current_feed,                # 点级 F（mm/s）
                                                            feedrate=region_feedrate,      # 区域级速度（mm/s）
                                                            arc_direction=am.direction,
                                                            arc_center_offset=am.center_offset,
                                                            arc_center=am.center,
                                                            arc_radius=am.radius,
                                                            arc_radius_deviation=am.radius_deviation,
                                                        ))
                                                        pending_anchor = None
                                                    else:
                                                        # E<=0（如擦拭）不进入轮廓；关闭当前路径，把位置作为下一段的候选起点
                                                        if current is not None and len(current) > 0:
                                                            paths_accum.append(current)
                                                        current = None
                                                        pending_anchor = xy
                                                else:
                                                    # travel：关闭当前路径，把位置作为下一段的候选起点
                                                    if current is not None and len(current) > 0:
                                                        paths_accum.append(current)
                                                    current = None
                                                    pending_anchor = xy
                                                last_xy = xy
                                    pos = (line_end + 1) if nl != -1 else pe

                            if current is not None and len(current) > 0:
                                paths_accum.append(current)

                        if paths_accum:
                            reg = layer.ensure_region(oid, tname)
                            reg.paths.extend(paths_accum)
                            reg.feedrate = region_feedrate
                            reg.velocity_limits = region_limits or {}

        if types is None and use_cache_when_all_types and no_layer_filter:
            self._layers_cache_all = layers
        return layers

    # ---------- 层级“运动路径”，返回 Point3D ----------
    def get_motion_paths_for_layer(
            self,
            layer_index: int
    ) -> List[Point3D]:
        mp = self.get_motion_paths(
            layer_indices=[layer_index]
        )
        return mp.get(layer_index)

    def get_motion_paths(
            self,
            *,
            layer_indices: Optional[Sequence[int]] = None,
            start_layer: Optional[int] = None,
            end_layer: Optional[int] = None,
            layer_stride: int = 1,
            stride_offset: int = 0,
            skip_layers: Optional[Sequence[int]] = None,
            max_layers: Optional[int] = None,
    ) -> Dict[int, List[Point3D]]:
        """按规则输出每层“线性时间序列”的运动点列表（Point3D）。
        规则由 _classify_kind_v3 提供：
          - 仅 G1/G2/G3 参与分类；
          - extrude 只能有 X 或 Y（至少一个），不能有 Z；
          - wipe 需要同时有 X 与 Y，且不能有 Z；
          - retract/unretract 不能包含任何坐标（只允许 E+F）；
          - travel 为无 E 且任一坐标有变化；
          - fanchange 为无 E、无坐标、仅 F。
        额外行为：
          - F 统一转换为 mm/s 存入 Point3D.f；
          - ;TYPE: 出现时，立即把“上一运动点”的 extrusion_type 改为新类型。
        新增行为：
          - 动态跟踪 SET_VELOCITY_LIMIT 行：形如
              "SET_VELOCITY_LIMIT ACCEL=3000 ACCEL_TO_DECEL=3000 SQUARE_CORNER_VELOCITY=6"
            该行出现后，更新“当前继承的三键快照”（可缺省部分键），影响之后的所有点，
            直到下一条 SET_VELOCITY_LIMIT 行覆盖为止。
          - 每个 Point3D.velocity_limits 都是当时的“快照”（浅拷贝 dict）。
        """

        def _build_selection(L: int) -> set[int]:
            if layer_indices is not None:
                sel = sorted({i for i in layer_indices if 0 <= i < L})
            else:
                s0 = 0 if start_layer is None else max(0, start_layer)
                e0 = (L - 1) if end_layer is None else min(L - 1, end_layer)
                if e0 < s0:
                    return set()
                step = max(1, int(layer_stride or 1))
                off = int(stride_offset or 0)
                sel = [i for i in range(s0, e0 + 1) if ((i - s0 + off) % step) == 0]
            if skip_layers:
                skip = {i for i in skip_layers if 0 <= i < L}
                sel = [i for i in sel if i not in skip]
            if max_layers is not None and max_layers >= 0:
                sel = sel[:max_layers]
            return set(sel)

        out: Dict[int, List[Point3D]] = {}

        with self.path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            beg, end = self._find_pair(mm, EXEC_BEGIN, EXEC_END, 0)

            # —— 构建（或复用）全局 SET_VELOCITY_LIMIT 索引；用于在每层开始时给“当前继承”做一个就近上游的初始化
            self._build_velocity_index(mm, beg, end)

            flat_layers = self._index_layers(mm, beg, end)
            L = len(flat_layers)
            if L == 0:
                return out

            selected = _build_selection(L)
            if not selected:
                return out

            for layer_idx in sorted(selected):
                ls, le = flat_layers[layer_idx]

                seq: List[Point3D] = []
                # 继承状态（按读入顺序更新）
                last_xy: Optional[Tuple[float, float]] = None
                last_z: Optional[float] = None
                last_f_ms: Optional[float] = None  # mm/s
                current_type: Optional[str] = None

                # —— 新增：速度限制继承（按行动态更新）
                # 先在层起点用“就近向上”的一条 SET_VELOCITY_LIMIT 进行初始化（如果存在）
                current_limits: Dict[str, float] = dict(self._lookup_velocity_limits(anchor=ls))

                pos = ls
                while pos < le:
                    nl = mm.find(b"\n", pos, le)
                    line_end = nl if nl != -1 else le
                    raw = mm[pos:line_end]
                    body = pre_comment(raw)
                    offset = pos

                    # 处理 ;TYPE: —— 立即将“上一点”的 extrusion_type 改为新类型
                    stripped = raw.lstrip()
                    if stripped.startswith(TYPE_PREFIX):
                        tname = stripped[len(TYPE_PREFIX):].decode("utf-8", errors="ignore").strip()
                        current_type = self._canon_type_name(tname)
                        if seq:
                            last = seq[-1]
                            seq[-1] = Point3D(
                                x=last.x, y=last.y, z=last.z,
                                f=last.f,
                                kind=last.kind,
                                extrusion_type=current_type,
                                e=last.e,
                                offset=last.offset,
                                feedrate=last.feedrate,
                                arc_direction=last.arc_direction,
                                arc_center_offset=last.arc_center_offset,
                                arc_center=last.arc_center,
                                arc_radius=last.arc_radius,
                                arc_radius_deviation=last.arc_radius_deviation,
                                velocity_limits=last.velocity_limits,  # 保持上一点的快照不变
                            )
                        pos = (line_end + 1) if nl != -1 else le
                        continue

                    if body:
                        # —— 先判定是否为 SET_VELOCITY_LIMIT 行：若是，更新“继承字典”，并继续读下一行
                        if _RX_SET_VEL.search(body):
                            # 抽取本行键值，**不清空**，而是在 current_limits 上“向上补全式覆盖”
                            # 允许行内缺省部分键，仅覆盖出现的键
                            for k_b, v_b in _RX_VEL_KV.findall(body):
                                k = k_b.decode("ascii", errors="ignore").upper()
                                if k not in _VEL_KEYS_CANON:
                                    continue
                                try:
                                    current_limits[k] = float(v_b.decode("ascii", errors="ignore"))
                                except Exception:
                                    pass
                            pos = (line_end + 1) if nl != -1 else le
                            continue

                        # 先解析本行的字段（注意：F/Z 的继承要按照出现顺序更新）
                        e_val = parse_e(body) if has_e(body) else None
                        f_val = parse_f(body) if has_f(body) else None
                        z_new = _parse_z(body) if has_z(body) else None

                        xy_new: Optional[Tuple[float, float]] = None
                        if has_x(body) or has_y(body):
                            xy_new = parse_xy_loose(body, last_xy)

                        # 更新继承源（F 需要转 mm/s）
                        if z_new is not None:
                            last_z = z_new
                        if f_val is not None:
                            last_f_ms = self._mm_per_min_to_mm_per_s(f_val)

                        # 仅对运动行进行分类
                        try:
                            kind = classify_kind(body)
                        except ValueError:
                            # 非运动或非法组合：忽略该行
                            pos = (line_end + 1) if nl != -1 else le
                            continue

                        # 根据 kind 产点
                        # —— 默认落点位置取“最新可得”的坐标；对仅 Z 变化的 travel，XY 继承 last_xy
                        cur_f = 0.0 if last_f_ms is None else last_f_ms
                        cur_z = 0.0 if last_z is None else last_z

                        # —— 为当前要产出的点制作一份“速度限制快照”
                        acc_snap: Dict[str, float] = dict(current_limits) if current_limits else {}

                        if kind == "extrude":
                            # extrude: 需要 XY 至少一个出现且不含 Z（由分类器保证）；若 parse_xy 失败则跳过
                            if xy_new is not None and e_val is not None and e_val > 0:
                                am = build_arc_meta(body, last_xy, xy_new)
                                seq.append(Point3D(
                                    x=xy_new[0], y=xy_new[1], z=cur_z,
                                    f=cur_f, kind="extrude", extrusion_type=current_type,
                                    e=e_val, offset=offset, feedrate=None,
                                    arc_direction=am.direction,
                                    arc_center_offset=am.center_offset,
                                    arc_center=am.center,
                                    arc_radius=am.radius,
                                    arc_radius_deviation=am.radius_deviation,
                                    velocity_limits=acc_snap,
                                ))
                                last_xy = xy_new  # 前进锚点
                        elif kind == "wipe":
                            # wipe: 需要同时有 X 与 Y，且不含 Z（由分类器保证）
                            if xy_new is not None and e_val is not None and e_val < 0:
                                am = build_arc_meta(body, last_xy, xy_new)
                                seq.append(Point3D(
                                    x=xy_new[0], y=xy_new[1], z=cur_z,
                                    f=cur_f, kind="wipe", extrusion_type=current_type,
                                    e=e_val, offset=offset, feedrate=None,
                                    arc_direction=am.direction,
                                    arc_center_offset=am.center_offset,
                                    arc_center=am.center,
                                    arc_radius=am.radius,
                                    arc_radius_deviation=am.radius_deviation,
                                    velocity_limits=acc_snap,
                                ))
                                last_xy = xy_new
                        elif kind == "retract":
                            # retract: 只允许 E<0 + F；不得包含坐标（分类器保证）
                            if e_val is not None and e_val < 0:
                                seq.append(Point3D(
                                    x=(last_xy[0] if last_xy else 0.0),
                                    y=(last_xy[1] if last_xy else 0.0),
                                    z=cur_z,
                                    f=cur_f, kind="retract", extrusion_type=current_type,
                                    e=e_val, offset=offset, feedrate=None,
                                    velocity_limits=acc_snap,
                                ))
                        elif kind == "unretract":
                            # unretract: 只允许 E>0 + F；不得包含坐标（分类器保证）
                            if e_val is not None and e_val > 0:
                                seq.append(Point3D(
                                    x=(last_xy[0] if last_xy else 0.0),
                                    y=(last_xy[1] if last_xy else 0.0),
                                    z=cur_z,
                                    f=cur_f, kind="unretract", extrusion_type=current_type,
                                    e=e_val, offset=offset, feedrate=None,
                                    velocity_limits=acc_snap,
                                ))
                        elif kind == "travel":
                            # travel: 无 E；任一坐标变化即可（包含仅 Z 变）
                            xy_for_travel = xy_new if xy_new is not None else last_xy
                            if (xy_for_travel is not None) or (last_z is not None):
                                am = (build_arc_meta(body, last_xy, xy_for_travel)
                                      if xy_for_travel is not None else ArcMeta.none())
                                seq.append(Point3D(
                                    x=(xy_for_travel[0] if xy_for_travel else (last_xy[0] if last_xy else 0.0)),
                                    y=(xy_for_travel[1] if xy_for_travel else (last_xy[1] if last_xy else 0.0)),
                                    z=cur_z,
                                    f=cur_f, kind="travel", extrusion_type=current_type,
                                    e=None, offset=offset, feedrate=None,
                                    arc_direction=am.direction if xy_for_travel is not None else None,
                                    arc_center_offset=am.center_offset if xy_for_travel is not None else None,
                                    arc_center=am.center if xy_for_travel is not None else None,
                                    arc_radius=am.radius if xy_for_travel is not None else None,
                                    arc_radius_deviation=am.radius_deviation if xy_for_travel is not None else None,
                                    velocity_limits=acc_snap,
                                ))
                                if xy_new is not None:
                                    last_xy = xy_new
                        elif kind == "fanchange":
                            # fanchange：仅 F；无坐标与 E
                            seq.append(Point3D(
                                x=(last_xy[0] if last_xy else 0.0),
                                y=(last_xy[1] if last_xy else 0.0),
                                z=cur_z,
                                f=cur_f, kind="fanchange", extrusion_type=current_type,
                                e=None, offset=offset, feedrate=None,
                                velocity_limits=acc_snap,
                            ))
                        # 其它情况（不应出现）直接忽略

                    pos = (line_end + 1) if nl != -1 else le

                if seq:
                    out[layer_idx] = seq

        return out

    # ---------- 旧结构导出 ----------
    @staticmethod
    def to_legacy_type_contours(layers: List[Layer]) -> List[Dict[int, Dict[str, List[List[Point]]]]]:
        out: List[Dict[int, Dict[str, List[List[Point]]]]] = []
        for layer in layers:
            lm: Dict[int, Dict[str, List[List[Point]]]] = {}
            for oid, tmap in layer.regions.items():
                tm: Dict[str, List[List[Point]]] = {}
                for tname, region in tmap.items():
                    tm[tname] = [p.as_points() for p in region.paths]
                lm[oid] = tm
            out.append(lm)
        return out

    # ---------- 仅在片段内含“有效挤出”时，才输出块 ----------
    @staticmethod
    def _piece_has_extrude(mm: mmap.mmap, ps: int, pe: int) -> bool:
        """片段 [ps, pe) 是否包含至少一条“有效挤出”：
           - 仅 G1/G2/G3 ；
           - E>0；
           - 含 X 或 Y（至少一个）；
           - 不含 Z。
        """
        pos = ps
        while pos < pe:
            nl = mm.find(b"\n", pos, pe)
            line_end = nl if nl != -1 else pe
            body = pre_comment(mm[pos:line_end])
            if body and (is_g1(body) or arc_mode(body) is not None):
                if has_e(body):
                    try:
                        e = parse_e(body)
                    except Exception:
                        e = None
                    if (e is not None) and (e > 0) and (has_x(body) or has_y(body)) and (not has_z(body)):
                        return True
            if nl == -1:
                break
            pos = nl + 1
        return False

    @classmethod
    def _filter_pieces_with_extrude(cls, mm: mmap.mmap, pieces: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        return [(ps, pe) for (ps, pe) in pieces if cls._piece_has_extrude(mm, ps, pe)]

    # ---------- 与旧能力等价的块级 API ----------
    def get_extrusions_blocks_per_layer(
            self,
            entities: Sequence["ExtrusionType | str | bytes"],
            *,
            include_wipe: bool = False,
            decode: bool = True,
    ) -> List[Dict[int, Dict[str, List[bytes | str]]]]:
        whitelist = ExtrusionType.as_filter(entities)
        if not whitelist:
            return []

        out_layers: List[Dict[int, Dict[str, List[bytes | str]]]] = []
        with self.path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            exe_beg, exe_end = self._find_pair(mm, EXEC_BEGIN, EXEC_END, 0)
            flat_layers = self._index_layers(mm, exe_beg, exe_end)

            for (ls, le) in flat_layers:
                layer_map: Dict[int, Dict[str, List[bytes | str]]] = {}
                obj_map: Dict[int, List[Tuple[int, int]]] = self._with_global_segments(
                    self._object_windows_in_layer(mm, ls, le), ls, le
                )
                type_windows, wipes = self._scan_extrusions_and_wipes(mm, ls, le)

                for (tname_raw, ts, te) in type_windows:
                    tname = self._canon_type_name(tname_raw)
                    if tname not in whitelist:
                        continue
                    for oid, segs in obj_map.items():
                        pieces_all: List[Tuple[int, int]] = []
                        for (ss, se) in segs:
                            inter = self._interval_intersect((ts, te), (ss, se))
                            if not inter:
                                continue
                            if include_wipe:
                                pieces_all.append(inter)
                            else:
                                pieces_all.extend(self._interval_subtract(inter, wipes))
                        if not pieces_all:
                            continue

                        # === 仅保留包含“有效挤出”的片段 ===
                        valid_pieces = pieces_all if include_wipe else self._filter_pieces_with_extrude(mm, pieces_all)
                        if not valid_pieces:
                            continue

                        if include_wipe:
                            for (ps, pe) in valid_pieces:
                                blob = mm[ps:pe]
                                layer_map.setdefault(oid, {}).setdefault(tname, []).append(
                                    blob.decode("utf-8", errors="ignore") if decode else blob
                                )
                        else:
                            if decode:
                                joined = "".join(
                                    mm[ps:pe].decode("utf-8", errors="ignore") for (ps, pe) in valid_pieces)
                            else:
                                joined = b"".join(mm[ps:pe] for (ps, pe) in valid_pieces)
                            layer_map.setdefault(oid, {}).setdefault(tname, []).append(joined)
                out_layers.append(layer_map)
        return out_layers

    def get_wipe_blocks_per_layer(
            self,
            *,
            decode: bool = False,
    ) -> List[Dict[int, List[bytes | str]]]:
        out_layers: List[Dict[int, List[bytes | str]]] = []
        with self.path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            exe_beg, exe_end = self._find_pair(mm, EXEC_BEGIN, EXEC_END, 0)
            flat_layers = self._index_layers(mm, exe_beg, exe_end)

            for (ls, le) in flat_layers:
                layer_map: Dict[int, List[bytes | str]] = {}
                obj_map = self._with_global_segments(self._object_windows_in_layer(mm, ls, le), ls, le)
                _, wipes = self._scan_extrusions_and_wipes(mm, ls, le)

                for (wb, we) in wipes:
                    for oid, segs in obj_map.items():
                        for (ss, se) in segs:
                            inter = self._interval_intersect((wb, we), (ss, se))
                            if not inter:
                                continue
                            ps, pe = inter
                            payload = mm[ps:pe]
                            layer_map.setdefault(oid, []).append(
                                payload.decode("utf-8", errors="ignore") if decode else payload
                            )
                out_layers.append(layer_map)
        return out_layers

    # ---------- 每层 (Z, HEIGHT) 提取 ----------
    def extract_layers(self, *, workers: int = 0) -> List[Tuple[Optional[float], Optional[float]]]:
        with self.path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            exe_beg, exe_end = self._find_pair(mm, EXEC_BEGIN, EXEC_END, 0)
            flat_layers = self._index_layers(mm, exe_beg, exe_end)
            if not flat_layers:
                return []

            if not workers or workers <= 1:
                return [self._parse_layer_meta(mm[s:e]) for (s, e) in flat_layers]

            from concurrent.futures import ThreadPoolExecutor
            blobs = [mm[s:e] for (s, e) in flat_layers]
            max_workers = max(2, min(32, int(workers)))
            out: List[Tuple[Optional[float], Optional[float]]] = []
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                for zh in ex.map(self._parse_layer_meta, blobs, chunksize=32):
                    out.append(zh)
            return out


if __name__ == '__main__':
    demo = Path(r"C:\Users\118388\Desktop\automation\test_m_v.gcode")
    p = GCodeParserEx(demo)

    # 示例：读取 CONFIG
    try:
        cfg = p.load_config()
        print("[CONFIG] keys:", list(cfg)[:8], " ... count:", len(cfg))
    except Exception as e:
        print("[CONFIG] load skipped:", e)

    # 示例：提取层 (Z, HEIGHT)
    try:
        zhs = p.extract_layers(workers=0)
        print(f"[LAYERS] count={len(zhs)} head={zhs[:3]}")
    except Exception as e:
        print("[LAYERS] extract skipped:", e)

    # 示例：运动路径（含 wipe），Point3D & extrusion_type
    try:
        mp = p.get_motion_paths(layer_indices=[0, 1])
        print(f"[MOTION] layers_in_map={len(mp)}  L0_polylines={len(mp.get(0, []))}")
        if mp.get(0):
            pt0 = mp.get(0)[0]
            print(" first point3d:", pt0)
    except Exception as e:
        print("[MOTION] parse skipped:", e)

    lidx = 50

    contours = p.get_type_contours_per_layer(types=[ExtrusionType.OUTER_WALL], layer_indices=[lidx])

    interested_contours = contours[lidx]

    layer_motion = p.get_motion_paths()

    blocks = p.get_extrusions_blocks_per_layer(entities=[ExtrusionType.INNER_WALL, ExtrusionType.OUTER_WALL])

    # 2) 验证：抽样打印前 5 层中，包含 velocity_limits 的 (oid, type) 区域
    layers = p.get_type_contours_per_layer(types=None)
    allowed_keys = {"ACCEL", "ACCEL_TO_DECEL", "SQUARE_CORNER_VELOCITY"}
    printed = 0
    print("\n[CHECK] Regions carrying global velocity limits (first 5 layers):")
    for layer in layers[:5]:
        for oid, tmap in layer.regions.items():
            for tname, region in tmap.items():
                if region.velocity_limits:
                    invalid = set(region.velocity_limits) - allowed_keys
                    assert not invalid, f"Unexpected keys in velocity_limits: {invalid}"
                    print(f"  - L{layer.index:03d}  oid={oid:<8}  type={tname:<18}  "
                          f"feedrate={region.feedrate if region.feedrate is not None else 'None'}  "
                          f"limits={region.velocity_limits}")
                    printed += 1

    if printed == 0:
        print("  (no regions with velocity_limits found in first 5 layers)")

    pass
