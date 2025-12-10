from engine_params.src.gcode.GCodeParser import find_all, TYPE_PREFIX, parse_type_name_at, Point
from engine_params.src.gcode.constants import *
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
import math
import mmap
import re


# ================== wall_sequence ==================

def _pos_in_any_span(pos: int, spans: List[Tuple[int, int]]) -> bool:
    """判断字节偏移 pos 是否落在任意 [s,e) 片段内。"""
    for s, e in spans:
        if s <= pos < e:
            return True
    return False


def parse_wall_sequence(
        gcode_path: Path | str,
        expected_style: WallStyle,
) -> Tuple[bool, WallStyle, List[Tuple[int, WallStyle, List[str]]]]:
    """
    按“给定的期望风格 expected_style”校验所有非首层（layer>0）的墙顺序。
    规则：
      - 跳过首层 layer 0；
      - 若某层含 ';TYPE:Top surface'，整层跳过（不参与校验）；
      - 仅当某层恰好能提取到 3 次 Inner/Outer 时，才用三元顺序判定；
      - 与 expected_style 不同的层，加入 bad_layers。
    返回：
      ok:             是否所有参与校验的层都与 expected_style 一致
      expected_style: 原样回传
      bad_layers:     [(layer_idx, parsed_style, seq3)]
                      其中 seq3 是该层实际解析到的前三个墙标记（长度=3）
    """
    if expected_style not in (
        "inner wall/outer wall",
        "outer wall/inner wall",
        "inner-outer-inner wall",
        "unknown",
    ):
        raise ValueError(f"unexpected expected_style: {expected_style!r}")

    def judge_triplet(seq3: List[str]) -> WallStyle:
        if len(seq3) != 3:
            return "unknown"
        a, b, c = seq3
        if a == ExtrusionType.INNER_WALL.value and b == ExtrusionType.INNER_WALL.value and c == ExtrusionType.OUTER_WALL.value:
            return "inner wall/outer wall"
        if a == ExtrusionType.OUTER_WALL.value and b == ExtrusionType.INNER_WALL.value and c == ExtrusionType.INNER_WALL.value:
            return "outer wall/inner wall"
        if a == ExtrusionType.INNER_WALL.value and b == ExtrusionType.OUTER_WALL.value and c == ExtrusionType.INNER_WALL.value:
            return "inner-outer-inner wall"
        return "unknown"

    p = GCodeParser(gcode_path)

    # 新：用“整层窗口 + 物体片段”组合判断
    flat_wins = p._layer_windows_flat()          # List[(s,e)] 整层范围
    obj_layer_maps = p.layer_windows()           # List[{oid: [(s,e), ...]}] 物体片段
    if not flat_wins or not obj_layer_maps or len(flat_wins) != len(obj_layer_maps):
        return False, expected_style, []

    # 旧调用就按 object_id=0 来判断 Top surface 是否存在；保持原有语义
    top_blocks_per_layer = p.get_extrusion_blocks_by_object(
        ExtrusionType.TOP_SURFACE.value, 0, include_wipe=True, decode=False, workers=0
    )

    bad_layers: List[Tuple[int, WallStyle, List[str]]] = []

    with p.path.open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        for layer_idx, ((s, e), obj_map) in enumerate(zip(flat_wins, obj_layer_maps)):
            if layer_idx == 0:
                continue  # 跳过首层

            # 含顶面：整层跳过
            if layer_idx < len(top_blocks_per_layer) and top_blocks_per_layer[layer_idx]:
                continue

            # 把本层所有“物体片段”合并；没有物体标记则退化为整层
            spans: List[Tuple[int, int]] = []
            if obj_map:
                for segs in obj_map.values():
                    spans.extend(segs)
                spans.sort(key=lambda t: t[0])
            else:
                spans = [(s, e)]

            # 为了保留跨类型顺序，逐个 TYPE 扫描同层，但只统计“落在物体片段内”的 TYPE
            seq: List[str] = []
            for tp in find_all(mm, TYPE_PREFIX, s, e):
                if not _pos_in_any_span(tp, spans):
                    continue
                name = parse_type_name_at(mm, tp, e)
                if name in (ExtrusionType.INNER_WALL.value, ExtrusionType.OUTER_WALL.value):
                    if len(seq) < 3:
                        seq.append(name)
                    if len(seq) == 3:
                        break  # 只取前三个

            if len(seq) != 3:
                continue  # 不足3次/不规则：跳过，不参与校验

            parsed_style = judge_triplet(seq)
            if parsed_style != expected_style:
                bad_layers.append((layer_idx, parsed_style, seq))

    ok = (len(bad_layers) == 0)
    return ok, expected_style, bad_layers


# ================== is_infill_first ==================

INFILLS = {ExtrusionType.SPARSE_INFILL.value, ExtrusionType.INTERNAL_SOLID_INFILL.value}
WALLS = {ExtrusionType.INNER_WALL.value, ExtrusionType.OUTER_WALL.value}


def _pos_in_any_span(pos: int, spans: List[Tuple[int, int]]) -> bool:
    """判断字节偏移 pos 是否落在任意 [s,e) 片段内。"""
    for s, e in spans:
        if s <= pos < e:
            return True
    return False


def parse_is_infill_first(
        gcode_path: Path | str,
        expected_first: bool = True,
) -> Tuple[bool, bool, List[Tuple[int, str, List[str]]]]:
    """
    校验每层中 *infill*（Sparse infill / Internal solid infill 等） 与 *wall*
    （Inner wall / Outer wall）的先后关系（仅统计落在“物体片段”内的 ;TYPE: 顺序）。

      - expected_first=True ：若该层存在 infill，则 infill 必须在 wall 之前
      - expected_first=False：若该层存在 infill，则 wall 必须在 infill 之前

    其他说明：
      - 若该层不存在 infill -> 自动通过（不校验该层）。
      - 你已声明“有 infill 但没有 wall 的情况不存在”，若出现则视为失败并标注 'no-walls'。
      - 返回的 seq 仅包含本层出现的 INFILLS 与 WALLS，按原始先后顺序保留具体名。

    返回:
      ok            : 是否所有层都满足期望
      expected_first: 原样回传
      bad_layers    : List[(layer_idx, flag, seq)]
                      flag ∈ {'infill-after-walls', 'infill-before-walls', 'no-walls'}
                      seq  : 该层相关类型（INFILLS ∪ WALLS）的出现顺序明细
    """
    p = GCodeParser(gcode_path)

    # 如你的用例需要，可以保留该断言
    cfg = p.load_config()
    assert cfg.get("is_infill_first", True) is not None

    # 新旧窗口：
    # - flat_wins: 每层的整体范围（不按物体）
    # - obj_layer_maps: 每层的 {oid: [(s,e), ...]} 映射
    flat_wins = p._layer_windows_flat()
    obj_layer_maps = p.layer_windows()

    if not flat_wins or not obj_layer_maps or len(flat_wins) != len(obj_layer_maps):
        return False, expected_first, []

    bad_layers: List[Tuple[int, str, List[str]]] = []

    with Path(gcode_path).open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        for layer_idx, (flat_span, obj_map) in enumerate(zip(flat_wins, obj_layer_maps)):
            s, e = flat_span

            # 把本层所有物体片段合并为一个列表；若该层没有任何物体标记，则退化为“整层范围”
            spans: List[Tuple[int, int]] = []
            if obj_map:
                for segs in obj_map.values():
                    spans.extend(segs)
                # （可选）按起点排序，保持扫描时的时间顺序
                spans.sort(key=lambda t: t[0])
            else:
                spans = [(s, e)]

            # 收集“INFILLS 与 WALLS”的出现顺序
            seq: List[str] = []
            first_infill_i = None
            first_wall_i = None

            # 在整层范围内找 ;TYPE:，再过滤到“物体片段”里
            for pos in find_all(mm, TYPE_PREFIX, s, e):
                if not _pos_in_any_span(pos, spans):
                    continue
                name = parse_type_name_at(mm, pos, e)
                if name in INFILLS:
                    seq.append(name)
                    if first_infill_i is None:
                        first_infill_i = len(seq) - 1
                elif name in WALLS:
                    seq.append(name)
                    if first_wall_i is None:
                        first_wall_i = len(seq) - 1

                # 已经各见一次即可提前判断
                if first_infill_i is not None and first_wall_i is not None:
                    break

            # 没有 infill -> 本层通过
            if first_infill_i is None:
                continue

            # 有 infill 必须要有 wall，否则记失败
            if first_wall_i is None:
                bad_layers.append((layer_idx, "no-walls", seq))
                continue

            # 两者都存在，按期望判定
            if expected_first:
                # 期望：infill 在 wall 前
                if not (first_infill_i < first_wall_i):
                    bad_layers.append((layer_idx, "infill-after-walls", seq))
            else:
                # 期望：infill 在 wall 后
                if not (first_wall_i < first_infill_i):
                    bad_layers.append((layer_idx, "infill-before-walls", seq))

    # 判失败：出现 infill 与期望不符的层
    fatal = {"infill-after-walls", "infill-before-walls", "no-walls"}
    ok = all(flag not in fatal for _, flag, _ in bad_layers) if bad_layers else True
    return ok, expected_first, bad_layers

# ================== wall_direction ==================
# 行首 G0/G1（忽略注释）
_GMOVE_RE = re.compile(r"^\s*G(?:0|1)\b([^;]*)", re.IGNORECASE)
# 通用数值：+1, -1, 1., 1.23, .23 都支持
_NUM = r"([+-]?(?:\d+(?:\.\d*)?|\.\d+))"
# 参数提取（大小写不敏感）
_X_RE = re.compile(rf"\bX{_NUM}", re.IGNORECASE)
_Y_RE = re.compile(rf"\bY{_NUM}", re.IGNORECASE)
_E_RE = re.compile(rf"\bE{_NUM}", re.IGNORECASE)


def _direction_from_block(block_text: str, *, eps: float = 1e-3) -> WallDirection:
    """
    严格解析 + 自动闭合（不做终点≈起点去重）：
    - 仅接受形如 G1 X.. Y.. E.. 的行。
    - 不要求显式回环；面积计算时自动将最后一点连回第一点。
    """
    pts: List[Tuple[float, float]] = []

    for raw in block_text.splitlines():
        # 仅考虑 G1
        if not re.match(r"^\s*G1\b", raw, re.IGNORECASE):
            continue

        m = _GMOVE_RE.match(raw)
        if not m:
            continue
        body = m.group(1)

        # 必须带 E...
        if _E_RE.search(body) is None:
            continue

        # 必须同时带 X 和 Y
        mx, my = _X_RE.search(body), _Y_RE.search(body)
        if not (mx and my):
            continue

        x = float(mx.group(1))
        y = float(my.group(1))
        pts.append((x, y))

    # 至少 3 点
    if len(pts) < 3:
        return "unknown"

    # 鞋带公式（自动闭合：i 与 (i+1)%n，不做去重）
    area2 = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        area2 += x1 * y2 - x2 * y1

    if area2 > 0:
        return "ccw"
    if area2 < 0:
        return "cw"
    return "unknown"


def parse_wall_directions(
        gcode_path: Path | str,
        expected_dir: WallDirection,
) -> Tuple[bool, WallDirection, List[Tuple[int, str, int, WallDirection]]]:
    """
    独立函数：校验所有层中“所有内墙与外墙块”的打印方向是否都等于 expected_dir。
    只面向简单立方体：对每个墙块取“第一个闭合环”判方向。

    参数：
      gcode_path   : G-code 路径
      expected_dir : 期望方向，'cw' 或 'ccw'（若传 'unknown' 将直接判失败）

    返回：
      ok           : bool，是否所有参与校验的墙块方向都等于 expected_dir
      expected_dir : 原样回传
      bad_layers   : List[(layer_idx, kind, block_idx, parsed_dir)]
                     - layer_idx  : 层索引（与 layer_windows 对齐）
                     - kind       : 'Inner wall' 或 'Outer wall'
                     - block_idx  : 该层内此类墙的第几个块（从 0 开始）
                     - parsed_dir : 实际判定出的方向（'cw'/'ccw'/'unknown'）

    说明：
      - 层内若没有某类墙块，就不校验该类（既不通过也不记为失败）。
      - 若某墙块无法形成闭环 -> parsed_dir='unknown'，视为不符合 expected_dir，计入 bad_layers。
    """
    if expected_dir not in ("cw", "ccw"):
        # 期望方向必须明确；否则没有校验意义
        return False, expected_dir, []

    p = GCodeParser(gcode_path)
    inner_blocks_per_layer = p.get_extrusion_blocks_by_object(
        ExtrusionType.INNER_WALL.value, 0, include_wipe=False, decode=True, workers=0
    )
    outer_blocks_per_layer = p.get_extrusion_blocks_by_object(
        ExtrusionType.OUTER_WALL.value, 0, include_wipe=False, decode=True, workers=0
    )

    L = max(len(inner_blocks_per_layer), len(outer_blocks_per_layer))
    bad: List[Tuple[int, str, int, WallDirection]] = []

    for layer_idx in range(L):
        # 校验所有 Inner wall 块
        if layer_idx < len(inner_blocks_per_layer):
            for k, block in enumerate(inner_blocks_per_layer[layer_idx]):
                parsed = _direction_from_block(block)
                if parsed != expected_dir:
                    bad.append((layer_idx, ExtrusionType.INNER_WALL.value, k, parsed))
        # 校验所有 Outer wall 块
        if layer_idx < len(outer_blocks_per_layer):
            for k, block in enumerate(outer_blocks_per_layer[layer_idx]):
                parsed = _direction_from_block(block)
                if parsed != expected_dir:
                    bad.append((layer_idx, ExtrusionType.OUTER_WALL.value, k, parsed))

    ok = (len(bad) == 0)
    return ok, expected_dir, bad


# ================== only_one_wall_top ==================

def _walls_from_polylines_by_toolchange(polys: List[List[Point]]) -> int:
    """
    以“换刀点计数”换算墙数：
      - 若 polyline 内存在挤出点，则该 polyline 贡献: 1 + (#toolchange)
      - 若 polyline 没有挤出点，则贡献 0（忽略）
    """
    total = 0
    for pl in (polys or []):
        if any(p.kind == "extrude" for p in pl):
            tc = sum(1 for p in pl if p.kind == "toolchange")
            total += 1 + tc
    return total


# ================== only_one_wall_top ==================
from typing import List, Tuple, Dict, Any
from pathlib import Path

from engine_params.src.gcode.GCodeParser import GCodeParser  # 确保已导入

def parse_only_one_wall_top(
        gcode_path: Path | str,
        expected_only_one_wall_top: bool = True,
) -> Tuple[bool, bool, List[Tuple[int, str, Dict[str, Any]]]]:
    """
    校验最后一层（顶面层）外墙/内墙数量是否满足期望（基于 get_type_contours_per_layer）。
    参考原注释，语义保持不变。
    """
    p = GCodeParser(gcode_path)

    # 用新 API 一次性拿到“外墙/内墙”的所有折线（每条折线 = 一个挤出块）
    contours = p.get_type_contours_per_layer(types=[ExtrusionType.OUTER_WALL.value, ExtrusionType.INNER_WALL.value], workers=0)
    if not contours:
        return False, expected_only_one_wall_top, []

    # TODO，先写死，因为现在的样本都是只有一个，id都是0
    target_oid = 0

    # 层数
    L = len(contours)

    # ---------- 1) 先验：检查中间层 ----------
    mid_idx = L // 2
    mid_layer_map = contours[mid_idx] or {}
    mid_obj_map = mid_layer_map.get(target_oid, {}) if mid_layer_map else {}
    mid_inner = len(mid_obj_map.get(ExtrusionType.INNER_WALL.value, []) or [])
    mid_outer = len(mid_obj_map.get(ExtrusionType.OUTER_WALL.value, []) or [])
    mid_total = mid_inner + mid_outer
    assert mid_total != 2, (
        f"中间层(索引 {mid_idx})的墙总数仅为 2（Outer={mid_outer}, Inner={mid_inner}）。"
        f"校验该参数至少需要三层墙的 .3mf 模型。"
    )

    # ---------- 2) 校验最后一层 ----------
    last_idx = L - 1
    last_layer_map = contours[last_idx] or {}
    last_obj_map = last_layer_map.get(target_oid, {}) if last_layer_map else {}
    last_inner = len(last_obj_map.get(ExtrusionType.INNER_WALL.value, []) or [])
    last_outer = len(last_obj_map.get(ExtrusionType.OUTER_WALL.value, []) or [])

    bad_layers: List[Tuple[int, str, Dict[str, Any]]] = []
    details = {"outer_count": last_outer, "inner_count": last_inner}

    if expected_only_one_wall_top:
        # 期望：仅 1 个 Outer 且 0 个 Inner
        if last_inner > 0:
            bad_layers.append((last_idx, "has-inner-wall", details))
        if last_outer != 1:
            bad_layers.append((last_idx, "outer-count-not-one", details))
    else:
        # 期望：顶面层墙总数 >= 2
        if (last_outer + last_inner) < 2:
            bad_layers.append((last_idx, "top-walls-lt-2", details))

    ok = (len(bad_layers) == 0)
    return ok, expected_only_one_wall_top, bad_layers


def parse_one_wall_first_layer(
        gcode_path: Path | str,
        expected_one_wall_first_layer: bool = True,
) -> Tuple[bool, bool, List[Tuple[int, str, Dict[str, Any]]]]:
    """
    校验首层（layer 0）是否只打印单壁。
    约定：
      - 期望开启时：Outer wall 数量应为 1，Inner wall 数量应为 0。
      - 期望关闭时：总墙数（Inner + Outer）应不少于 2。
    """
    p = GCodeParser(gcode_path)

    contours = p.get_type_contours_per_layer(types=[ExtrusionType.OUTER_WALL.value, ExtrusionType.INNER_WALL.value], workers=0)
    if not contours:
        return False, expected_one_wall_first_layer, []

    target_oid = 0

    first_idx = 0
    first_layer_map = contours[first_idx] or {}
    first_obj_map = first_layer_map.get(target_oid, {}) if first_layer_map else {}
    first_inner = len(first_obj_map.get(ExtrusionType.INNER_WALL.value, []) or [])
    first_outer = len(first_obj_map.get(ExtrusionType.OUTER_WALL.value, []) or [])

    bad_layers: List[Tuple[int, str, Dict[str, Any]]] = []
    details = {"outer_count": first_outer, "inner_count": first_inner}

    if expected_one_wall_first_layer:
        if first_inner > 0:
            bad_layers.append((first_idx, "has-inner-wall", details))
        if first_outer != 1:
            bad_layers.append((first_idx, "outer-count-not-one", details))
    else:
        if (first_outer + first_inner) < 2:
            bad_layers.append((first_idx, "first-layer-walls-lt-2", details))

    ok = (len(bad_layers) == 0)
    return ok, expected_one_wall_first_layer, bad_layers


def _extract_last_extrude_e(parser: GCodeParser, type_value: str) -> Optional[float]:
    """Return the last extrude E value for the specified TYPE across all layers."""
    contours = parser.get_type_contours_per_layer(
        types=[type_value],
        workers=0,
    )
    if not contours:
        return None

    last_e: Optional[float] = None
    for layer_map in contours:
        if not layer_map:
            continue
        for oid in sorted(layer_map.keys()):
            type_map = layer_map.get(oid) or {}
            polylines = type_map.get(type_value) or []
            for poly in polylines or []:
                for pt in poly:
                    if pt.kind == "extrude" and pt.e is not None:
                        last_e = pt.e
    return last_e


def parse_top_solid_infill_flow_ratio(
        tested_gcode: Path | str,
        baseline_gcode: Path | str,
        expected_ratio: float,
        *,
        tol: float = 1e-3,
) -> Tuple[bool, Optional[float], Dict[str, object]]:
    """
    Compare the last top-surface extrude E between tested and baseline G-code.
    """
    tested_path = Path(tested_gcode)
    baseline_path = Path(baseline_gcode)

    tested_parser = GCodeParser(tested_path)
    baseline_parser = GCodeParser(baseline_path)

    tested_e = _extract_last_extrude_e(tested_parser, ExtrusionType.TOP_SURFACE.value)
    baseline_e = _extract_last_extrude_e(baseline_parser, ExtrusionType.TOP_SURFACE.value)

    ratio: Optional[float] = None
    ok = False

    if tested_e is not None and baseline_e is not None and abs(baseline_e) > 1e-9:
        ratio = tested_e / baseline_e
        ok = math.isclose(ratio, expected_ratio, rel_tol=tol, abs_tol=tol)

    details: Dict[str, object] = {
        "tested_gcode": str(tested_path),
        "baseline_gcode": str(baseline_path),
        "tested_e": tested_e,
        "baseline_e": baseline_e,
        "ratio": ratio,
        "expected_ratio": expected_ratio,
        "tolerance": tol,
    }

    return ok, ratio, details


def parse_bottom_solid_infill_flow_ratio(
        tested_gcode: Path | str,
        baseline_gcode: Path | str,
        expected_ratio: float,
        *,
        tol: float = 1e-3,
) -> Tuple[bool, Optional[float], Dict[str, object]]:
    """
    Compare the last bottom-surface extrude E between tested and baseline G-code.
    """
    tested_path = Path(tested_gcode)
    baseline_path = Path(baseline_gcode)

    tested_parser = GCodeParser(tested_path)
    baseline_parser = GCodeParser(baseline_path)

    tested_e = _extract_last_extrude_e(tested_parser, ExtrusionType.BOTTOM_SURFACE.value)
    baseline_e = _extract_last_extrude_e(baseline_parser, ExtrusionType.BOTTOM_SURFACE.value)

    ratio: Optional[float] = None
    ok = False

    if tested_e is not None and baseline_e is not None and abs(baseline_e) > 1e-9:
        ratio = tested_e / baseline_e
        ok = math.isclose(ratio, expected_ratio, rel_tol=tol, abs_tol=tol)

    details: Dict[str, object] = {
        "tested_gcode": str(tested_path),
        "baseline_gcode": str(baseline_path),
        "tested_e": tested_e,
        "baseline_e": baseline_e,
        "ratio": ratio,
        "expected_ratio": expected_ratio,
        "tolerance": tol,
    }

    return ok, ratio, details
