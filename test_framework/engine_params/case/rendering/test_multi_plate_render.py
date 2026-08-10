from __future__ import annotations

import re
from pathlib import Path

import cv2
import numpy as np
import pytest

from engine_params.conftest import wait_for_file_written
from engine_params.src.slicerctl.slicing import wait_for_slicing_done


MODEL_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "models"
    / "rendering"
    / "multi_plate"
    / "36个盘.3mf"
)


def _cluster_count(values: list[float], tolerance: float) -> int:
    clusters: list[list[float]] = []
    for value in sorted(values):
        if not clusters or value - float(np.mean(clusters[-1])) > tolerance:
            clusters.append([value])
        else:
            clusters[-1].append(value)
    return len(clusters)


def _analyze_plate_grid(image: np.ndarray, debug_path: Path) -> dict[str, object]:
    """从程序内部截取的固定顶视图中检测独立盘面。"""
    viewport = image

    gray = cv2.cvtColor(viewport, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 10, 30)
    connected = cv2.morphologyEx(
        edges,
        cv2.MORPH_CLOSE,
        np.ones((5, 5), dtype=np.uint8),
        iterations=2,
    )
    _, _, stats, _ = cv2.connectedComponentsWithStats(connected)

    view_height, view_width = gray.shape
    min_area = view_height * view_width * 0.002
    candidates: list[tuple[int, int, int, int, int]] = []
    for x, y, item_width, item_height, area in stats[1:]:
        if y < view_height * 0.01:
            continue
        if area < min_area or item_width < view_width * 0.04 or item_height < view_height * 0.035:
            continue
        candidates.append((int(x), int(y), int(item_width), int(item_height), int(area)))

    wide = [box for box in candidates if box[2] / box[3] > 3.0 or box[2] > view_width * 0.45]
    regular = [box for box in candidates if 0.60 <= box[2] / box[3] <= 1.70]

    row_count = 0
    column_count = 0
    width_variation = float("inf")
    height_variation = float("inf")
    if regular:
        widths = np.array([box[2] for box in regular], dtype=float)
        heights = np.array([box[3] for box in regular], dtype=float)
        centers_x = [box[0] + box[2] / 2 for box in regular]
        centers_y = [box[1] + box[3] / 2 for box in regular]
        row_count = _cluster_count(centers_y, float(np.median(heights) * 0.50))
        column_count = _cluster_count(centers_x, float(np.median(widths) * 0.50))
        width_variation = float(np.std(widths) / np.mean(widths))
        height_variation = float(np.std(heights) / np.mean(heights))

    debug = viewport.copy()
    for x, y, item_width, item_height, _ in candidates:
        color = (0, 0, 255) if (x, y, item_width, item_height, _) in wide else (0, 255, 0)
        cv2.rectangle(debug, (x, y), (x + item_width, y + item_height), color, 3)
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(debug_path), debug)

    return {
        "candidate_count": len(candidates),
        "regular_plate_count": len(regular),
        "wide_component_count": len(wide),
        "wide_components": wide,
        "row_count": row_count,
        "column_count": column_count,
        "width_variation": width_variation,
        "height_variation": height_variation,
        "debug_image": str(debug_path),
    }


@pytest.mark.engine_params
def test_render_36_plates_as_6_by_6_grid(engine_injector, pytestconfig):
    assert MODEL_PATH.is_file(), f"测试模型不存在: {MODEL_PATH}"

    reset = engine_injector.submit(
        "reset_project",
        {"skip_confirm": True, "silent": True, "project_name": "render_36_plates"},
    ).result(timeout=30)
    assert reset.get("code") == 0, f"重置项目失败: {reset}"

    loaded = engine_injector.submit(
        "trigger_load_project2",
        {"file": str(MODEL_PATH), "discard_preset_changes": True},
        timeout=300,
    ).result(timeout=300)
    assert loaded.get("code") == 0, f"加载36盘项目失败: {loaded}"

    artifact = Path(pytestconfig.rootpath) / "artifacts" / "multi_plate_render" / "actual.png"
    artifact.parent.mkdir(parents=True, exist_ok=True)

    # GLCanvas3D::render_on_image() 在交换缓冲区后读取后缓冲，第一次会读到切换
    # 顶视图前的上一帧。先渲染一次，使正式截图稳定取得目标视角。
    warmup_artifact = artifact.with_name("warmup.png")
    warmed_up = engine_injector.submit(
        "capture_plate_overview",
        {"save_as": str(warmup_artifact), "view": "top"},
        timeout=60,
    ).result(timeout=60)
    assert warmed_up.get("code") == 0, f"预热多盘顶视图失败: {warmed_up}"

    captured = engine_injector.submit(
        "capture_plate_overview",
        {"save_as": str(artifact), "view": "top"},
        timeout=60,
    ).result(timeout=60)
    assert captured.get("code") == 0, f"截取多盘顶视图失败: {captured}"
    assert artifact.is_file(), f"截图命令成功但图片不存在: {artifact}, response={captured}"

    image = cv2.imread(str(artifact), cv2.IMREAD_COLOR)
    assert image is not None and image.size > 0, f"无法读取3D画布截图: {artifact}"

    payload = captured.get("payload", {})
    assert payload.get("width") == image.shape[1], f"截图宽度与响应不一致: {captured}"
    assert payload.get("height") == image.shape[0], f"截图高度与响应不一致: {captured}"
    debug_artifact = artifact.with_name("detected.png")
    result = _analyze_plate_grid(image, debug_artifact)
    print(f"[multi_plate_render] screenshot={artifact}, result={result}")

    layout_ok = (
        result["candidate_count"] == 36
        and result["regular_plate_count"] >= 34
        and result["wide_component_count"] == 0
        and result["row_count"] == 6
        and result["column_count"] == 6
        and result["width_variation"] <= 0.25
        and result["height_variation"] <= 0.25
    )
    assert layout_ok, f"36盘渲染不是规则6×6结构: {result}"


@pytest.mark.engine_params
def test_slice_plate_36_and_export_gcode(engine_injector, pytestconfig):
    assert MODEL_PATH.is_file(), f"测试模型不存在: {MODEL_PATH}"

    reset = engine_injector.submit(
        "reset_project",
        {"skip_confirm": True, "silent": True, "project_name": "slice_plate_36"},
    ).result(timeout=30)
    assert reset.get("code") == 0, f"重置项目失败: {reset}"

    loaded = engine_injector.submit(
        "trigger_load_project2",
        {"file": str(MODEL_PATH), "discard_preset_changes": True},
        timeout=300,
    ).result(timeout=300)
    assert loaded.get("code") == 0, f"加载36盘项目失败: {loaded}"

    triggered = engine_injector.submit(
        "trigger_slice_plate",
        {"plate_number": 36},
        timeout=60,
    ).result(timeout=60)
    assert triggered.get("code") == 0, f"触发第36盘切片失败: {triggered}"
    assert triggered.get("payload", {}).get("plate_number") == 36, triggered

    progress = wait_for_slicing_done(
        engine_injector,
        timeout=600,
        poll_interval=1,
        stall_timeout=120,
        command_params={"plate_number": 36},
    )
    assert progress.get("all_plate_finished"), f"第36盘未完成切片: {progress}"

    output = Path(pytestconfig.rootpath) / "artifacts" / "multi_plate_slice" / "plate_36.gcode"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    exported = engine_injector.submit(
        "export_gcode",
        {"export_all": False, "output": str(output)},
        timeout=300,
    ).result(timeout=360)
    assert exported.get("code") == 0, f"导出第36盘 G-code失败: {exported}"

    wait_for_file_written(output, timeout=180, settle_time=1)
    assert output.stat().st_size > 1024, f"第36盘 G-code文件过小: {output.stat().st_size} bytes"
    content = output.read_text(encoding="utf-8", errors="replace")
    assert ";LAYER_CHANGE" in content, "第36盘 G-code中没有层变化标记"
    assert re.search(r"(?m)^G[01][^;\r\n]*\bE[-+]?\d*\.?\d+", content), (
        "第36盘 G-code中没有有效挤出指令"
    )
