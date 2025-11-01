from __future__ import annotations

import math
from pathlib import Path
import re
from typing import Dict, List, Tuple, Optional, Sequence

from engine_params.src.gcode.GCodeParser import GCodeParser, Point
from engine_params.src.gcode.constants import ExtrusionType

# 行首 G0/G1（忽略注释）
_GMOVE_RE = re.compile(r"^\s*G(?:0|1)\b([^;]*)", re.IGNORECASE)

# 通用数值：+1, -1, 1., 1.23, .23 都支持
_NUM = r"([+-]?(?:\d+(?:\.\d*)?|\.\d+))"

# 参数提取（大小写不敏感）
_X_RE = re.compile(rf"\bX{_NUM}", re.IGNORECASE)
_Y_RE = re.compile(rf"\bY{_NUM}", re.IGNORECASE)
_E_RE = re.compile(rf"\bE{_NUM}", re.IGNORECASE)


# TODO,好像有点问题
def _extract_xy_extrusions(text: str) -> list[tuple[float, float]]:
    """
    从一段 G-code 文本中提取“带 E 的挤出行”的 (X, Y) 点序列。
    - 不带 E 的行（空走、仅 F 设置）不算轮廓点
    - 行内如果只出现 X 或 Y，则沿用当前工艺状态的另一轴（若未知则跳过）
    """
    out: list[tuple[float, float]] = []
    cur_x = cur_y = None

    for raw in text.splitlines():
        m = _GMOVE_RE.match(raw)
        if not m:
            continue
        body = m.group(1) or ""

        # 必须含 E
        if _E_RE.search(body) is None:
            continue

        # 更新本行 X/Y（缺失则沿用上一状态）
        mx = _X_RE.search(body)
        my = _Y_RE.search(body)
        if mx is not None:
            try:
                cur_x = float(mx.group(1))
            except ValueError:
                pass
        if my is not None:
            try:
                cur_y = float(my.group(1))
            except ValueError:
                pass

        if (cur_x is not None) and (cur_y is not None):
            out.append((cur_x, cur_y))

    return out


def _bbox(points: list[tuple[float, float]]):
    """
    points -> (minX, maxX, minY, maxY)
    """
    if not points:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), max(xs), min(ys), max(ys))


def _layer_wall_bbox_from_extrusions(
        per_layer_blocks: list[list[str]],
        layer_index: int,
) -> tuple[float, float, float, float] | None:
    """
    从 get_extrusion_blocks_per_layer(entity, include_wipe=False, decode=True) 的结果中，
    计算指定层的包围盒。
    - per_layer_blocks[layer] 是该层该 TYPE 的若干整块文本（已去除 WIPE，并做过拼接）
    """
    if layer_index < 0 or layer_index >= len(per_layer_blocks):
        raise ValueError("layer_index is out of range")

    blocks = per_layer_blocks[layer_index] or []
    if not blocks:
        return None

    pts: list[tuple[float, float]] = []
    for text in blocks:
        pts.extend(_extract_xy_extrusions(text))

    return _bbox(pts)


def _assert_layer_bbox_shrink(
        base_bbox: tuple[float, float, float, float],
        test_bbox: tuple[float, float, float, float],
        expected_comp: float,
        tol: float,
        layer_index: int,
        wall_kind: str,
):
    """
    对单层单墙类型断言包围盒“单边内缩≈expected_comp”。
    """
    b_minx, b_maxx, b_miny, b_maxy = base_bbox
    t_minx, t_maxx, t_miny, t_maxy = test_bbox

    dx_min = t_minx - b_minx
    dx_max = b_maxx - t_maxx
    dy_min = t_miny - b_miny
    dy_max = b_maxy - t_maxy

    prefix = f"[layer={layer_index}, wall={wall_kind}]"
    assert abs(dx_min - expected_comp) <= tol, f"{prefix} X-left shrink {dx_min:.4f} != {expected_comp:.4f} (tol={tol})"
    assert abs(
        dx_max - expected_comp) <= tol, f"{prefix} X-right shrink {dx_max:.4f} != {expected_comp:.4f} (tol={tol})"
    assert abs(
        dy_min - expected_comp) <= tol, f"{prefix} Y-bottom shrink {dy_min:.4f} != {expected_comp:.4f} (tol={tol})"
    assert abs(dy_max - expected_comp) <= tol, f"{prefix} Y-top shrink {dy_max:.4f} != {expected_comp:.4f} (tol={tol})"


def _expected_comp_for_layer(base_comp: float, layer_index: int, max_layers: int | None) -> float:
    """
    基于层号计算该层的期望缩量。
    - max_layers 为 None → 全部层用 base_comp
    - 否则做线性递减：i < max_layers 时为 base_comp * (max_layers - i) / max_layers，否则为 0
    """
    if max_layers is None:
        return base_comp
    if layer_index >= max_layers:
        return 0.0
    # 线性递减（包含首层=base_comp，直到第 max_layers-1 层 > 0，之后为 0）
    return base_comp * (max_layers - layer_index) / max_layers


def assert_per_layer(
        baseline: Path,
        tested: Path,
        expected_comp: float,
        tol: float,
        max_layers: int | None = None,
):
    """
    逐层校验（outer / inner 各自一遍）。
    - 若 max_layers 不为空：按线性递减规则计算每层的 expected_comp_i（其后层为 0）。
    - 如果某层某墙类型在 base 或 test 中缺失 bbox，跳过该层该墙断言（但记录情况）。
    """
    base = GCodeParser(baseline)
    tst = GCodeParser(tested)

    # 分别取 Outer/Inner 的片段（已剔除 WIPE，并拼接）
    base_outer = base.get_extrusion_blocks_by_object(ExtrusionType.OUTER_WALL.value, 0, include_wipe=False, decode=True,
                                                     workers=8)
    base_inner = base.get_extrusion_blocks_by_object(ExtrusionType.INNER_WALL.value, 0, include_wipe=False, decode=True,
                                                     workers=8)

    test_outer = tst.get_extrusion_blocks_by_object(ExtrusionType.OUTER_WALL.value, 0, include_wipe=False, decode=True,
                                                    workers=8)
    test_inner = tst.get_extrusion_blocks_by_object(ExtrusionType.INNER_WALL.value, 0, include_wipe=False, decode=True,
                                                    workers=8)

    # 一致性校验：层数应一致
    assert len(base_outer) == len(base_inner) == len(test_outer) == len(test_inner), \
        "per-layer list length mismatch; please check layer_windows consistency"
    total_layers = len(base_outer)
    assert total_layers == len(test_outer), "baseline and tested layer counts differ"

    # 注意：这里不再用 max_layers 截断层数；需要对所有层断言，
    # 只是在公式中对 max_layers 之后的层期望值=0
    missing: list[tuple[int, str, str]] = []  # (layer, wall, which_missing)
    checked = 0

    for li in range(total_layers):
        exp_li = _expected_comp_for_layer(expected_comp, li, max_layers)

        # outer
        b_bbox = _layer_wall_bbox_from_extrusions(base_outer, li)
        t_bbox = _layer_wall_bbox_from_extrusions(test_outer, li)
        if b_bbox is None or t_bbox is None:
            missing.append((li, "outer", "baseline" if b_bbox is None else "tested"))
        else:
            _assert_layer_bbox_shrink(b_bbox, t_bbox, exp_li, tol, li, "outer")
            checked += 1

        # inner
        b_bbox = _layer_wall_bbox_from_extrusions(base_inner, li)
        t_bbox = _layer_wall_bbox_from_extrusions(test_inner, li)
        if b_bbox is None or t_bbox is None:
            missing.append((li, "inner", "baseline" if b_bbox is None else "tested"))
        else:
            _assert_layer_bbox_shrink(b_bbox, t_bbox, exp_li, tol, li, "inner")
            checked += 1

    assert checked > 0, f"没有任何层的外/内墙都同时存在可以比较的 bbox。缺失明细: {missing}"


def check_elefant_foot_compensation(
        baseline: Path,
        tested: Path,
        expected_comp: float,
        tol: float,
        max_layers: int | None = None,
):
    """
    入口封装：
    - 若 max_layers=None：整个打印过程期望固定缩量 expected_comp；
    - 若设定了 max_layers：按照线性递减规则校验（其后层为 0）。
    """
    assert_per_layer(baseline, tested, expected_comp, tol, max_layers=max_layers)

# ================== xy_hole_compensation / xy_contour_compensation ==================
BBox = Tuple[float, float, float, float]  # (minx, maxx, miny, maxy)

# ---------------------------
# 小工具：从 polyline 取二维包围盒
# ---------------------------
def _poly_bbox(pl: List[Point]) -> Optional[BBox]:
    if not pl:
        return None
    xs = [p.x for p in pl]
    ys = [p.y for p in pl]
    return (min(xs), max(xs), min(ys), max(ys))

# Δ边界（tested - baseline）
def _bbx_delta(t: BBox, b: BBox) -> Tuple[float, float, float, float]:
    tminx, tmaxx, tminy, tmaxy = t
    bminx, bmaxx, bminy, bmaxy = b
    return (tminx - bminx, tmaxx - bmaxx, tminy - bminy, tmaxy - bmaxy)

# 统一判定（Left/Bottom → -expected_offset；Right/Top → +expected_offset）
def _bbx_ok(delta: Tuple[float, float, float, float], expected_offset: float, tol: float) -> Tuple[bool, str]:
    dL, dR, dB, dT = delta
    expL = -expected_offset
    expR = +expected_offset
    expB = -expected_offset
    expT = +expected_offset
    def ok(a, e): return abs(a - e) <= tol
    good = ok(dL, expL) and ok(dR, expR) and ok(dB, expB) and ok(dT, expT)
    msg  = f"ΔL={dL:.4f}(exp {expL:+.4f}), ΔR={dR:.4f}(exp {expR:+.4f}), ΔB={dB:.4f}(exp {expB:+.4f}), ΔT={dT:.4f}(exp {expT:+.4f})"
    return good, msg

# 读取分层 contours（只取指定 object_id）
def _contours_per_layer(parser: GCodeParser, object_id: int) -> List[Dict[str, List[List[Point]]]]:
    layers_raw = parser.get_type_contours_per_layer(
        types=[ExtrusionType.OUTER_WALL.value, ExtrusionType.INNER_WALL.value],
        workers=0,
    )
    return [layer_map.get(object_id, {}) for layer_map in layers_raw]

def parse_enable_arc_fitting(
        gcode_path: Path | str,
        expected_enable: bool,
        *,
        object_id: int = 0,
) -> Tuple[bool, Dict[str, object]]:
    """
    说明：读取 CONFIG 中 enable_arc_fitting，并检查指定对象的内/外墙挤出块是否包含 G2/G3 指令。
    当 expected_value = 0 时，认为关闭圆弧拟合，内/外墙应仅包含 G0/G1。
    """
    parser = GCodeParser(Path(gcode_path))
    cfg = parser.load_config()

    raw_value = cfg.get("enable_arc_fitting")
    actual_value: Optional[int] = None
    if raw_value is not None:
        try:
            actual_value = int(str(raw_value).strip())
        except ValueError:
            actual_value = None

    config_ok = (actual_value == int(expected_enable))

    per_layer = parser.get_extrusions_blocks_by_object(
        [ExtrusionType.OUTER_WALL, ExtrusionType.INNER_WALL],
        object_id=object_id,
        include_wipe=False,
        decode=True,
        workers=0,
    )

    arc_layers: List[int] = []
    for layer_idx, type_map in enumerate(per_layer):
        has_arc = False
        for blocks in type_map.values():
            for block in blocks or []:
                for line in block.splitlines():
                    stripped = line.strip().upper()
                    if stripped.startswith("G2") or stripped.startswith("G3"):
                        has_arc = True
                        break
                if has_arc:
                    break
            if has_arc:
                arc_layers.append(layer_idx)
                break

    if not expected_enable:
        arcs_ok = len(arc_layers) == 0
    else:
        arcs_ok = True

    ok = config_ok and arcs_ok

    details: Dict[str, object] = {
        "expected_enable": expected_enable,
        "actual_value": actual_value,
        "config_ok": config_ok,
        "arc_layers": arc_layers,
        "arcs_ok": arcs_ok,
        "checked_layers": len(per_layer),
    }

    return ok, details


# =============================================================================
#    —— 每层取 “孔洞闭合轮廓”：索引 0（按模型的约定），用 OUTER_WALL 的第 0 条 polyline
# =============================================================================
def parse_xy_hole_compensation(
    *,
    baseline: str | Path,
    tested: str | Path,
    expected_offset: float,
    tolerance: float,
    object_id: int = 0,
) -> Tuple[bool, str]:
    """
    假设：
    - 每层 polyline 列表：索引 0 是孔洞闭合轮廓，索引 1 是外轮廓族闭合轮廓；
    - 模型两圈墙；
    - 使用 OUTER_WALL[0] 直接做 BBX 边偏移对比；
    - BBX 计算使用 polyline 的“所有点”，不区分 kind。
    """
    base = GCodeParser(Path(baseline))
    test = GCodeParser(Path(tested))

    base_layers = _contours_per_layer(base, object_id)
    test_layers = _contours_per_layer(test, object_id)

    total_layers = min(len(base_layers), len(test_layers))
    if total_layers == 0:
        return False, "未解析到任何层数据"

    failures: List[str] = []
    checked = 0

    for L in range(total_layers):
        # 不检验最后一层
        if L == total_layers - 1:
            break
        b_type = base_layers[L]
        t_type = test_layers[L]

        b_list = b_type.get(ExtrusionType.OUTER_WALL.value, [])
        t_list = t_type.get(ExtrusionType.OUTER_WALL.value, [])

        if len(b_list) < 1 or len(t_list) < 1:
            failures.append(f"L{L}: OUTER_WALL 缺少孔洞索引0 (baseline_len={len(b_list)}, tested_len={len(t_list)})")
            continue

        b_bbox = _poly_bbox(b_list[0])
        t_bbox = _poly_bbox(t_list[0])
        if b_bbox is None or t_bbox is None:
            failures.append(f"L{L}: OUTER_WALL[0] BBX 无法计算")
            continue

        delta = _bbx_delta(t_bbox, b_bbox)
        ok, msg = _bbx_ok(delta, expected_offset, tolerance)
        checked += 1
        if not ok:
            failures.append(f"L{L} hole@outer_wall[0]: {msg}")

    if checked == 0:
        return False, "没有任何层对齐到 OUTER_WALL[0] 进行校验"

    if failures:
        detail = " | ".join(failures[:30])
        if len(failures) > 30:
            detail += " | ... 共 {} 处不符合".format(len(failures))
        return False, detail

    return True, "xy_hole_compensation 达到期望"

# =============================================================================
#    —— 每层取 “外轮廓族闭合轮廓”：索引 1
#       * OUTER_WALL[1] → 外轮廓族的外墙
#       * INNER_WALL[1] → 外轮廓族的内墙
#    —— BBX 计算使用 polyline 的“所有点”
# =============================================================================
def parse_xy_contour_compensation(
    *,
    baseline: str | Path,
    tested: str | Path,
    expected_offset: float,
    tolerance: float,
    object_id: int = 0,
) -> Tuple[bool, str]:
    """
    假设与顺序同上；分别对 OUTER_WALL[1]（外墙）与 INNER_WALL[1]（内墙）做 BBX 边偏移对比。
    """
    base = GCodeParser(Path(baseline))
    test  = GCodeParser(Path(tested))

    base_layers = _contours_per_layer(base, object_id)
    test_layers = _contours_per_layer(test, object_id)

    total_layers = min(len(base_layers), len(test_layers))
    if total_layers == 0:
        return False, "未解析到任何层数据"

    failures: List[str] = []
    checked = 0

    for L in range(total_layers):

        # 不检验最后一层
        if L==total_layers-1:
            break
        b_type = base_layers[L]
        t_type = test_layers[L]

        # 外轮廓族 外墙：OUTER_WALL[1]
        b_ow = b_type.get(ExtrusionType.OUTER_WALL.value, [])
        t_ow = t_type.get(ExtrusionType.OUTER_WALL.value, [])
        if len(b_ow) < 2 or len(t_ow) < 2:
            failures.append(f"L{L}: OUTER_WALL 缺少外轮廓族索引1 (baseline_len={len(b_ow)}, tested_len={len(t_ow)})")
        else:
            b_bbox = _poly_bbox(b_ow[1])
            t_bbox = _poly_bbox(t_ow[1])
            if b_bbox is None or t_bbox is None:
                failures.append(f"L{L}: OUTER_WALL[1] BBX 无法计算")
            else:
                delta = _bbx_delta(t_bbox, b_bbox)
                ok, msg = _bbx_ok(delta, expected_offset, tolerance)
                checked += 1
                if not ok:
                    failures.append(f"L{L} outer_contour@outer_wall[1]: {msg}")

        # 外轮廓族 内墙：INNER_WALL[1]
        b_iw = b_type.get(ExtrusionType.INNER_WALL.value, [])
        t_iw = t_type.get(ExtrusionType.INNER_WALL.value, [])
        if len(b_iw) < 2 or len(t_iw) < 2:
            failures.append(f"L{L}: INNER_WALL 缺少外轮廓族索引1 (baseline_len={len(b_iw)}, tested_len={len(t_iw)})")
        else:
            b_bbox = _poly_bbox(b_iw[1])
            t_bbox = _poly_bbox(t_iw[1])
            if b_bbox is None or t_bbox is None:
                failures.append(f"L{L}: INNER_WALL[1] BBX 无法计算")
            else:
                delta = _bbx_delta(t_bbox, b_bbox)
                ok, msg = _bbx_ok(delta, expected_offset, tolerance)
                checked += 1
                if not ok:
                    failures.append(f"L{L} outer_contour@inner_wall[1]: {msg}")

    if checked == 0:
        return False, "没有任何层对齐到索引1（外轮廓族）进行校验"

    if failures:
        detail = " | ".join(failures[:30])
        if len(failures) > 30:
            detail += " | ... 共 {} 处不符合".format(len(failures))
        return False, detail

    return True, "xy_contour_compensation 达到期望"


if __name__ == "__main__":
    baseline = Path(r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\baseline_cube_no_efc.gcode")
    tested = Path(
        r"C:\Users\118388\Desktop\automation\efc_cube_01mm_5layers.gcode"
    )
    # 示例：只考察前 5 层线性递减（后续层期望=0）
    assert_per_layer(baseline, tested, expected_comp=0.10, tol=1e-6, max_layers=5)
