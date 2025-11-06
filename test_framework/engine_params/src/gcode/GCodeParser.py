# gcode_parser_tokenized.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import math
import mmap
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Literal, Sequence, Any, Callable

from engine_params.src.gcode.constants import ExtrusionType
from concurrent.futures import ThreadPoolExecutor
import zlib

# ===================== 顶层 BLOCK 常量（字节级；大小写敏感） =====================
HEADER_BEGIN = b"; HEADER_BLOCK_START"
HEADER_END = b"; HEADER_BLOCK_END"
THUMBNAIL_BEGIN = b"; THUMBNAIL_BLOCK_START"
THUMBNAIL_END = b"; THUMBNAIL_BLOCK_END"
EXEC_BEGIN = b"; EXECUTABLE_BLOCK_START"
EXEC_END = b"; EXECUTABLE_BLOCK_END"
CONFIG_BEGIN = b"; CONFIG_BLOCK_START"
CONFIG_END = b"; CONFIG_BLOCK_END"

LAYER_MARK = b";LAYER_CHANGE"  # 每层起点（包含在层窗口内）
TYPE_PREFIX = b";TYPE:"
WIPE_BEGIN = b";WIPE_START"
WIPE_END = b";WIPE_END"

# ===================== EXCLUDE_OBJECT_START/END 行级正则 =====================
OBJ2_BEGIN_RE = re.compile(
    rb"^\s*;?\s*EXCLUDE_OBJECT_START\s+NAME=(?P<name>[^\r\n]+)\s*$",
    re.IGNORECASE
)
OBJ2_END_RE = re.compile(
    rb"^\s*;?\s*EXCLUDE_OBJECT_END\s+NAME=(?P<name>[^\r\n]+)\s*$",
    re.IGNORECASE
)

# 从 NAME=立方体_id_0_copy_0 中提取 id / copy（只强制使用 id；copy 视需要）
ID_FROM_NAME_RE_B = re.compile(rb"(?:^|[^A-Za-z0-9])id_(\d+)(?:[^A-Za-z0-9]|$)", re.IGNORECASE)
COPY_FROM_NAME_RE_B = re.compile(rb"(?:^|[^A-Za-z0-9_])copy_(\d+)(?:[^A-Za-z0-9_]|$)", re.IGNORECASE)

# ===================== CONFIG 行级正则 =====================
CFG_LINE_RE = re.compile(r"^\s*;\s*([^=]+?)\s*=\s*(.*?)\s*$")
Z_RE = re.compile(r"^\s*;Z\s*:\s*([+-]?\d+(?:\.\d+)?)\s*$")
H_RE = re.compile(r"^\s*;HEIGHT\s*:\s*([+-]?\d+(?:\.\d+)?)\s*$")

# ===================== 指令解析：仅看分号 ';' 之前的“指令体” =====================
_NUM_B = rb"([+-]?(?:\d+(?:\.\d*)?|\.\d+))"
_G1_RE_B = re.compile(rb"^\s*G1\b", re.IGNORECASE)
_G2_RE_B = re.compile(rb"^\s*G2\b", re.IGNORECASE)
_G3_RE_B = re.compile(rb"^\s*G3\b", re.IGNORECASE)
_X_RE_B = re.compile(rb"\bX" + _NUM_B + rb"\b", re.IGNORECASE)
_Y_RE_B = re.compile(rb"\bY" + _NUM_B + rb"\b", re.IGNORECASE)
_E_RE_B = re.compile(rb"\bE" + _NUM_B + rb"\b", re.IGNORECASE)
_Z_RE_B = re.compile(rb"\bZ" + _NUM_B + rb"\b", re.IGNORECASE)
_F_RE_B = re.compile(rb"\bF" + _NUM_B + rb"\b", re.IGNORECASE)
_I_RE_B = re.compile(rb"\bI" + _NUM_B + rb"\b", re.IGNORECASE)
_J_RE_B = re.compile(rb"\bJ" + _NUM_B + rb"\b", re.IGNORECASE)
_R_RE_B = re.compile(rb"\bR" + _NUM_B + rb"\b", re.IGNORECASE)


# ===================== 数据类 =====================

@dataclass(frozen=True)
class ExtrusionEntity:
    name: str
    start: int
    end: int
    layer_index: int


@dataclass(frozen=True)
class Technology:
    kind: str
    start: int
    end: int
    layer_index: int
    parent_extrusion: Optional[str]
    data: bytes | str | None = field(default=None)


@dataclass(frozen=True)
class Point:
    x: float
    y: float
    kind: Literal["extrude", "toolchange"]  # "extrude"=挤出点；"toolchange"=换刀点
    has_z: bool = False
    has_f: bool = False
    has_e: bool = False
    offset: Optional[int] = None  # 该点所在行（分号前指令体）的起始字节偏移，主要是轮廓点的第一个点是在其实字节前面
    e: Optional[float] = None  # 当前行解析得到的 G1 E 值（绝对或相对，依据 G-code 模式）
    arc_direction: Optional[Literal["cw", "ccw"]] = None
    arc_center_offset: Optional[Tuple[float, float]] = None
    arc_center: Optional[Tuple[float, float]] = None
    arc_radius: Optional[float] = None
    arc_radius_deviation: Optional[float] = None


# ===================== 工具 =====================

def _norm_key(k: str) -> str:
    import re as _re
    return _re.sub(r"\s+", "_", k.strip().lower())


def _parse_value(raw: str):
    s = raw.strip()
    if s.lower() in ("true", "false"):
        return s.lower() == "true"
    for caster in (int, float):
        try:
            return caster(s)
        except ValueError:
            pass
    return s


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


def find_all(mm: mmap.mmap, token: bytes | str, start: int, end: int) -> List[int]:
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


def _index_layers_flat(mm: mmap.mmap, exe_beg: int, exe_end: int) -> List[Tuple[int, int]]:
    """原版层窗口（不按物体切分），供层高等与物体无关的逻辑调用。"""
    layers: List[Tuple[int, int]] = []
    pos = exe_beg
    while True:
        i = mm.find(LAYER_MARK, pos, exe_end)
        if i < 0:
            break
        j = mm.find(LAYER_MARK, i + len(LAYER_MARK), exe_end)
        end = j if j >= 0 else exe_end
        layers.append((i, end))
        if j < 0:
            break
        pos = j
    return layers


def parse_type_name_at(mm: mmap.mmap, type_pos: int, file_end: int) -> str:
    nl = mm.find(b"\n", type_pos, file_end)
    line = mm[type_pos:nl if nl > 0 else file_end]
    body = line[len(TYPE_PREFIX):]
    return body.decode("utf-8", errors="ignore").strip()


def _linear_pair_ranges(mm: mmap.mmap, start: int, end: int,
                        begin_tok: bytes, end_tok: bytes) -> List[Tuple[int, int]]:
    """
    线性配对：用 begin_tok/end_tok 生成 [begin, end) 区间。
    解析 WIPE 时右边界扩展到 end_tok 行尾（含 '\n'）。
    """
    begins = find_all(mm, begin_tok, start, end)
    ends = find_all(mm, end_tok, start, end)
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


def _interval_subtract(base: Tuple[int, int], holes: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    s, e = base
    if not holes:
        return [(s, e)] if e > s else []
    holes = [(max(s, h0), min(e, h1)) for (h0, h1) in holes if min(e, h1) > max(s, h0)]
    if not holes:
        return [(s, e)] if e > s else []
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


def _oid_from_name_bytes(name_b: bytes) -> int:
    """
    从 NAME=... 中提取 id_数字；若不存在，则用 crc32(name_b) 生成稳定伪ID。
    """
    m = ID_FROM_NAME_RE_B.search(name_b)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            pass
    # 兜底：稳定伪ID，避免不同 NAME 混淆
    return zlib.crc32(name_b) & 0x7FFFFFFF


def _interval_intersect(a: Tuple[int, int], b: Tuple[int, int]) -> Optional[Tuple[int, int]]:
    s = max(a[0], b[0])
    e = min(a[1], b[1])
    return (s, e) if e > s else None


# =============== 层内：按物体分段（依据 printing/stop printing object 标记） ===============

def _object_windows_in_layer(mm: mmap.mmap, layer_start: int, layer_end: int) -> Dict[int, List[Tuple[int, int]]]:
    """
    扫描 [layer_start, layer_end) 的逐层打印物体段。
    支持两种标记：
      1) 新：EXCLUDE_OBJECT_START NAME=... / EXCLUDE_OBJECT_END NAME=...
      2) 旧：; printing object ... id:<d> copy <d> / ; stop printing object ...
    返回 {object_id: [(seg_start, seg_end), ...]}，区段内容不含标记行本身。
    """
    out: Dict[int, List[Tuple[int, int]]] = {}
    pos = layer_start
    cur_obj: Optional[int] = None
    cur_seg_start: Optional[int] = None

    while pos < layer_end:
        nl = mm.find(b"\n", pos, layer_end)
        if nl < 0:
            line_end = layer_end
        else:
            line_end = nl  # 不含 '\n'
        line = mm[pos:line_end]

        # --- 优先匹配新规则 ---
        m2_begin = OBJ2_BEGIN_RE.match(line)
        m2_end = OBJ2_END_RE.match(line)

        if m2_begin or m2_end:
            if m2_begin:
                # 关闭之前未闭合的段（兜底）
                if cur_obj is not None and cur_seg_start is not None and cur_seg_start < pos:
                    out.setdefault(cur_obj, []).append((cur_seg_start, pos))
                name_b = m2_begin.group("name")
                oid = _oid_from_name_bytes(name_b)
                cur_obj = oid
                cur_seg_start = line_end + 1 if nl != -1 else layer_end
            else:
                # END
                name_b = m2_end.group("name")
                oid = _oid_from_name_bytes(name_b)
                if cur_obj == oid and cur_seg_start is not None and cur_seg_start < pos:
                    out.setdefault(oid, []).append((cur_seg_start, pos))
                cur_obj = None
                cur_seg_start = None

        if nl == -1:
            break
        pos = nl + 1

    # 收尾：若某对象仍未闭合，延伸到层末
    if cur_obj is not None and cur_seg_start is not None and cur_seg_start < layer_end:
        out.setdefault(cur_obj, []).append((cur_seg_start, layer_end))

    return out


# ===================== 主解析器类 =====================

class GCodeParser:
    def __init__(self, gcode_path: str | Path):
        self.path = Path(gcode_path)
        self._cfg: Optional[Dict[str, object]] = None

    # ---------- 顶层块 ----------
    def block_range(self, kind: str) -> Tuple[int, int]:
        mapping = {
            "header": (HEADER_BEGIN, HEADER_END),
            "thumbnail": (THUMBNAIL_BEGIN, THUMBNAIL_END),
            "executable": (EXEC_BEGIN, EXEC_END),
            "config": (CONFIG_BEGIN, CONFIG_END),
        }
        if kind not in mapping:
            raise ValueError(f"unknown block kind: {kind}")
        with self.path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            return _find_pair(mm, *mapping[kind])

    # ---------- 层窗口（按物体切分） ----------
    def layer_windows(self) -> List[Dict[int, List[Tuple[int, int]]]]:
        """
        返回：List[ per_layer_dict ]，
        per_layer_dict: { object_id: [ (start, end), ... ] }
        如果某层没有任何物体标记，返回 {}（调用方可选择把该层视为“未标注物体”的一整段）。
        """
        with self.path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            exe_beg, exe_end = _find_pair(mm, EXEC_BEGIN, EXEC_END, 0)
            flat_layers = _index_layers_flat(mm, exe_beg, exe_end)
            out: List[Dict[int, List[Tuple[int, int]]]] = []
            for (s, e) in flat_layers:
                obj_map = _object_windows_in_layer(mm, s, e)
                out.append(obj_map)
            return out

    # 兼容用途：原始整层窗口（仅供内部：提取层高等）
    def _layer_windows_flat(self) -> List[Tuple[int, int]]:
        with self.path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            exe_beg, exe_end = _find_pair(mm, EXEC_BEGIN, EXEC_END, 0)
            return _index_layers_flat(mm, exe_beg, exe_end)

    # ---------- CONFIG ----------
    def load_config(self) -> Dict[str, object | float]:
        if self._cfg is not None:
            return self._cfg
        with self.path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            beg, end = _find_pair(mm, CONFIG_BEGIN, CONFIG_END, 0)
            text = mm[beg:end].decode("utf-8", errors="ignore")
        cfg: Dict[str, object] = {}
        for line in text.splitlines():
            m = CFG_LINE_RE.match(line)
            if not m:
                continue
            k, v = m.group(1), m.group(2)
            cfg[_norm_key(k)] = _parse_value(v)
        self._cfg = cfg
        return cfg

    # ---------- (Z, HEIGHT) ----------
    @staticmethod
    def _parse_one_layer_blob(blob: bytes) -> Tuple[Optional[float], Optional[float]]:
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

    # ---------- 层内扫描（不按物体） ----------
    @staticmethod
    def _scan_extrusions_and_wipes_in_layer(
            mm: mmap.mmap, layer_start: int, layer_end: int
    ) -> Tuple[List[ExtrusionEntity], List[Tuple[int, int]]]:
        type_positions = find_all(mm, TYPE_PREFIX, layer_start, layer_end)
        extrusions: List[ExtrusionEntity] = []
        if type_positions:
            for idx, tpos in enumerate(type_positions):
                name = parse_type_name_at(mm, tpos, layer_end)
                t_end = type_positions[idx + 1] if idx + 1 < len(type_positions) else layer_end
                extrusions.append(ExtrusionEntity(name=name, start=tpos, end=t_end, layer_index=-1))
        wipes = _linear_pair_ranges(mm, layer_start, layer_end, WIPE_BEGIN, WIPE_END)
        return extrusions, wipes

    # ---------- API 1：指定挤出类型，按层/物体返回 ----------
    def get_extrusion_blocks_per_layer(
            self,
            entity_name: ExtrusionType | str,
            *,
            include_wipe: bool = False,
            decode: bool = False,
            workers: int = 0,
    ) -> List[Dict[int, List[bytes | str]]]:
        """
        返回：List[ per_layer_map ]，
          per_layer_map: { object_id: [block, block, ...] }
        - include_wipe=False：裁掉 WIPE，并把同一 TYPE 窗口内被 WIPE 切开的多段**拼接成一个整体**再纳入相应物体。
        - include_wipe=True ：保留 TYPE 原始窗口（与物体段相交的那部分按相交关系切分，但**不**再去掉 WIPE）。
        - 若某层没有物体标记，则该层返回空 dict（你可选择把整层视为“未标注物体”再后处理）。
        """
        flat_wins = self._layer_windows_flat()
        # 预先展开每层的原始字节窗口，后续逐个任务分发
        if not flat_wins:
            return []

        def _one(args: Tuple[int, Tuple[int, int]]) -> Dict[int, List[bytes | str]]:
            layer_idx, (s, e) = args
            with self.path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                # 先拿到本层的物体窗口
                obj_map = _object_windows_in_layer(mm, s, e)  # {oid: [(os, oe), ...]}
                if not obj_map:
                    return {}  # 本层没有物体标记

                # 再拿到 TYPE / WIPE（基于整层）
                extrusions, wipes = self._scan_extrusions_and_wipes_in_layer(mm, s, e)

                # 目标 TYPE
                target_name = entity_name.value if isinstance(entity_name, ExtrusionType) else entity_name
                targets = [ex for ex in extrusions if ex.name == target_name]
                if not targets:
                    return {}

                out_layer: Dict[int, List[bytes | str]] = {}

                for ex in targets:
                    ex_span = (ex.start, ex.end)
                    # 对每个物体窗口求交集
                    for oid, segs in obj_map.items():
                        # 与该物体所有段求相交，得到该 TYPE 在此物体上的若干片段
                        intersected: List[Tuple[int, int]] = []
                        for seg in segs:
                            inter = _interval_intersect(ex_span, seg)
                            if inter:
                                intersected.append(inter)
                        if not intersected:
                            continue

                        if include_wipe:
                            # 直接从交集片段取数据并累积（可能多个片段 → 多个 block）
                            for (bs, be) in intersected:
                                chunk = mm[bs:be]
                                out_layer.setdefault(oid, []).append(
                                    chunk.decode("utf-8", errors="ignore") if decode else chunk
                                )
                        else:
                            # 从交集片段里“剪掉” WIPE，然后把多段拼接为一个整体 block
                            holes = [(wb, we) for (wb, we) in wipes]
                            # 先对每个交集片段做 subtract，再拼接
                            pieces_all: List[Tuple[int, int]] = []
                            for (bs, be) in intersected:
                                pieces_all.extend(_interval_subtract((bs, be), holes))
                            if not pieces_all:
                                continue
                            if decode:
                                joined = "".join(mm[ps:pe].decode("utf-8", errors="ignore") for (ps, pe) in pieces_all)
                                out_layer.setdefault(oid, []).append(joined)
                            else:
                                joined = b"".join(mm[ps:pe] for (ps, pe) in pieces_all)
                                out_layer.setdefault(oid, []).append(joined)

                return out_layer

        args = list(enumerate(flat_wins))
        if workers and workers > 1:
            with ThreadPoolExecutor(max_workers=workers) as ex:
                return list(ex.map(_one, args, chunksize=32))
        else:
            return [_one(a) for a in args]

    def get_extrusions_blocks_per_layer(
            self,
            entity_names: Sequence["ExtrusionType | str | bytes"],
            *,
            include_wipe: bool = False,
            decode: bool = False,
            workers: int = 0,
    ) -> List[Dict[int, Dict[str, List[bytes | str]]]]:
        """
        单次扫描多类型版（上面的get_extrusion_blocks_per_layer是老API，不动了）：
          返回 layers[L] -> { object_id: { type_name: [block, ...] } }

        说明
        - `entity_names` 支持 ExtrusionType/str/bytes，内部用 ExtrusionType.as_filter 归一化，
          自动处理大小写/空白/连字符与常见别名（如 'top skin' → 'Top surface'）。
        - include_wipe=False：对 (TYPE ∩ object) 的交集片段剪掉所有 WIPE，再把同一 TYPE
          在同一 object 的所有片段**拼接为单个 block** 后追加。
        - include_wipe=True ：不剪 WIPE；每个交集片段各自作为一个 block 追加。
        - decode=True 产出 str；否则产出 bytes。
        """
        # —— 归一化目标类型白名单
        type_whitelist: set[str] = ExtrusionType.as_filter(entity_names)  # 规范的 value 字符串集合
        if not type_whitelist:
            return []

        flat_wins = self._layer_windows_flat()
        if not flat_wins:
            return []

        def _one(args: tuple[int, tuple[int, int]]) -> Dict[int, Dict[str, List[bytes | str]]]:
            layer_idx, (s, e) = args
            out_layer: Dict[int, Dict[str, List[bytes | str]]] = {}
            with self.path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                # 该层的物体窗口
                obj_map = _object_windows_in_layer(mm, s, e)
                if not obj_map:
                    return out_layer

                # 该层的 TYPE 与 WIPE（全局到层）
                extrusions, wipes = self._scan_extrusions_and_wipes_in_layer(mm, s, e)

                # 仅保留关注的 TYPE
                ex_targets = [ex for ex in extrusions if ex.name in type_whitelist]
                if not ex_targets:
                    return out_layer

                for ex in ex_targets:
                    ex_span = (ex.start, ex.end)
                    tname = ex.name  # 使用 ;TYPE: 行里的原始 value（已由 whitelist 规范化对齐）

                    for oid, segs in obj_map.items():
                        # 与该 object 的窗口求交集
                        intersected: List[tuple[int, int]] = []
                        for seg in segs:
                            inter = _interval_intersect(ex_span, seg)
                            if inter:
                                intersected.append(inter)
                        if not intersected:
                            continue

                        if include_wipe:
                            # 直接按交集片段切块
                            for (bs, be) in intersected:
                                payload = mm[bs:be]
                                out_layer.setdefault(oid, {}).setdefault(tname, []).append(
                                    payload.decode("utf-8", errors="ignore") if decode else payload
                                )
                        else:
                            # 剪掉 WIPE，再把所有片段拼接为单个 block
                            holes = [(wb, we) for (wb, we) in wipes]
                            pieces_all: List[tuple[int, int]] = []
                            for (bs, be) in intersected:
                                pieces_all.extend(_interval_subtract((bs, be), holes))
                            if not pieces_all:
                                continue

                            if decode:
                                joined = "".join(mm[ps:pe].decode("utf-8", errors="ignore") for (ps, pe) in pieces_all)
                            else:
                                joined = b"".join(mm[ps:pe] for (ps, pe) in pieces_all)
                            out_layer.setdefault(oid, {}).setdefault(tname, []).append(joined)

            return out_layer

        args = list(enumerate(flat_wins))
        if workers and workers > 1:
            with ThreadPoolExecutor(max_workers=workers) as ex:
                return list(ex.map(_one, args, chunksize=32))
        else:
            return [_one(a) for a in args]

    def get_extrusions_blocks_by_object(
            self,
            entity_names: Sequence["ExtrusionType | str | bytes"],
            object_id: int,
            *,
            include_wipe: bool = False,
            decode: bool = False,
            workers: int = 0,
    ) -> List[Dict[str, List[bytes | str]]]:
        """
        多类型封装（按 object_id 提取，保持层序对齐）：
          返回：layers[L] -> { type_name: [block, ...] }，只包含指定 object_id。

        - entity_names: 支持 ExtrusionType/str/bytes，内部已由 get_extrusions_blocks_per_layer 使用
          ExtrusionType.as_filter 归一化（大小写/连字符/别名统一，忽略 MULTIPLE）。
        - include_wipe / decode / workers 语义与 per-layer 版本一致。
        """
        # 直接复用高效的“单次扫描多类型/逐层输出”实现
        per_layer = self.get_extrusions_blocks_per_layer(
            entity_names,
            include_wipe=include_wipe,
            decode=decode,
            workers=workers,
        )

        # 抽取指定 object_id；保持层对齐，每层给一个 dict（可能为空）
        out: List[Dict[str, List[bytes | str]]] = []
        for layer_map in per_layer:
            # layer_map: { oid: { type_name: [block, ...] } }
            type_map = layer_map.get(object_id, {})
            # 做一次浅拷贝，避免外部对返回列表的修改影响内部缓存
            out.append({t: list(blocks) for t, blocks in type_map.items()})
        return out

    # ---------- Helper：指定 TYPE，按 object_id 返回 List[List[bytes|str]]（外层=层；内层=该层的块） ----------
    def get_extrusion_blocks_by_object(
            self,
            entity_name: ExtrusionType | str,
            object_id: int,
            *,
            include_wipe: bool = False,
            decode: bool = False,
            workers: int = 0,
    ) -> List[List[bytes | str]]:
        """
        - 内部调用 get_extrusion_blocks_per_layer(entity_name, ...)
        - 再按 object_id 提取并保持层序对齐：
            返回 List[ per_layer_blocks ]，
            其中 per_layer_blocks 是该层该 object_id 的 [block, ...]（可能为空列表）。
        """
        per_layer = self.get_extrusion_blocks_per_layer(
            entity_name,
            include_wipe=include_wipe,
            decode=decode,
            workers=workers,
        )
        # 保持“每层一个列表”的对齐结构
        return [layer_map.get(object_id, []) for layer_map in per_layer]

    # ---------- API 2：按层/物体返回 WIPE 技术片段 ----------
    def get_wipe_blocks_per_layer(
            self,
            *,
            decode: bool = False,
            workers: int = 0,
    ) -> List[Dict[int, List[Technology]]]:
        """
        返回每层的 WIPE 片段，按“物体ID”组织：
          -> List[ { object_id: [Technology(kind='wipe', ...), ...], ... } ]
        细节：
          - 以“WIPE片段 与 物体窗口”的交集为准，必要时切分。
          - Technology.parent_extrusion 为交集起点所在处的 ;TYPE 名（若无则 None）。
        """
        flat_wins = self._layer_windows_flat()
        if not flat_wins:
            return []

        def _one(args: Tuple[int, Tuple[int, int]]) -> Dict[int, List[Technology]]:
            layer_idx, (s, e) = args
            with self.path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                obj_map = _object_windows_in_layer(mm, s, e)  # {oid: [(os, oe), ...]}
                if not obj_map:
                    return {}

                extrusions, wipes = self._scan_extrusions_and_wipes_in_layer(mm, s, e)

                # 为 parent_extrusion 查询做一个“包含查询”帮助
                def _parent_type_name_at(pos: int) -> Optional[str]:
                    # 找出 pos 所在的 TYPE 区间
                    for ex in extrusions:
                        if ex.start <= pos < ex.end:
                            return ex.name
                    return None

                out_map: Dict[int, List[Technology]] = {}

                for (wb, we) in wipes:
                    wipe_span = (wb, we)
                    # 与所有物体窗口求交集
                    for oid, segs in obj_map.items():
                        for seg in segs:
                            inter = _interval_intersect(wipe_span, seg)
                            if not inter:
                                continue
                            is_, ie_ = inter
                            parent = _parent_type_name_at(is_)
                            payload: bytes | str
                            if decode:
                                payload = mm[is_:ie_].decode("utf-8", errors="ignore")
                            else:
                                payload = mm[is_:ie_]
                            out_map.setdefault(oid, []).append(
                                Technology(
                                    kind="wipe",
                                    start=is_,
                                    end=ie_,
                                    layer_index=layer_idx,
                                    parent_extrusion=parent,
                                    data=payload
                                )
                            )
                return out_map

        args = list(enumerate(flat_wins))
        if workers and workers > 1:
            with ThreadPoolExecutor(max_workers=workers) as ex:
                return list(ex.map(_one, args, chunksize=32))
        else:
            return [_one(a) for a in args]

    # ---------- Helper：WIPE，按 object_id 返回 List[List[bytes|str]]（外层=层；内层=该层的 WIPE 块数据） ----------
    def get_wipe_blocks_by_object(
            self,
            object_id: int,
            *,
            decode: bool = False,
            workers: int = 0,
    ) -> List[List[bytes | str]]:
        """
        - 内部调用 get_wipe_blocks_per_layer(decode=..., workers=...)
        - 再按 object_id 提取每层的 WIPE 数据块列表（Technology.data），保持层序对齐。
        返回：List[ per_layer_wipes ]，其中 per_layer_wipes 是该层该 object_id 的 [bytes|str, ...]
        """
        per_layer = self.get_wipe_blocks_per_layer(decode=decode, workers=workers)
        out: List[List[bytes | str]] = []
        for layer_map in per_layer:
            techs = layer_map.get(object_id, [])
            # 取出 data 字段；此前 decode 决定了是 bytes 还是 str
            out.append([t.data for t in techs if t.data is not None])
        return out

    # ---------- API 3：获取所有层的层高（与物体无关） ----------
    def extract_layers(self, *, workers: int = 0) -> List[Tuple[Optional[float], Optional[float]]]:
        flat_wins = self._layer_windows_flat()
        if not flat_wins:
            return []
        with self.path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            blobs = [mm[s:e] for (s, e) in flat_wins]
        import os
        max_workers = workers if (workers and workers > 1) else (os.cpu_count() or 1)
        max_workers = min(32, max_workers + 2)
        out: List[Tuple[Optional[float], Optional[float]]] = []
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            for z_h in ex.map(self._parse_one_layer_blob, blobs, chunksize=32):
                out.append(z_h)
        return out

    # ---------- API 4：按printing object获取所有层的轮廓点 ----------
    @staticmethod
    def _pre_comment(line: bytes) -> bytes:
        """返回分号 ';' 之前的指令体（去掉 CR）。整行注释则返回空。"""
        line = line.rstrip(b"\r")
        i = line.find(b";")
        return line if i == -1 else line[:i]

    def _cmd_is_g1(self, body: bytes) -> bool:
        return bool(_G1_RE_B.match(body))

    def _has_xy(self, body: bytes) -> bool:
        return bool(_X_RE_B.search(body) and _Y_RE_B.search(body))

    def _has_e(self, body: bytes) -> bool:
        return bool(_E_RE_B.search(body))

    def _has_z(self, body: bytes) -> bool:
        return bool(_Z_RE_B.search(body))

    def _has_f(self, body: bytes) -> bool:
        return bool(_F_RE_B.search(body))

    def _parse_xy_from_body(self, body: bytes) -> Optional[Tuple[float, float]]:
        """仅在 body（分号前指令体）中解析 X/Y。失败返回 None。"""
        mX = _X_RE_B.search(body)
        if not mX:
            return None
        mY = _Y_RE_B.search(body)
        if not mY:
            return None
        try:
            x = float(mX.group(1).decode("ascii", errors="ignore"))
            y = float(mY.group(1).decode("ascii", errors="ignore"))
            return (x, y)
        except Exception:
            return None

    def _parse_e_from_body(self, body: bytes) -> Optional[float]:
        """解析 G1 行中的 E 值，若不存在则返回 None。"""
        mE = _E_RE_B.search(body)
        if not mE:
            return None
        try:
            return float(mE.group(1).decode("ascii", errors="ignore"))
        except Exception:
            return None

    def _arc_mode(self, body: bytes) -> Optional[Literal["cw", "ccw"]]:
        if _G2_RE_B.match(body):
            return "cw"
        if _G3_RE_B.match(body):
            return "ccw"
        return None

    def _parse_ij_from_body(self, body: bytes) -> Optional[Tuple[float, float]]:
        """解析 G2/G3 指令中的 I、J 偏移量，缺失任一项则返回 None。"""
        mI = _I_RE_B.search(body)
        mJ = _J_RE_B.search(body)
        if not (mI and mJ):
            return None
        try:
            i_val = float(mI.group(1).decode("ascii", errors="ignore"))
            j_val = float(mJ.group(1).decode("ascii", errors="ignore"))
            return (i_val, j_val)
        except Exception:
            return None

    def _parse_r_from_body(self, body: bytes) -> Optional[float]:
        """解析 G2/G3 指令中的 R 半径，若未指定则返回 None。"""
        mR = _R_RE_B.search(body)
        if not mR:
            return None
        try:
            return float(mR.group(1).decode("ascii", errors="ignore"))
        except Exception:
            return None

    def _build_arc_metadata(
            self,
            body: bytes,
            start_xy: Optional[Tuple[float, float]],
            end_xy: Tuple[float, float],
    ) -> Tuple[
        Optional[Literal["cw", "ccw"]], Optional[Tuple[float, float]], Optional[Tuple[float, float]], Optional[float],
        Optional[float]]:
        """组合圆弧相关元数据，无法计算时返回 None。"""
        direction = self._arc_mode(body)
        center_offset: Optional[Tuple[float, float]] = None
        center: Optional[Tuple[float, float]] = None
        radius: Optional[float] = None
        radius_dev: Optional[float] = None

        if direction is None:
            return direction, center_offset, center, radius, radius_dev
        if start_xy is None:
            return direction, center_offset, center, radius, radius_dev

        ij = self._parse_ij_from_body(body)
        if ij is not None:
            center_offset = ij
            cx = start_xy[0] + ij[0]
            cy = start_xy[1] + ij[1]
            center = (cx, cy)
            expected_radius = math.hypot(ij[0], ij[1])
            radius = math.hypot(end_xy[0] - cx, end_xy[1] - cy)
            radius_dev = radius - expected_radius
        else:
            r_val = self._parse_r_from_body(body)
            if r_val is not None:
                radius = abs(r_val)
                radius_dev = None

        return direction, center_offset, center, radius, radius_dev

    def _find_upward_start_toolchange(
            self, mm: mmap.mmap, seg_start: int, block_start: int
    ) -> Optional[Tuple[float, float]]:
        """
        在同一物体片段 [seg_start, block_start) 内，自下而上寻找最近的“换刀点”（G1 且含 X/Y 且不含 E）。
        返回 (x, y) 或 None。
        """
        if block_start <= seg_start:
            return None
        blob = mm[seg_start:block_start]
        pos = 0
        # 倒序扫描：逐行定位
        lines = blob.split(b"\n")
        for i in range(len(lines) - 1, -1, -1):
            raw = lines[i]
            body = self._pre_comment(raw)
            if not body:
                continue
            if self._cmd_is_g1(body) and self._has_xy(body) and (not self._has_e(body)):
                xy = self._parse_xy_from_body(body)
                if xy is not None:
                    return xy
        return None

    def get_type_contours_per_layer(
            self,
            *,
            types: Optional[Sequence["ExtrusionType | str | bytes"]] = None,
            workers: int = 0,
    ) -> List[Dict[int, Dict[str, List[List[Point]]]]]:
        """
        返回：layers[L] -> { object_id: { type_name: [ polyline(Point)[], ... ] } }

        点类型：
          - 挤出点("extrude"):   G1/G2/G3 带 X/Y/E
          - 换刀点("toolchange"):G1/G2/G3 带 X/Y但不带 E，可带/不带 F/Z
        逻辑
          - 若遇到换刀候选点：在可挤出的段内，同 object 范围，寻找最近的换刀点作为起点（如有）。
          - 遇到无挤出量的 G1/G2/G3 XY（旅行/换刀点）时：
              * 若当前已经在构建 polyline，则将当前 polyline 结束（point 列表追加到结果中）。
              * 记录该换刀点作为下一条 polyline 的候选（pending）。
          - 遇到带挤出量的点（G1/G2/G3 XYE）开始新的 polyline：
              * 优先取 pending 的换刀点（Point(kind='toolchange')），否则用“向上起点”（若存在）。
              * 然后把当前挤出点作为 Point(kind='extrude') 追加。
          - 在段末/片段末若还有未使用的最后一个换刀候选（pending）不输出。

        每个 Point 额外记录：
          - has_z / has_f：是否有 Z / F 字段
          - offset：该点所在“分号前指令体”的起始字节偏移
        """
        flat_wins = self._layer_windows_flat()
        if not flat_wins:
            return []

        # --- 白名单归一化（保持与其它 API 一致）
        # 如果传进来 None 之后，那么就默认抓取所有类型的挤出
        if types is None:
            type_whitelist: Optional[set[str]] = None
        else:
            type_whitelist = ExtrusionType.as_filter(types)  # -> set[str] 规范名集合
            if not type_whitelist:
                return []

        # --- 辅助：把 ;TYPE: 原始值归一化到规范名（若失败直接报错，因为不在标准的挤出类型之内）
        def _canon(name_raw: str) -> str:
            s = ExtrusionType.as_filter([name_raw])
            return next(iter(s)) if s else name_raw.strip()

        def _one(args: Tuple[int, Tuple[int, int]]) -> Dict[int, Dict[str, List[List[Point]]]]:
            layer_idx, (s, e) = args
            out_layer: Dict[int, Dict[str, List[List[Point]]]] = {}
            with self.path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                # 本层物体窗口
                obj_map = _object_windows_in_layer(mm, s, e)
                if not obj_map:
                    return out_layer

                # 本层 TYPE / WIPE
                extrusions, wipes = self._scan_extrusions_and_wipes_in_layer(mm, s, e)

                # 仅保留目标类型（先把 ;TYPE: 原始名转为规范名再过滤）
                ex_targets: List[Tuple[ExtrusionEntity, str]] = []
                for ex in extrusions:
                    tname_canon = _canon(ex.name)
                    if (type_whitelist is None) or (tname_canon in type_whitelist):
                        ex_targets.append((ex, tname_canon))
                if not ex_targets:
                    return out_layer

                for ex, tname_canon in ex_targets:
                    ex_span = (ex.start, ex.end)

                    for oid, segs in obj_map.items():
                        for (seg_s, seg_e) in segs:
                            inter = _interval_intersect(ex_span, (seg_s, seg_e))
                            if not inter:
                                continue
                            bs, be = inter

                            # 剪掉 WIPE 段，保留纯挤出片段
                            pieces = _interval_subtract((bs, be), wipes)
                            if not pieces:
                                continue

                            # 回溯寻找段起点上的换刀锚点
                            upward_tc = self._find_upward_start_toolchange(mm, seg_s, bs)

                            polylines: List[List[Point]] = []
                            current_poly: List[Point] | None = None
                            pending_start_xy: Optional[Tuple[float, float]] = None
                            last_xy: Optional[Tuple[float, float]] = upward_tc

                            def _ensure_polyline() -> None:
                                nonlocal current_poly, pending_start_xy
                                if current_poly is not None:
                                    return
                                current_poly = []
                                anchor = pending_start_xy if pending_start_xy is not None else upward_tc
                                if anchor is not None:
                                    current_poly.append(Point(
                                        anchor[0], anchor[1],
                                        "toolchange",
                                        has_z=False,
                                        has_f=False,
                                        has_e=False,
                                        offset=None,
                                        e=None,
                                    ))
                                pending_start_xy = None

                            for (ps, pe) in pieces:
                                pos = ps
                                while pos < pe:
                                    nl = mm.find(b"\n", pos, pe)
                                    line_end = nl if nl != -1 else pe
                                    raw = mm[pos:line_end]
                                    body = self._pre_comment(raw)
                                    offset = pos

                                    if body:
                                        arc_mode = self._arc_mode(body)
                                        is_move = bool(self._cmd_is_g1(body) or arc_mode is not None)
                                        has_xy = self._has_xy(body)
                                        if is_move and has_xy:
                                            xy = self._parse_xy_from_body(body)
                                            if xy is not None:
                                                has_e = self._has_e(body)
                                                e_val = self._parse_e_from_body(body) if has_e else None
                                                has_z = self._has_z(body)
                                                has_f = self._has_f(body)
                                                start_xy_for_arc = last_xy

                                                if has_e and e_val is not None:
                                                    _ensure_polyline()
                                                    arc_direction, arc_center_offset, arc_center, arc_radius, arc_radius_dev = self._build_arc_metadata(
                                                        body, start_xy_for_arc, xy
                                                    )
                                                    current_poly.append(Point(
                                                        xy[0], xy[1],
                                                        "extrude",
                                                        has_z=has_z,
                                                        has_f=has_f,
                                                        has_e=True,
                                                        offset=offset,
                                                        e=e_val,
                                                        arc_direction=arc_direction,
                                                        arc_center_offset=arc_center_offset,
                                                        arc_center=arc_center,
                                                        arc_radius=arc_radius,
                                                        arc_radius_deviation=arc_radius_dev,
                                                    ))
                                                    pending_start_xy = None
                                                else:
                                                    if current_poly is not None:
                                                        polylines.append(current_poly)
                                                        current_poly = None
                                                    pending_start_xy = xy

                                                last_xy = xy
                                    pos = (line_end + 1) if nl != -1 else pe

                            if current_poly is not None:
                                polylines.append(current_poly)
                                current_poly = None

                            if polylines:
                                out_layer.setdefault(oid, {}).setdefault(tname_canon, []).extend(polylines)

            return out_layer

        args = list(enumerate(flat_wins))
        if workers and workers > 1:
            with ThreadPoolExecutor(max_workers=workers) as ex:
                return list(ex.map(_one, args, chunksize=32))
        else:
            return [_one(a) for a in args]

    def get_type_contours_per_layer_by_object(
            self,
            object_id: int,
            *,
            types: Optional[Sequence["ExtrusionType | str | bytes"]] = None,
            workers: int = 0,
    ) -> List[Dict[str, List[List[Point]]]]:
        """
        轻量包装:
          输入: object_id
          输出: layers[L] -> { type_name: [ polyline(Point)[], ... ] }

        说明:
          - 直接调用原始 get_type_contours_per_layer，并从每层结果中选择指定 object_id。
          - 若某层该 object_id 没有数据，则该层返回 {}，保持层数对齐。
        """
        all_layers = self.get_type_contours_per_layer(types=types, workers=workers)
        if not all_layers:
            return []

        out: List[Dict[str, List[List[Point]]]] = []
        for layer_map in all_layers:
            obj_map = layer_map.get(object_id)  # Dict[str, List[List[Point]]] or None
            out.append(obj_map if obj_map is not None else {})
        return out

    @staticmethod
    def compare_type_contours(
            baseline_parser: "GCodeParser",
            test_parser: "GCodeParser",
            *,
            object_id: int = 0,
            types: Sequence["ExtrusionType | str | bytes"],
            tolerance: float = 1e-6,
            layer_filter: Optional[Callable[[int, int], bool]] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        通用轮廓对比助手：针对指定挤出类型，逐层比较基线与测试 G-code 的轮廓是否一致。

        逻辑概要:
          1. 通过 get_type_contours_per_layer_by_object 提取基线/测试中指定 object_id 的轮廓。
          2. 如果层数不同直接判定不匹配；
          3. 对于每一层的每种挤出类型，依次比较 polyline 数量以及 polyline 内的点坐标；
          4. 任意层出现缺失类型、polylines 数量不一致，或点坐标超 tolerance 即记录 mismatch。
          5. 返回总体 ok 结果与详细 mismatch 信息，便于上层测试输出定位。
           6. 可选 layer_filter 提供层筛选（如忽略首尾层）。
        """
        if not types:
            raise ValueError("compare_type_contours 需要至少一个挤出类型")

        def _canon(name: "ExtrusionType | str | bytes") -> str:
            if isinstance(name, ExtrusionType):
                return name.value
            resolved = ExtrusionType.to_str(name)
            return resolved if resolved is not None else str(name)

        type_names = [_canon(t) for t in types]

        baseline_layers = baseline_parser.get_type_contours_per_layer_by_object(
            object_id,
            types=type_names,
        ) or []
        test_layers = test_parser.get_type_contours_per_layer_by_object(
            object_id,
            types=type_names,
        ) or []

        # 记录层数与差异细节，便于定位
        details: Dict[str, Any] = {
            "types": type_names,
            "baseline_layer_count": len(baseline_layers),
            "test_layer_count": len(test_layers),
            "mismatch_layers": [],
            "errors": [],
        }

        ok = True

        # 层数不同直接失败
        if len(baseline_layers) != len(test_layers):
            ok = False
            details["errors"].append(
                f"Layer count mismatch: baseline={len(baseline_layers)}, test={len(test_layers)}"
            )

        layer_count = min(len(baseline_layers), len(test_layers))

        for layer_idx in range(layer_count):
            if layer_filter and not layer_filter(layer_idx, layer_count):
                continue

            baseline_layer = baseline_layers[layer_idx] or {}
            test_layer = test_layers[layer_idx] or {}

            for type_name in type_names:
                baseline_polys = baseline_layer.get(type_name, [])
                test_polys = test_layer.get(type_name, [])

                # 双方均无该类型，跳过
                if not baseline_polys and not test_polys:
                    continue

                if not baseline_polys and test_polys:
                    ok = False
                    details["mismatch_layers"].append({
                        "layer_index": layer_idx,
                        "type": type_name,
                        "reason": "baseline-missing-type",
                        "baseline_polylines": 0,
                        "test_polylines": len(test_polys),
                    })
                    continue

                if baseline_polys and not test_polys:
                    ok = False
                    details["mismatch_layers"].append({
                        "layer_index": layer_idx,
                        "type": type_name,
                        "reason": "test-missing-type",
                        "baseline_polylines": len(baseline_polys),
                        "test_polylines": 0,
                    })
                    continue

                if len(baseline_polys) != len(test_polys):
                    ok = False
                    details["mismatch_layers"].append({
                        "layer_index": layer_idx,
                        "type": type_name,
                        "reason": "polyline-count-mismatch",
                        "baseline_polylines": len(baseline_polys),
                        "test_polylines": len(test_polys),
                    })
                    continue

                for poly_idx, (base_poly, test_poly) in enumerate(zip(baseline_polys, test_polys)):
                    if len(base_poly) != len(test_poly):
                        ok = False
                        details["mismatch_layers"].append({
                            "layer_index": layer_idx,
                            "type": type_name,
                            "reason": "point-count-mismatch",
                            "polyline_index": poly_idx,
                            "baseline_points": len(base_poly),
                            "test_points": len(test_poly),
                        })
                        continue

                    for point_idx, (base_pt, test_pt) in enumerate(zip(base_poly, test_poly)):
                        if (
                                abs(base_pt.x - test_pt.x) > tolerance
                                or abs(base_pt.y - test_pt.y) > tolerance
                        ):
                            ok = False
                            details["mismatch_layers"].append({
                                "layer_index": layer_idx,
                                "type": type_name,
                                "reason": "point-coordinate-mismatch",
                                "polyline_index": poly_idx,
                                "point_index": point_idx,
                                "baseline_point": (base_pt.x, base_pt.y),
                                "test_point": (test_pt.x, test_pt.y),
                            })
                            break
                    else:
                        continue
                    break

        return ok, details


# ===================== 简单自检 =====================
if __name__ == "__main__":
    demo_path = Path(r"C:\Users\118388\Desktop\automation\lhx_test.gcode")
    p = GCodeParser(demo_path)

    # 1) 层→物体窗口统计
    layer_obj_windows = p.layer_windows()
    print(f"[LWIN] Total layers: {len(layer_obj_windows)}")
    if layer_obj_windows:
        print("[LWIN] L0 object ids:", list(layer_obj_windows[0].keys()))

    # 2) 指定 TYPE 的块（例如 Inner wall），按层/物体
    entity = ExtrusionType.TOP_SURFACE.value
    per_layer_ex = p.get_extrusion_blocks_per_layer(entity, include_wipe=False, decode=True, workers=8)
    if per_layer_ex:
        for layer_idx, layer_map in enumerate(per_layer_ex):
            if layer_map:
                some_oid = next(iter(layer_map.keys()))
                print(f"[EX-PL] L{layer_idx} oid={some_oid} '{entity}' blocks(no wipe):", len(layer_map[some_oid]))
                break
    print(f"[EX-PL] Layers returned: {len(per_layer_ex)}")

    # 3) 指定 object_id
    target_oid = 0
    ex_by_oid = p.get_extrusion_blocks_by_object(entity, target_oid, include_wipe=False, decode=True, workers=8)
    print(f"[EX-OID] '{entity}' object_id={target_oid} -> layers={len(ex_by_oid)}")
    if ex_by_oid:
        print(f"[EX-OID] L0 blocks count:", len(ex_by_oid[0]))

    # 4) WIPE 片段（按层/物体）
    per_layer_wipes = p.get_wipe_blocks_per_layer(decode=True, workers=8)
    if per_layer_wipes:
        first_layer = per_layer_wipes[0]
        if first_layer:
            some_oid2 = next(iter(first_layer.keys()))
            print(f"[WP-PL] L0 oid={some_oid2} wipe segments:", len(first_layer[some_oid2]))
    print(f"[WP-PL] Layers returned: {len(per_layer_wipes)}")

    # 5) 新增：WIPE（按 object_id，保持层对齐）
    wipes_by_oid = p.get_wipe_blocks_by_object(target_oid, decode=True, workers=8)
    print(f"[WP-OID] object_id={target_oid} -> layers={len(wipes_by_oid)}")
    if wipes_by_oid:
        print(f"[WP-OID] L0 wipe segments:", len(wipes_by_oid[0]))

    # 6) 填缝挤出字段（示例：Gap infill）
    entity2 = "Gap infill"
    gap_infill_by_oid = p.get_extrusion_blocks_by_object(entity2, target_oid, include_wipe=False, decode=True,
                                                         workers=8)
    print(f"[EX-OID] '{entity2}' object_id={target_oid} -> layers={len(gap_infill_by_oid)}")
    if gap_infill_by_oid:
        print(f"[EX-OID] L0 blocks count:", len(gap_infill_by_oid[0]))

    # 7) 轮廓点 API 验证（全 TYPE / 指定 TYPE）
    contours_all = p.get_type_contours_per_layer(workers=8)
    print(f"[CTRS] layers(contours_all): {len(contours_all)}")
    contours_ow_iw = p.get_type_contours_per_layer(
        types=[ExtrusionType.OUTER_WALL.value, ExtrusionType.INNER_WALL.value], workers=8)
    print(f"[CTRS] layers(contours_ow_iw): {len(contours_ow_iw)}")
    if contours_ow_iw and contours_ow_iw[0]:
        any_oid = next(iter(contours_ow_iw[0].keys()))
        types_on_oid0 = list(contours_ow_iw[0][any_oid].keys())
        print(f"[CTRS] L0 oid={any_oid} types:", types_on_oid0[:4])

    # 8) 层高
    layer_heights = p.extract_layers(workers=8)
    if layer_heights:
        print("[Z/H] L0 Z,H:", layer_heights[0])

    print("Self-check done.")

    # 9)
    entity3 = [ExtrusionType.SUPPORT]
    sparse_infill_contour = p.get_type_contours_per_layer(types=entity3)
    print(f"[EX-OID] '{entity3}' object_id={target_oid} -> layers={len(sparse_infill_contour)}")
    if sparse_infill_contour:
        print(f"[EX-OID] L0 blocks count:", len(sparse_infill_contour[0]))

    # 10)
    contour2 = p.get_type_contours_per_layer_by_object(0, types=entity3)

    p2 = GCodeParser(
        r"D:\C3DBaseline\test_framework\engine_params\output\mod_test_fill\test_sparse_infill_pattern_sparse_infill_pattern_lightning__1.gcode")

    slice_gcode_contour = p2.get_type_contours_per_layer_by_object(0, types=entity3)
    pass
