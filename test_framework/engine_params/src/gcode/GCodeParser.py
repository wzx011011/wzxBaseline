# gcode_parser_tokenized.py
from __future__ import annotations
import mmap
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Literal
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
    s = max(a[0], b[0]);
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
    def load_config(self) -> Dict[str, object]:
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
            entity_name: str,
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
                targets = [ex for ex in extrusions if ex.name == entity_name]
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

    # ---------- Helper：指定 TYPE，按 object_id 返回 List[List[bytes|str]]（外层=层；内层=该层的块） ----------
    def get_extrusion_blocks_by_object(
            self,
            entity_name: str,
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

    # ---------- 辅助：匹配 G1 带 X/Y 的行（起点查找）/ 带 X/Y/E 的行（块内点） ----------
    _NUM_B = rb"([+-]?(?:\d+(?:\.\d*)?|\.\d+))"
    _G1_XY_LINE_RE_B = re.compile(
        rb"^\s*G1\b(?=[^;]*\bX" + _NUM_B + rb"\b)(?=[^;]*\bY" + _NUM_B + rb"\b)[^;]*$",
        re.IGNORECASE
    )
    _G1_XYE_LINE_RE_B = re.compile(
        rb"^\s*G1\b(?=[^;]*\bX" + _NUM_B + rb"\b)(?=[^;]*\bY" + _NUM_B + rb"\b)(?=[^;]*\bE" + _NUM_B + rb"\b)[^;]*$",
        re.IGNORECASE
    )
    _X_RE_B = re.compile(rb"\bX" + _NUM_B + rb"\b", re.IGNORECASE)
    _Y_RE_B = re.compile(rb"\bY" + _NUM_B + rb"\b", re.IGNORECASE)

    def _parse_xy_from_line(self, line: bytes) -> Optional[Tuple[float, float]]:
        """从一行 bytes 中解析 X/Y，失败返回 None。"""
        mX = self._X_RE_B.search(line)
        if not mX:
            return None
        mY = self._Y_RE_B.search(line)
        if not mY:
            return None
        try:
            x = float(mX.group(1).decode('ascii', errors='ignore'))
            y = float(mY.group(1).decode('ascii', errors='ignore'))
            return (x, y)
        except Exception:
            return None

    def _find_upward_start_xy(self, mm: mmap.mmap, seg_start: int, block_start: int) -> Optional[Tuple[float, float]]:
        """
        在同一物体片段 [seg_start, block_start) 内，向上寻找最近的 G1 且同时带 X/Y 的行。
        找到则返回 (x, y)，否则 None。
        """
        if block_start <= seg_start:
            return None
        blob = mm[seg_start:block_start]
        # 逐行倒序查找（bytes）
        lines = blob.split(b"\n")
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].rstrip(b"\r")
            if self._G1_XY_LINE_RE_B.match(line):
                xy = self._parse_xy_from_line(line)
                if xy is not None:
                    return xy
        return None

    def get_type_contours_per_layer(
            self,
            *,
            types: Optional[List[str]] = None,
            workers: int = 0,
    ) -> List[Dict[int, Dict[str, List[List[Tuple[float, float]]]]]]:
        """
        layers[L] -> { object_id: { type_name: [ polyline_points_of_each_block, ... ] } }
        规则：
          - 起点：从块起点向上，在“同一 object 段”内找最近的 G1(含 X/Y) 行（无需 E）。
          - 块内点：仅采集 G1(含 X/Y/E) 的行。
          - 若块内没有任何带 E 的点，则该块跳过。
        types=None 表示收集所有 ;TYPE:，否则仅收集给定类型名集合（大小写敏感度与原始解析一致）。
        """
        flat_wins = self._layer_windows_flat()
        if not flat_wins:
            return []

        def _one(args: Tuple[int, Tuple[int, int]]) -> Dict[int, Dict[str, List[List[Tuple[float, float]]]]]:
            layer_idx, (s, e) = args
            out_layer: Dict[int, Dict[str, List[List[Tuple[float, float]]]]] = {}
            with self.path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                # 同层物体窗口（一个物体可能多段）
                obj_map = _object_windows_in_layer(mm, s, e)  # {oid: [(os, oe), ...]}
                if not obj_map:
                    return out_layer

                # 本层挤出类型窗口和 WIPE 片段（基于整层）
                extrusions, wipes = self._scan_extrusions_and_wipes_in_layer(mm, s, e)

                # 过滤类型
                ex_targets = [ex for ex in extrusions if (types is None or ex.name in types)]
                if not ex_targets:
                    return out_layer

                # 遍历每个 TYPE 窗口
                for ex in ex_targets:
                    ex_span = (ex.start, ex.end)

                    # 分配到每个物体：与其物体段求交集，再剪掉 WIPE，得到 piece 列表（按顺序）
                    for oid, segs in obj_map.items():
                        for (seg_s, seg_e) in segs:
                            inter = _interval_intersect(ex_span, (seg_s, seg_e))
                            if not inter:
                                continue
                            bs, be = inter

                            # 剪掉 WIPE（整层的 WIPE 已经扩展到了行尾，所以这里切分是对齐行的）
                            pieces = _interval_subtract((bs, be), wipes)
                            if not pieces:
                                continue

                            # 先查起点（在当前物体段内，向上找最近 G1 X/Y）
                            start_xy = self._find_upward_start_xy(mm, seg_s, bs)

                            # 再收集块内点（仅 E-挤出行），顺序遍历每个 piece 的每一行
                            poly: List[Tuple[float, float]] = []
                            if start_xy is not None:
                                poly.append(start_xy)

                            for (ps, pe) in pieces:
                                chunk = mm[ps:pe]
                                for raw in chunk.split(b"\n"):
                                    line = raw.rstrip(b"\r")
                                    if not line:
                                        continue
                                    if self._G1_XYE_LINE_RE_B.match(line):
                                        xy = self._parse_xy_from_line(line)
                                        if xy is not None:
                                            poly.append(xy)

                            # 如果块内没有任何带 E 的点，跳过（不满足“结束点在块内”的约束）
                            # 即便有起点，也不返回，以免产生空挤出折线
                            inblock_count = len(poly)
                            if start_xy is not None:
                                inblock_count -= 1
                            has_inblock_e_point = inblock_count >= 1
                            if not has_inblock_e_point:
                                continue

                            # 记入 out_layer
                            out_layer.setdefault(oid, {}).setdefault(ex.name, []).append(poly)

            return out_layer

            # END _one

        args = list(enumerate(flat_wins))
        if workers and workers > 1:
            with ThreadPoolExecutor(max_workers=workers) as ex:
                return list(ex.map(_one, args, chunksize=32))
        else:
            return [_one(a) for a in args]


# ===================== 简单自检 =====================
if __name__ == "__main__":
    demo_path = Path(r"C:\Users\118388\Desktop\for printing object\2.gcode")
    p = GCodeParser(demo_path)

    # 1) 层→物体窗口统计
    layer_obj_windows = p.layer_windows()
    print(f"[LWIN] Total layers: {len(layer_obj_windows)}")
    if layer_obj_windows:
        print("[LWIN] L0 object ids:", list(layer_obj_windows[0].keys()))

    # 2) 指定 TYPE 的块（例如 Inner wall），按层/物体
    entity = "Inner wall"
    per_layer_ex = p.get_extrusion_blocks_per_layer(entity, include_wipe=False, decode=True, workers=8)
    if per_layer_ex:
        first_layer = per_layer_ex[0]
        if first_layer:
            some_oid = next(iter(first_layer.keys()))
            print(f"[EX-PL] L0 oid={some_oid} '{entity}' blocks(no wipe):", len(first_layer[some_oid]))
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

    # 5) 新增：WIPE 一站式（按 object_id，保持层对齐）
    wipes_by_oid = p.get_wipe_blocks_by_object(target_oid, decode=True, workers=8)
    print(f"[WP-OID] object_id={target_oid} -> layers={len(wipes_by_oid)}")
    if wipes_by_oid:
        print(f"[WP-OID] L0 wipe segments:", len(wipes_by_oid[0]))

    # 6) 填缝挤出字段（示例：Gap infill），演示一站式
    entity2 = "Gap infill"
    gap_infill_by_oid = p.get_extrusion_blocks_by_object(entity2, target_oid, include_wipe=False, decode=True,
                                                         workers=8)
    print(f"[EX-OID] '{entity2}' object_id={target_oid} -> layers={len(gap_infill_by_oid)}")
    if gap_infill_by_oid:
        print(f"[EX-OID] L0 blocks count:", len(gap_infill_by_oid[0]))

    # 7) 轮廓点 API 验证（全 TYPE / 指定 TYPE）
    contours_all = p.get_type_contours_per_layer(workers=8)
    print(f"[CTRS] layers(contours_all): {len(contours_all)}")
    contours_ow_iw = p.get_type_contours_per_layer(types=["Outer wall", "Inner wall"], workers=8)
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

    pass
