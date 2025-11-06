# -*- coding: utf-8 -*-
"""
    - 主要存放一些和解析GCode相关的数据类型、正则表达式、小函数

"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional, Tuple, Literal

# =============== 顶层/层内标记（与历史文件保持一致） ===============
HEADER_BEGIN: bytes = b"; HEADER_BLOCK_START"
HEADER_END: bytes = b"; HEADER_BLOCK_END"
THUMBNAIL_BEGIN: bytes = b"; THUMBNAIL_BLOCK_START"
THUMBNAIL_END: bytes = b"; THUMBNAIL_BLOCK_END"
EXEC_BEGIN: bytes = b"; EXECUTABLE_BLOCK_START"
EXEC_END: bytes = b"; EXECUTABLE_BLOCK_END"
CONFIG_BEGIN: bytes = b"; CONFIG_BLOCK_START"
CONFIG_END: bytes = b"; CONFIG_BLOCK_END"

LAYER_MARK: bytes = b";LAYER_CHANGE"  # 每层起点
TYPE_PREFIX: bytes = b";TYPE:"  # 层内挤出类型分段
WIPE_BEGIN: bytes = b";WIPE_START"
WIPE_END: bytes = b";WIPE_END"

# # EXCLUDE_OBJECT（旧式）行级正则
# OBJ2_BEGIN_RE = re.compile(
#     rb"^\s*;?\s*EXCLUDE_OBJECT_START\s+NAME=(?P<name>[^\r\n]+)\s*$",
#     re.IGNORECASE
# )
# OBJ2_END_RE = re.compile(
#     rb"^\s*;?\s*EXCLUDE_OBJECT_END\s+NAME=(?P<name>[^\r\n]+)\s*$",
#     re.IGNORECASE
# )
# ID_FROM_NAME_RE_B = re.compile(rb"(?:^|[^A-Za-z0-9])id_(\d+)(?:[^A-Za-z0-9]|$)", re.IGNORECASE)
# COPY_FROM_NAME_RE_B = re.compile(rb"(?:^|[^A-Za-z0-9_])copy_(\d+)(?:[^A-Za-z0-9_]|$)", re.IGNORECASE)

# 标识打印物体的新式行级正则，不做旧格式的兼容
OBJ_BEGIN_RE = re.compile(
    rb"^\s*;?\s*printing\s+object\s+(?P<name>.+?\s+id:\d+\s+copy\s+\d+)\s*$",
    re.IGNORECASE
)
OBJ_END_RE = re.compile(
    rb"^\s*;?\s*stop\s+printing\s+object\s+(?P<name>.+?\s+id:\d+\s+copy\s+\d+)\s*$",
    re.IGNORECASE
)

ID_FROM_NAME_RE_B  = re.compile(rb"\bid\s*:\s*(\d+)\b", re.IGNORECASE)
COPY_FROM_NAME_RE_B = re.compile(rb"\bcopy\s+(\d+)\b", re.IGNORECASE)

# CONFIG 行级正则
CFG_LINE_RE = re.compile(r"^\s*;\s*([^=]+?)\s*=\s*(.*?)\s*$")
Z_RE = re.compile(r"^\s*;Z\s*:\s*([+-]?\d+(?:\.\d+)?)\s*$")
H_RE = re.compile(r"^\s*;HEIGHT\s*:\s*([+-]?\d+(?:\.\d+)?)\s*$")

# —— 本文件内定义 SET_VELOCITY_LIMIT 相关正则
# TODO，这个键值对要做成枚举类来管理
_RX_SET_VEL = re.compile(br'\bSET_VELOCITY_LIMIT\b', re.IGNORECASE)
_RX_VEL_KV = re.compile(
    br'\b(ACCEL|ACCEL_TO_DECEL|SQUARE_CORNER_VELOCITY)\s*=\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))',
    re.IGNORECASE
)
_VEL_KEYS_CANON = ("ACCEL", "ACCEL_TO_DECEL", "SQUARE_CORNER_VELOCITY")

# =============== 指令体（仅看 ';' 前） ===============
_NUM_B = rb"([+-]?(?:\d+(?:\.\d*)?|\.\d+))"
_G1_RE_B = re.compile(rb"^\s*G1\b", re.IGNORECASE)
_G2_RE_B = re.compile(rb"^\s*G2\b", re.IGNORECASE)
_G3_RE_B = re.compile(rb"^\s*G3\b", re.IGNORECASE)
_X_RE_B = re.compile(rb"\bX" + _NUM_B + rb"\b", re.IGNORECASE)
_Y_RE_B = re.compile(rb"\bY" + _NUM_B + rb"\b", re.IGNORECASE)
_Z_NUM_B = re.compile(br"\bZ([+-]?(?:\d+(?:\.\d*)?|\.\d+))", re.IGNORECASE)
_E_RE_B = re.compile(rb"\bE" + _NUM_B + rb"\b", re.IGNORECASE)
_Z_RE_B = re.compile(rb"\bZ" + _NUM_B + rb"\b", re.IGNORECASE)
_F_RE_B = re.compile(rb"\bF" + _NUM_B + rb"\b", re.IGNORECASE)
_I_RE_B = re.compile(rb"\bI" + _NUM_B + rb"\b", re.IGNORECASE)
_J_RE_B = re.compile(rb"\bJ" + _NUM_B + rb"\b", re.IGNORECASE)
_R_RE_B = re.compile(rb"\bR" + _NUM_B + rb"\b", re.IGNORECASE)

# —— 为“只给 X 或只给 Y”的行提供更宽松的匹配（避免被诸如 EXTRAX 之类的词干命中）
_RX_X_LOOSE = re.compile(br'(?<![A-Z])X\s*([-+]?\d+(?:\.\d+)?)', re.IGNORECASE)
_RX_Y_LOOSE = re.compile(br'(?<![A-Z])Y\s*([-+]?\d+(?:\.\d+)?)', re.IGNORECASE)


# =============== 轻量解析工具 ===============
def pre_comment(line: bytes) -> bytes:
    """返回 ';' 前的指令体（去 CR）。整行注释 → 空。"""
    line = line.rstrip(b"\r")
    i = line.find(b";")
    return line if i == -1 else line[:i]


def is_g1(body: bytes) -> bool:
    return bool(_G1_RE_B.match(body))


def arc_mode(body: bytes) -> Optional[Literal["cw", "ccw"]]:
    if _G2_RE_B.match(body): return "cw"
    if _G3_RE_B.match(body): return "ccw"
    return None


def has_xy(body: bytes) -> bool:
    return bool(_X_RE_B.search(body) and _Y_RE_B.search(body))


def has_x(body: bytes) -> bool:
    return bool(_X_RE_B.search(body))


def has_y(body: bytes) -> bool:
    return bool(_Y_RE_B.search(body))


def has_e(body: bytes) -> bool:
    return bool(_E_RE_B.search(body))


def has_z(body: bytes) -> bool:
    return bool(_Z_RE_B.search(body))


def has_f(body: bytes) -> bool:
    return bool(_F_RE_B.search(body))


def parse_xy(body: bytes) -> Optional[Tuple[float, float]]:
    mX = _X_RE_B.search(body)
    if not mX: return None
    mY = _Y_RE_B.search(body)
    if not mY: return None
    try:
        x = float(mX.group(1).decode("ascii", errors="ignore"))
        y = float(mY.group(1).decode("ascii", errors="ignore"))
        return (x, y)
    except Exception:
        return None


def parse_xy_loose(body: bytes, last_xy: Optional[Tuple[float, float]]) -> Optional[Tuple[float, float]]:
    """
    宽松版本：允许只给 X 或只给 Y。
    - 若两者都出现，直接返回解析值；
    - 若仅出现 X 或 Y，且存在 last_xy，则用 last_xy 的另一轴补齐；
    - 若无法补齐，返回 None。
    """
    mX = _RX_X_LOOSE.search(body)
    mY = _RX_Y_LOOSE.search(body)

    got_x = mX is not None
    got_y = mY is not None

    if got_x and got_y:
        try:
            x = float(mX.group(1).decode("ascii", errors="ignore"))
            y = float(mY.group(1).decode("ascii", errors="ignore"))
            return (x, y)
        except Exception:
            return None

    if last_xy is None:
        return None

    try:
        if got_x and not got_y:
            x = float(mX.group(1).decode("ascii", errors="ignore"))
            return (x, last_xy[1])
        if got_y and not got_x:
            y = float(mY.group(1).decode("ascii", errors="ignore"))
            return (last_xy[0], y)
    except Exception:
        return None

    return None


def _parse_z(body: bytes) -> Optional[float]:
    m = _Z_NUM_B.search(body)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None


def parse_e(body: bytes) -> Optional[float]:
    mE = _E_RE_B.search(body)
    if not mE: return None
    try:
        return float(mE.group(1).decode("ascii", errors="ignore"))
    except Exception:
        return None


def parse_f(body: bytes) -> Optional[float]:
    mF = _F_RE_B.search(body)
    if not mF: return None
    try:
        return float(mF.group(1).decode("ascii", errors="ignore"))
    except Exception:
        return None


def parse_ij(body: bytes) -> Optional[Tuple[float, float]]:
    mI = _I_RE_B.search(body)
    mJ = _J_RE_B.search(body)
    if not (mI and mJ): return None
    try:
        return (float(mI.group(1).decode("ascii", errors="ignore")),
                float(mJ.group(1).decode("ascii", errors="ignore")))
    except Exception:
        return None


def parse_r(body: bytes) -> Optional[float]:
    mR = _R_RE_B.search(body)
    if not mR: return None
    try:
        return float(mR.group(1).decode("ascii", errors="ignore"))
    except Exception:
        return None


def _is_motion(body: bytes) -> bool:
    return bool(is_g1(body) or (arc_mode(body) is not None))


def _coord_any(body: bytes) -> bool:
    return bool(has_x(body) or has_y(body) or has_z(body))


def _coord_xy_both(body: bytes) -> bool:
    return bool(has_x(body) and has_y(body))


# ====== 严格版分类器 ======
def classify_kind(body: bytes) -> Literal["extrude", "travel", "wipe", "fanchange", "retract", "unretract"]:
    """
    仅当 G1/G2/G3 才分类：
      - 含 E：
          * e < 0:
              - 同时含 X 和 Y 且不含 Z -> wipe
              - 不含任意坐标 -> retract
              - 其它（含任一坐标但不满足上式，或含 Z） -> 无效（抛错）
          * e > 0:
              - 含 X 或 Y（至少一个）且不含 Z -> extrude
              - 不含任意坐标 -> unretract
              - 其它（含 Z 或坐标只含 Z） -> 无效（抛错）
      - 不含 E：
          * 有任一坐标 -> travel
          * 无坐标但有 F -> fanchange
          * 其它 -> 无效（抛错）
    """
    if not _is_motion(body):
        raise ValueError("not a motion line")

    e_val = parse_e(body) if has_e(body) else None
    if e_val is not None and abs(e_val) < 1e-12:
        e_val = None

    if e_val is not None:
        if e_val < 0:  # negative E
            if _coord_xy_both(body) and (not has_z(body)):
                return "wipe"
            if not _coord_any(body):
                return "retract"
            raise ValueError("invalid retract/wipe combo: E<0 with illegal coords")
        else:  # positive E
            if (has_x(body) or has_y(body)) and (not has_z(body)):
                return "extrude"
            if not _coord_any(body):
                return "unretract"
            raise ValueError("invalid extrude/unretract combo: E>0 with Z or illegal coords")

    # no E
    if _coord_any(body):
        return "travel"
    if has_f(body):
        return "fanchange"
    raise ValueError("unknown motion kind: no E, no coord, no F")


# =============== 圆弧数据 ===============
@dataclass(frozen=True)
class ArcMeta:
    direction: Optional[Literal["cw", "ccw"]]
    center_offset: Optional[Tuple[float, float]]
    center: Optional[Tuple[float, float]]
    radius: Optional[float]
    radius_deviation: Optional[float]

    @staticmethod
    def none() -> "ArcMeta":
        """返回一个“无圆弧”占位元数据对象。"""
        return ArcMeta(
            direction=None,
            center_offset=None,
            center=None,
            radius=None,
            radius_deviation=None,
        )


def build_arc_meta(body: bytes,
                   start_xy: Optional[Tuple[float, float]],
                   end_xy: Tuple[float, float]) -> ArcMeta:
    import math
    mode = arc_mode(body)
    if mode is None or start_xy is None:
        return ArcMeta(None, None, None, None, None)

    ij = parse_ij(body)
    if ij is not None:
        cx, cy = start_xy[0] + ij[0], start_xy[1] + ij[1]
        expected_radius = math.hypot(ij[0], ij[1])
        radius = math.hypot(end_xy[0] - cx, end_xy[1] - cy)
        return ArcMeta(mode, ij, (cx, cy), radius, radius - expected_radius)

    r = parse_r(body)
    return ArcMeta(mode, None, None, abs(r) if r is not None else None, None)
