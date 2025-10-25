# wipe_speed_check.py
from __future__ import annotations
from pathlib import Path
import re
from typing import Dict, List, Optional

from engine_params.src.gcode.GCodeParser import GCodeParser, Technology  # Technology 仅作类型提示

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


def _to_str(b_or_s: bytes | str | None) -> str:
    if b_or_s is None:
        return ""
    if isinstance(b_or_s, bytes):
        return b_or_s.decode("utf-8", errors="ignore")
    return b_or_s


def check_wipe_speed_by_layer(
    gcode_path: str | Path,
    expected_v_per_sec: float,
    *,
    float_tol: float = 1e-6,
    skip_if_role_based_wipe_speed_is_1: bool = True,
    return_all: bool = False,
    workers: int = 0,
    object_id: Optional[int] = None,  # ⭐ 新增：可指定 object_id，仅检查该物体；None=检查全部物体
) -> Dict[str, object]:
    """
    @ expected_v_per_sec: 单位为 mm/s

    逻辑：
      1) CONFIG_BLOCK: 若 role_based_wipe_speed == "1"，则报告 skip（或用于 pytest.skip）。
      2) EXECUTABLE_BLOCK:
         - 若 object_id 指定：使用一站式 API get_wipe_blocks_by_object() 获取“按层对齐”的块文本；
         - 若 object_id 未指定：使用 get_wipe_blocks_per_layer()，遍历每层所有物体。
      3) 校验每个 WIPE 区块内 G0/G1 的 V/60 是否与期望一致。

    返回：
      {
        "skipped": bool,
        "skip_reason": Optional[str],
        "layers_total": int,
        "layers_with_wipe": int,   # 至少有一个 wipe 的层数（按 object_id 过滤后统计）
        "violations": [
          {"layer_index": i, "v": raw_v, "v_per_sec": raw_v/60, "expected": expected_v_per_sec, "object_id": oid_or_none},
          ...
        ],
        # 若 return_all=True，还会包含每层解析明细：
        "layer_details": [
          {"layer_index": i, "v_list": [...], "v_per_sec_list": [...], "object_id": oid_or_none}, ...
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

    violations: List[Dict[str, object]] = []
    layer_details: List[Dict[str, object]] = []

    # 2A) 若指定 object_id：使用一站式 API，直接拿到“按层对齐”的文本块列表
    if object_id is not None:
        per_layer_blocks: List[List[bytes | str]] = parser.get_wipe_blocks_by_object(
            object_id, decode=True, workers=workers
        )
        layers_total = len(per_layer_blocks)
        layers_with_wipe = 0

        for layer_idx, blocks in enumerate(per_layer_blocks):
            if not blocks:
                if return_all:
                    layer_details.append({
                        "layer_index": layer_idx,
                        "v_list": [],
                        "v_per_sec_list": [],
                        "object_id": object_id,
                    })
                continue

            layers_with_wipe += 1

            v_list: List[float] = []
            vps_list: List[float] = []
            for blk in blocks:
                text = _to_str(blk)
                for v in _parse_V_values_from_text_block(text):
                    vps = v / 60.0
                    v_list.append(v)
                    vps_list.append(vps)
                    if abs(vps - expected_v_per_sec) > float_tol:
                        violations.append({
                            "layer_index": layer_idx,
                            "v": v,
                            "v_per_sec": vps,
                            "expected": expected_v_per_sec,
                            "object_id": object_id,
                        })

            if return_all:
                layer_details.append({
                    "layer_index": layer_idx,
                    "v_list": v_list,
                    "v_per_sec_list": vps_list,
                    "object_id": object_id,
                })

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

    # 2B) 未指定 object_id：遍历每层所有物体（使用新的 API 结构）
    per_layer_wipes = parser.get_wipe_blocks_per_layer(decode=True, workers=workers)
    layers_total = len(per_layer_wipes)
    layers_with_wipe = 0

    for layer_idx, wipe_map in enumerate(per_layer_wipes):
        # 新 API：wipe_map 形如 { object_id: [Technology, ...], ... }
        # 统计这一层是否至少有一个 wipe
        any_wipe_in_layer = any(bool(techs) for techs in wipe_map.values())
        if any_wipe_in_layer:
            layers_with_wipe += 1

        # 逐 object_id 校验
        layer_has_detail = False
        for oid, tech_list in wipe_map.items():
            if not tech_list:
                if return_all:
                    # 该层该 oid 无 wipe，若需要全量明细可以记录空
                    layer_details.append({
                        "layer_index": layer_idx,
                        "v_list": [],
                        "v_per_sec_list": [],
                        "object_id": oid,
                    })
                continue

            v_list: List[float] = []
            vps_list: List[float] = []
            for tech in tech_list:
                text = _to_str(tech.data)
                for v in _parse_V_values_from_text_block(text):
                    vps = v / 60.0
                    v_list.append(v)
                    vps_list.append(vps)
                    if abs(vps - expected_v_per_sec) > float_tol:
                        violations.append({
                            "layer_index": layer_idx,
                            "v": v,
                            "v_per_sec": vps,
                            "expected": expected_v_per_sec,
                            "object_id": oid,
                        })

            if return_all:
                layer_details.append({
                    "layer_index": layer_idx,
                    "v_list": v_list,
                    "v_per_sec_list": vps_list,
                    "object_id": oid,
                })
                layer_has_detail = True

        # 如果该层没有任何 object 的 wipe，但 return_all=True，补一条空明细（不强制，按需）
        if return_all and not any(wipe_map.values()) and not layer_has_detail:
            layer_details.append({
                "layer_index": layer_idx,
                "v_list": [],
                "v_per_sec_list": [],
                "object_id": None,
            })

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
        # 示例1：检查所有物体
        out_all = check_wipe_speed_by_layer(demo, expected_v_per_sec=25.0, return_all=True, workers=8)
        print({"all_objects": True, "violations_count": len(out_all["violations"])})
        # 示例2：仅检查 object_id=0
        out_oid0 = check_wipe_speed_by_layer(demo, expected_v_per_sec=25.0, return_all=True, workers=8, object_id=0)
        print({"all_objects": False, "object_id": 0, "violations_count": len(out_oid0["violations"])})
    else:
        print("Demo skipped: put a real gcode path in `demo`.")
