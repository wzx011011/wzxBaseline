from __future__ import annotations
from pathlib import Path
import re

from engine_params.src.gcode.GCodeParser import GCodeParser  # 使用你最新的解析器

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
    base_outer = base.get_extrusion_blocks_by_object("Outer wall", 0, include_wipe=False, decode=True, workers=8)
    base_inner = base.get_extrusion_blocks_by_object("Inner wall", 0, include_wipe=False, decode=True, workers=8)

    test_outer = tst.get_extrusion_blocks_by_object("Outer wall", 0, include_wipe=False, decode=True, workers=8)
    test_inner = tst.get_extrusion_blocks_by_object("Inner wall", 0, include_wipe=False, decode=True, workers=8)

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


if __name__ == "__main__":
    baseline = Path(r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\baseline_cube_no_efc.gcode")
    tested = Path(
        r"C:\Users\118388\Desktop\automation\efc_cube_01mm_5layers.gcode"
    )
    # 示例：只考察前 5 层线性递减（后续层期望=0）
    assert_per_layer(baseline, tested, expected_comp=0.10, tol=1e-6, max_layers=5)
