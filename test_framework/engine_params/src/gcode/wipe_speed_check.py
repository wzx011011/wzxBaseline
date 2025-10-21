# wipe_speed_check.py
from __future__ import annotations
from pathlib import Path
import re
from typing import Dict, List

from engine_params.src.gcode.GCodeParser import GCodeParser, Technology  # Technology 用于类型提示，可不强依赖

# 只截取分号前的指令体，且行首必须是 G0/G1
MOVE_CMD_RE = re.compile(r"^\s*G(?:0|1)\b([^;]*)", re.IGNORECASE)
# 在指令体里匹配 V 或 F，形式如 "F3600" 或 "V3600"（不支持等号）
SPEED_PARAM_RE = re.compile(r"\b(?:V|F)\s*([+-]?\d+(?:\.\d+)?)\b", re.IGNORECASE)

def _parse_V_values_from_text_block(text: str) -> list[float]:
    """
    从擦拭区块文本中解析所有 G0/G1 的速度参数：
    - 支持 V 或 F，但**不**支持等号形式（例如不支持 V=1800/F=3600）
    - 返回原始数值（通常单位为 mm/min）；后续可用 v/60 转为 mm/s
    """
    vals: list[float] = []
    for line in text.splitlines():
        m = MOVE_CMD_RE.match(line)
        if not m:
            continue
        body = m.group(1) or ""  # 行内（不含注释段）
        m2 = SPEED_PARAM_RE.search(body)
        if not m2:
            continue
        try:
            vals.append(float(m2.group(1)))
        except ValueError:
            pass
    return vals



def check_wipe_speed_by_layer(
    gcode_path: str | Path,
    expected_v_per_sec: float,
    *,
    float_tol: float = 1e-6,
    skip_if_role_based_wipe_speed_is_1: bool = True,
    return_all: bool = False,
    workers: int = 0,
) -> Dict[str, object]:
    """
    @ expected_v_per_sec: 单位为 mm/s

    逻辑：
      1) CONFIG_BLOCK: 若 role_based_wipe_speed == "1"，则报告 skip（或用于 pytest.skip）。
      2) EXECUTABLE_BLOCK: 按层遍历，每层搜集所有 WIPE 区块（;WIPE_START / ;WIPE_END）。
      3) 校验每个 WIPE 区块内 G0/G1 的 V/60 是否与期望一致。

    返回：
      {
        "skipped": bool,
        "skip_reason": Optional[str],
        "layers_total": int,
        "layers_with_wipe": int,
        "violations": [
          {"layer_index": i, "v": raw_v, "v_per_sec": raw_v/60, "expected": expected_v_per_sec},
          ...
        ],
        # 若 return_all=True，还会包含每层解析明细：
        "layer_details": [
          {"layer_index": i, "v_list": [...], "v_per_sec_list": [...]}, ...
        ]
      }
    """
    p = Path(gcode_path)
    parser = GCodeParser(p)

    # 1) 读取 CONFIG
    cfg = parser.load_config()
    rbw = cfg.get("role_based_wipe_speed")
    if skip_if_role_based_wipe_speed_is_1 and str(rbw).strip() == "1":
        return {
            "skipped": True,
            "skip_reason": "role_based_wipe_speed == 1，按用例规范需要为 0，已跳过该用例。",
            "layers_total": 0,
            "layers_with_wipe": 0,
            "violations": [],
        }

    # 2) 使用“新解析器 API”取每层的 WIPE 段（decode=True -> 直接得到字符串）
    per_layer_wipes = parser.get_wipe_blocks_per_layer(decode=True, workers=workers)
    layers_total = len(per_layer_wipes)

    violations: List[Dict[str, object]] = []
    layer_details: List[Dict[str, object]] = []
    layers_with_wipe = 0

    for layer_idx, wipe_map in enumerate(per_layer_wipes):
        # wipe_map 形如 { "wipe": [Technology, ...] }
        tech_list: List[Technology] = wipe_map.get("wipe", []) or []
        if not tech_list:
            if return_all:
                layer_details.append({"layer_index": layer_idx, "v_list": [], "v_per_sec_list": []})
            continue

        layers_with_wipe += 1

        v_list: List[float] = []
        vps_list: List[float] = []
        for tech in tech_list:
            # tech.data 为 str（因为 decode=True）；做个兜底以防未来更改
            block_text = tech.data if isinstance(tech.data, str) else (tech.data.decode("utf-8", errors="ignore") if tech.data is not None else "")
            for v in _parse_V_values_from_text_block(block_text):
                vps = v / 60.0
                v_list.append(v)
                vps_list.append(vps)
                if abs(vps - expected_v_per_sec) > float_tol:
                    violations.append({
                        "layer_index": layer_idx,
                        "v": v,
                        "v_per_sec": vps,
                        "expected": expected_v_per_sec
                    })

        if return_all:
            layer_details.append({"layer_index": layer_idx, "v_list": v_list, "v_per_sec_list": vps_list})

    result: Dict[str, object] = {
        "skipped": False,
        "skip_reason": None,
        "layers_total": layers_total,
        "layers_with_wipe": layers_with_wipe,
        "violations": violations,
    }
    if return_all:
        result["layer_details"] = layer_details
    return result


if __name__ == "__main__":

    demo = Path(r"C:\Users\118388\Desktop\automation\test.gcode")
    if demo.exists():
        out = check_wipe_speed_by_layer(demo, expected_v_per_sec=25.0, return_all=True, workers=8)
        print(out | {"violations_count": len(out["violations"])})
    else:
        print("Demo skipped: put a real gcode path in `demo`.")

    pass