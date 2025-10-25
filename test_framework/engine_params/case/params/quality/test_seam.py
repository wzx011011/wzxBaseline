from __future__ import annotations

from pathlib import Path

import pytest

from engine_params.src.gcode.wipe_speed_check import check_wipe_speed_by_layer

# ----------- 参数化示例（indirect=True） -----------
# 说明：
#  - 把 dict 作为 request.param 传入 slice_and_export fixture（indirect=True）
#  - 每个 param 会触发一次 fixture 完整流程（reset/load/slice/export）
cases = [
    {
        "input_3mf": r"D:\C3DBaseline\test_framework\engine_params\data\models\quality\cube_100%_wipe_speed.3mf",
        # "output_gcode": r"C:\Users\118388\Desktop\automation\cube_100%_wipe_speed.gcode",
        "project_name": "test_layer_height_case1",
        "timeouts": {"load": 120, "slice": 240, "export": 600}
    },
    {
        "input_3mf": r"C:\Users\118388\Desktop\automation\3DBenchy.3mf",
        # "output_gcode": r"C:\Users\118388\Desktop\automation\plate2.gcode",
        "project_name": "test_layer_height_case2",
        "timeouts": {"load": 120, "slice": 240, "export": 600}
    }
]

@pytest.mark.engine_params
@pytest.mark.parametrize("slice_and_export", cases, indirect=True)
def test_wipe_speed(slice_and_export):
    """
    slice_and_export fixture 已完成导出，并返回导出的 gcode Path。
    这里只做解析与断言（占位解析器）。
    """
    gcode_path: Path = slice_and_export  # fixture 返回的值
    assert gcode_path.exists(), "导出的 gcode 文件不存在（fixture 逻辑问题）"
    wipe_cfg:dict[str, object] = check_wipe_speed_by_layer(gcode_path,500)
    assert wipe_cfg is not None, "未在 G-code 中解析到 wipe"
    # 断言TODO
    # assert 0.01 < layer_h < 1.0, f"layer_height 看起来不合理: {layer_h}"