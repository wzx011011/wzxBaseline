from __future__ import annotations

from pathlib import Path

import pytest

from engine_params.src.gcode.wipe_speed_check import check_wipe_speed_by_layer

@pytest.mark.engine_params
def test_wipe_speed(slice_and_export: Path, expected_has_wipe: bool) -> None:
    """
    slice_and_export fixture 已完成导出，并返回导出的 gcode Path。
    这里只做解析与断言（占位解析器逻辑）。
    """
    gcode_path: Path = slice_and_export  # fixture 返回的文件路径
    assert gcode_path.exists(), "导出的 gcode 文件不存在（fixture 逻辑异常）"

    wipe_cfg: dict[str, object] = check_wipe_speed_by_layer(gcode_path, 500)
    # 通过配置结果判断是否检测到了 wipe 指令，必须与预期保持一致
    assert bool(wipe_cfg) is expected_has_wipe, (
        f"wipe 检测结果应为 {expected_has_wipe}，实际为 {bool(wipe_cfg)}，详情: {wipe_cfg}"
    )
    assert wipe_cfg is not None, "未在 G-code 中检测到 wipe"
    # TODO: 完成 wipe 相关的具体断言逻辑
