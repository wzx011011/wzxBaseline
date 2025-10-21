# gcode_parser_tokenized.py
from __future__ import annotations
import mmap
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict
from concurrent.futures import ThreadPoolExecutor

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


def _index_layers(mm: mmap.mmap, exe_beg: int, exe_end: int) -> List[Tuple[int, int]]:
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


def _parse_type_name_at(mm: mmap.mmap, type_pos: int, file_end: int) -> str:
    nl = mm.find(b"\n", type_pos, file_end)
    line = mm[type_pos:nl if nl > 0 else file_end]
    body = line[len(TYPE_PREFIX):]
    return body.decode("utf-8", errors="ignore").strip()


def _linear_pair_ranges(mm: mmap.mmap, start: int, end: int,
                        begin_tok: bytes, end_tok: bytes) -> List[Tuple[int, int]]:
    """
    线性配对：用 begin_tok/end_tok 生成 [begin, end) 区间。
    特殊一点的是解析wipe的时候：右边界扩展到 end_tok 所在行的换行符之后，确保不会残留 ';WIPE_END\\n'。
    """
    begins = _find_all(mm, begin_tok, start, end)
    ends   = _find_all(mm, end_tok,   start, end)
    out: List[Tuple[int, int]] = []
    ei = 0
    for bpos in begins:
        # 找到与 bpos 匹配的 end（未找到则兜底到层末）
        while ei < len(ends) and ends[ei] < bpos:
            ei += 1
        if ei < len(ends):
            epos = ends[ei]
            # 关键：把右边界扩展到该行的行尾（含 '\n'）
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

    # ---------- 层窗口 ----------
    def layer_windows(self) -> List[Tuple[int, int]]:
        with self.path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            exe_beg, exe_end = _find_pair(mm, EXEC_BEGIN, EXEC_END, 0)
            return _index_layers(mm, exe_beg, exe_end)

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
            mz = Z_RE.match(line)
            if mz:
                try:
                    z = float(mz.group(1))
                except ValueError:
                    pass
                continue
            mh = H_RE.match(line)
            if mh:
                try:
                    h = float(mh.group(1))
                except ValueError:
                    pass
        return z, h

    # ---------- 层内扫描 ----------
    @staticmethod
    def _scan_extrusions_and_wipes_in_layer(
            mm: mmap.mmap, layer_start: int, layer_end: int
    ) -> Tuple[List[ExtrusionEntity], List[Tuple[int, int]]]:
        type_positions = _find_all(mm, TYPE_PREFIX, layer_start, layer_end)
        extrusions: List[ExtrusionEntity] = []
        if type_positions:
            for idx, tpos in enumerate(type_positions):
                name = _parse_type_name_at(mm, tpos, layer_end)
                t_end = type_positions[idx + 1] if idx + 1 < len(type_positions) else layer_end
                extrusions.append(ExtrusionEntity(name=name, start=tpos, end=t_end, layer_index=-1))
        wipes = _linear_pair_ranges(mm, layer_start, layer_end, WIPE_BEGIN, WIPE_END)
        return extrusions, wipes

    # ---------- API 1：指定挤出类型（支持“整体拼接后返回”） ----------
    def get_extrusion_blocks_per_layer(
            self,
            entity_name: str,
            *,
            include_wipe: bool = False,
            decode: bool = False,
            workers: int = 0,
    ) -> List[List[bytes | str]]:
        """
        返回每层指定 `;TYPE:<entity_name>` 的数据块列表。
        - include_wipe=False：如果某个 TYPE 窗口被 WIPE 分割，会把非 WIPE 片段**拼回一个整体**（同一窗口→1个块）。
        - include_wipe=True ：保留原始 TYPE 窗口（包含 WIPE）。
        - decode=True      ：返回 str（UTF-8 ignore），否则 bytes。
        结果：List[ per_layer_blocks ]，每层是一个列表（该 TYPE 在该层可能出现多次 → 多个整体块）。
        """
        wins = self.layer_windows()
        if not wins:
            return []

        def _one(span: Tuple[int, int]) -> List[bytes | str]:
            s, e = span
            with self.path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                extrusions, wipes = self._scan_extrusions_and_wipes_in_layer(mm, s, e)

                # 目标 TYPE 的所有窗口
                targets = [ex for ex in extrusions if ex.name == entity_name]
                if not targets:
                    return []

                blocks: List[bytes | str] = []
                for ex in targets:
                    if include_wipe:
                        # 原样整窗
                        chunk = mm[ex.start:ex.end]
                        blocks.append(chunk.decode("utf-8", errors="ignore") if decode else chunk)
                    else:
                        # 裁掉 WIPE，并把非 WIPE 片段拼接成 **一个整体**
                        holes = [(wb, we) for (wb, we) in wipes if we > ex.start and wb < ex.end]
                        pieces = _interval_subtract((ex.start, ex.end), holes)  # 多段
                        if not pieces:
                            continue
                        if decode:
                            joined = "".join(mm[bs:be].decode("utf-8", errors="ignore") for (bs, be) in pieces)
                            blocks.append(joined)
                        else:
                            joined = b"".join(mm[bs:be] for (bs, be) in pieces)
                            blocks.append(joined)

                return blocks

        if workers and workers > 1:
            with ThreadPoolExecutor(max_workers=workers) as ex:
                return list(ex.map(_one, wins, chunksize=32))
        else:
            return [_one(w) for w in wins]

    # ---------- API 2：获取所有层的 WIPE 块（带所属 TYPE） ----------
    def get_wipe_blocks_per_layer(
            self,
            *,
            decode: bool = False,
            workers: int = 0,
    ) -> List[Dict[str, List[Technology]]]:
        """
        返回每层的工艺段（目前仅 'wipe'）：
        -> List[ { "wipe": [Technology, ...] } ]
        Technology.parent_extrusion 指向其所属的 ;TYPE: 名（若在任何 TYPE 前出现，则为 None）。
        """
        wins = self.layer_windows()
        if not wins:
            return []

        def _one_with_idx(args: Tuple[int, Tuple[int, int]]) -> Dict[str, List[Technology]]:
            layer_idx, (s, e) = args
            with self.path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                extrusions, wipes = self._scan_extrusions_and_wipes_in_layer(mm, s, e)
                techs: List[Technology] = []
                for (wb, we) in wipes:
                    parent_name: Optional[str] = None
                    for ex in extrusions:
                        if ex.start <= wb < ex.end:
                            parent_name = ex.name
                            break
                    payload: bytes | str
                    if decode:
                        payload = mm[wb:we].decode("utf-8", errors="ignore")
                    else:
                        payload = mm[wb:we]
                    techs.append(Technology(
                        kind="wipe", start=wb, end=we, layer_index=layer_idx,
                        parent_extrusion=parent_name, data=payload
                    ))
                return {"wipe": techs}

        args = list(enumerate(wins))
        if workers and workers > 1:
            with ThreadPoolExecutor(max_workers=workers) as ex:
                return list(ex.map(_one_with_idx, args, chunksize=32))
        else:
            return [_one_with_idx(a) for a in args]

    # ---------- API 3：获取所有层的层高 ----------
    def extract_layers(self, *, workers: int = 0) -> List[Tuple[Optional[float], Optional[float]]]:
        wins = self.layer_windows()
        if not wins: return []
        with self.path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            blobs = [mm[s:e] for (s, e) in wins]
        import os
        max_workers = workers if (workers and workers > 1) else (os.cpu_count() or 1)
        max_workers = min(32, max_workers + 2)
        out: List[Tuple[Optional[float], Optional[float]]] = []
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            for z_h in ex.map(self._parse_one_layer_blob, blobs, chunksize=32):
                out.append(z_h)
        return out


# ===================== 简单自检（可选） =====================
if __name__ == "__main__":
    demo_path = Path(r"C:\Users\118388\Desktop\automation\test.gcode")
    p = GCodeParser(demo_path)

    # 1) 不含 WIPE：会把同一 TYPE 窗口的非 WIPE 片段拼接成“一块”
    ow_nowipe = p.get_extrusion_blocks_per_layer("Inner wall", include_wipe=False, decode=True, workers=8)
    if ow_nowipe:
        print("L0 Outer wall blocks (no wipe):", len(ow_nowipe[0]))

    # 2) 含 WIPE：原样返回窗口
    ow_withwipe = p.get_extrusion_blocks_per_layer("Inner wall", include_wipe=True, decode=False, workers=8)
    if ow_withwipe:
        print("L0 Outer wall blocks (with wipe):", len(ow_withwipe[0]))

    # 3) 所有层的 WIPE（带所属 TYPE）
    wipes = p.get_wipe_blocks_per_layer(decode=True, workers=8)
    if wipes:
        print("L0 wipe count:", len(wipes[0]["wipe"]))

    # 4)
    layer_heights = p.extract_layers(workers=8)

    pass