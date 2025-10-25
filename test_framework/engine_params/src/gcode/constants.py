from typing import Literal
'''
    维护一些GCodeParser要用的一些常量（例如枚举值等等）
'''



# ===================== 字面常量，方便IDE检查 =====================
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