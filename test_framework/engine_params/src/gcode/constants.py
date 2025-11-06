# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from enum import Enum
from typing import (
    Iterable,
    Literal,
    Optional,
    Sequence,
    Set,
    Union,
)

"""
维护 GCodeParser/GCodeParserEx 需要使用的常量与枚举。
本版本将“规范化/别名映射”放在模块级，避免与 Enum 成员发生属性名冲突。
"""


# ===================== 这块先随便放吧 =====================

ACCEL_KEY = "ACCEL"

# ===================== 类型别名（给静态检查/提示用） =====================

WallStyle = Literal[
    "inner wall/outer wall",
    "outer wall/inner wall",
    "inner-outer-inner wall",
    "unknown",
]

WallDirection = Literal[
    "cw",
    "ccw",
    "unknown",
]

# ===================== 模块级：标签规范化工具 & 别名表 =====================

# 空白/连字符/下划线/斜杠等统一处理
_PUNCT_RE = re.compile(r"[\s_\-\/]+")
_WS_RE = re.compile(r"\s+")

def _to_text(x: Union[str, bytes]) -> str:
    if isinstance(x, bytes):
        return x.decode("utf-8", errors="ignore")
    return x

def normalize_label(label: Union[str, bytes]) -> str:
    """
    把输入标签（str/bytes）规范化为比较用 key：
    - 全小写
    - 连字符/下划线/斜杠/多空白折叠为单空格
    - 去首尾空白
    """
    s = _to_text(label).strip().lower()
    s = _PUNCT_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    return s

# 别名映射：key 使用 normalize_label() 的结果；value 为“规范显示值”（即枚举 .value）
_ALIASES: dict[str, str] = {
    # ---- walls
    "inner wall": "Inner wall",
    "perimeter inner": "Inner wall",
    "outer wall": "Outer wall",
    "perimeter outer": "Outer wall",
    "overhang wall": "Overhang wall",

    # ---- infill
    "sparse infill": "Sparse infill",
    "infill sparse": "Sparse infill",
    "internal solid infill": "Internal solid infill",
    "solid infill": "Internal solid infill",
    "gap infill": "Gap infill",

    # ---- surfaces / skin
    "top surface": "Top surface",
    "top skin": "Top surface",
    "bottom surface": "Bottom surface",
    "bottom skin": "Bottom surface",
    "ironing": "Ironing",

    # ---- bridge
    "bridge": "Bridge",
    "internal bridge": "Internal Bridge",

    # ---- brim / skirt / tower
    "skirt": "Skirt",
    "brim": "Brim",
    "prime tower": "Prime tower",
    "wipe tower": "Prime tower",

    # ---- support
    "support": "Support",
    "support infill": "Support",
    "support interface": "Support interface",
    "support roof": "Support interface",
    "support transition": "Support transition",

    # ---- custom
    "custom": "Custom",
    # 注意：MULTIPLE 不作为真实类型参与匹配
}

# ===================== 枚举定义 =====================

class ExtrusionType(str, Enum):
    INNER_WALL = "Inner wall"
    OUTER_WALL = "Outer wall"
    OVERHANG_WALL = "Overhang wall"
    SPARSE_INFILL = "Sparse infill"
    INTERNAL_SOLID_INFILL = "Internal solid infill"
    TOP_SURFACE = "Top surface"
    BOTTOM_SURFACE = "Bottom surface"
    IRONING = "Ironing"
    BRIDGE = "Bridge"
    INTERNAL_BRIDGE = "Internal Bridge"
    GAP_INFILL = "Gap infill"
    SKIRT = "Skirt"
    BRIM = "Brim"
    SUPPORT = "Support"
    SUPPORT_INTERFACE = "Support interface"
    SUPPORT_TRANSITION = "Support transition"
    PRIME_TOWER = "Prime tower"
    CUSTOM = "Custom"
    MULTIPLE = "Multiple"

    # -------- 家族分组（便于快速过滤/统计） --------
    @classmethod
    def WALL_SET(cls) -> Set["ExtrusionType"]:
        return {cls.INNER_WALL, cls.OUTER_WALL, cls.OVERHANG_WALL}

    @classmethod
    def INFILL_SET(cls) -> Set["ExtrusionType"]:
        return {cls.SPARSE_INFILL, cls.INTERNAL_SOLID_INFILL, cls.GAP_INFILL}

    @classmethod
    def SURFACE_SET(cls) -> Set["ExtrusionType"]:
        return {cls.TOP_SURFACE, cls.BOTTOM_SURFACE, cls.IRONING}

    @classmethod
    def SUPPORT_SET(cls) -> Set["ExtrusionType"]:
        return {cls.SUPPORT, cls.SUPPORT_INTERFACE, cls.SUPPORT_TRANSITION}

    @classmethod
    def TOWER_SKIRT_BRIM_SET(cls) -> Set["ExtrusionType"]:
        return {cls.PRIME_TOWER, cls.SKIRT, cls.BRIM}

    # -------- 规范化 & 同义词映射（调用模块级工具，避免类属性冲突） --------
    @classmethod
    def from_label(cls, label: Union["ExtrusionType", str, bytes, None]) -> Optional["ExtrusionType"]:
        """
        将任意输入（ExtrusionType/str/bytes）映射为枚举成员；失败返回 None。
        规则：
          - 大小写/空白/连字符/下划线/斜杠不敏感；
          - 支持常见别名（如 top skin -> Top surface, wipe tower -> Prime tower）。
        """
        if label is None:
            return None
        if isinstance(label, cls):
            return label

        norm = normalize_label(label)

        # 1) 先查别名表
        target_val = _ALIASES.get(norm)
        if target_val:
            for m in cls:
                if m.value == target_val:
                    return m

        # 2) 再与各成员的规范化值对齐
        for m in cls:
            if normalize_label(m.value) == norm:
                return m

        return None

    @classmethod
    def to_str(cls, x: Union["ExtrusionType", str, bytes, None]) -> Optional[str]:
        """
        返回规范显示值（枚举 .value）；无法识别返回 None。
        """
        m = cls.from_label(x)
        return m.value if m else None

    @classmethod
    def as_filter(cls, items: Sequence[Union["ExtrusionType", str, bytes]]) -> Set[str]:
        """
        将一组标签归一化为“规范显示值字符串”的集合，用于白名单过滤。
        忽略无法识别项；忽略 MULTIPLE。
        """
        out: Set[str] = set()
        for it in items:
            m = cls.from_label(it)
            if not m:
                continue
            if m is cls.MULTIPLE:
                continue
            out.add(m.value)  # 对外统一使用规范显示值（大小写/空格保持）
        return out

    # -------- 便捷判断 --------
    def is_wall(self) -> bool:
        return self in self.WALL_SET()

    def is_infill(self) -> bool:
        return self in self.INFILL_SET()

    def is_surface(self) -> bool:
        return self in self.SURFACE_SET()

    def is_support(self) -> bool:
        return self in self.SUPPORT_SET()
