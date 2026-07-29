"""Insert concise validation-method comments into process parameter tests."""

from __future__ import annotations

import ast
from pathlib import Path


GROUP_MODEL = {
    "strength": "实体、薄壁、桥接或填充专用 3MF",
    "others": "首层附着、外壳或多对象专用 3MF",
    "filament": "双材料悬挑及擦料塔专用 3MF",
}


def evidence(name: str) -> str:
    if "bridge" in name:
        return "Bridge 类型路径的数量、主方向和挤出行为"
    if "infill" in name or "fill" in name or "tpms" in name or "tmps" in name:
        return "各层填充类型、路径方向、间距及正向挤出量"
    if "shell" in name or "surface_pattern" in name:
        return "Top/Bottom surface 连续层数、厚度和路径形态"
    if "wall" in name or "thin" in name:
        return "Inner/Outer wall 的每层路径数、顺序和几何覆盖"
    if "brim" in name:
        return "首层 Brim 路径的存在性、圈数、边界和对象间隙"
    if "skirt" in name or "draft_shield" in name:
        return "Skirt 路径的层数、圈数、边界距离、挤出长度和速度"
    if "sequence" in name or "print_order" in name:
        return "对象标签、层高 Z 和对象开始/结束标记的实际顺序"
    if "spiral" in name:
        return "外墙路径中的连续 Z 抬升、回抽次数和 XY 平滑变化"
    if "fuzzy" in name:
        return "Outer wall 坐标相对规则轮廓的偏移幅度、点距及生效层"
    if "gcode" in name or name in {"reduce_infill_retraction", "exclude_object"}:
        return "输出指令、行号、注释、对象标签和回抽事件"
    if "prime_tower" in name or "wipe_tower" in name or name.startswith("tc_wt"):
        return "Prime tower 分层路径、边界尺寸、工具切换及挤出/回抽量"
    if "interlocking" in name or "segmented" in name:
        return "T0/T1 材料边界附近的交错路径、层周期、宽度和深度"
    if "flush_into" in name:
        return "换料后填充/支撑角色由 T0/T1 承担的挤出量和出现比例"
    if "filament" in name:
        return "指定特征由目标 T0/T1 工具实际挤出的路径占比"
    if name in {"filename_format", "post_process", "notes"}:
        return "导出文件名规则以及 G-code 头尾中的脚本/备注结果"
    return "目标特征的 G-code 类型块、运动指令和尾部配置"


def update_file(path: Path, group: str) -> bool:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines(keepends=True)
    tree = ast.parse(text)
    inserts: list[tuple[int, str]] = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not node.name.startswith("test_"):
            continue
        body_start = node.body[0].lineno
        if isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
            body_start = node.body[0].end_lineno + 1
        nearby = "".join(lines[max(0, body_start - 2): min(len(lines), body_start + 1)])
        if "验证方法：" in nearby:
            continue
        parameter = node.name.removeprefix("test_")
        comment = (
            f"    # 验证方法：使用{GROUP_MODEL[group]}切片，解析{evidence(parameter)}；"
            "配置值仅用于确认输入，最终由实际 G-code 行为断言。\n"
        )
        inserts.append((body_start - 1, comment))
    for index, comment in reversed(inserts):
        lines.insert(index, comment)
    if inserts:
        path.write_text("".join(lines), encoding="utf-8")
    return bool(inserts)


def main() -> int:
    root = Path(__file__).resolve().parents[1] / "case/params/process"
    changed = 0
    for group in GROUP_MODEL:
        for path in sorted((root / group).glob("test_*.py")):
            if update_file(path, group):
                print(path.relative_to(root))
                changed += 1
    print(f"updated {changed} test modules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
