"""Shared behavioral G-code extraction for process/quality assertions.

Unlike :class:`GCodeParser`, which is optimized for byte-range queries, this
module keeps the state carried by G-code commands (position, feed rate,
extrusion mode, role, layer and generated WIDTH/HEIGHT hints).  Quality checks
use the resulting moves to validate toolpath behavior instead of echoing values
from CONFIG_BLOCK.
"""

from __future__ import annotations

import math
import re
import statistics
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence


_PARAM_RE = re.compile(r"\b([XYZEFIJR])([+-]?(?:\d+(?:\.\d*)?|\.\d+))", re.I)
_COMMENT_FLOAT_RE = re.compile(r"^;\s*([A-Z_]+)\s*:\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))", re.I)


@dataclass(frozen=True)
class Move:
    line_no: int
    command: str
    layer: int
    role: str | None
    block: int
    path: int
    x0: float
    y0: float
    z0: float
    x: float
    y: float
    z: float
    e: float
    feedrate: float | None
    width: float | None
    height: float | None
    wipe: bool

    @property
    def xy_length(self) -> float:
        if self.command in {"G2", "G3"}:
            # Chord length is deliberately used here. Arc-sensitive checks use
            # arc_count(), while flow checks discard arcs to avoid bias.
            return math.hypot(self.x - self.x0, self.y - self.y0)
        return math.hypot(self.x - self.x0, self.y - self.y0)

    @property
    def is_extrusion(self) -> bool:
        return self.e > 1e-9 and self.xy_length > 1e-9 and not self.wipe

    @property
    def speed(self) -> float | None:
        return None if self.feedrate is None else self.feedrate / 60.0

    @property
    def angle(self) -> float | None:
        if self.xy_length <= 1e-9:
            return None
        return math.degrees(math.atan2(self.y - self.y0, self.x - self.x0)) % 180.0


@dataclass(frozen=True)
class LayerInfo:
    index: int
    z: float | None
    height: float | None


class BehaviorGCode:
    """Stateful, role-aware view of a generated G-code file."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.moves: list[Move] = []
        self.layers: list[LayerInfo] = []
        self._parse()

    def _parse(self) -> None:
        x = y = z = 0.0
        absolute_xyz = True
        relative_e = False
        absolute_e_value = 0.0
        feedrate: float | None = None
        layer = -1
        layer_z: float | None = None
        layer_height: float | None = None
        role: str | None = None
        width: float | None = None
        move_height: float | None = None
        block = 0
        path = 0
        break_path = True
        wipe = False

        for line_no, raw in enumerate(self.path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            line = raw.strip()
            if not line:
                continue

            if line.startswith(";LAYER_CHANGE"):
                if layer >= 0:
                    self.layers.append(LayerInfo(layer, layer_z, layer_height))
                layer += 1
                layer_z = None
                layer_height = None
                move_height = None
                role = None
                break_path = True
                continue
            if line.startswith(";TYPE:"):
                role = line.split(":", 1)[1].strip()
                block += 1
                path += 1
                break_path = False
                width = None
                move_height = layer_height
                continue
            if line.startswith(";WIPE_START"):
                wipe = True
                break_path = True
                continue
            if line.startswith(";WIPE_END"):
                wipe = False
                break_path = True
                continue

            cm = _COMMENT_FLOAT_RE.match(line)
            if cm:
                key, value = cm.group(1).upper(), float(cm.group(2))
                if key == "Z":
                    layer_z = value
                elif key == "HEIGHT":
                    if role is None or layer_height is None:
                        layer_height = value
                    move_height = value
                elif key == "WIDTH":
                    width = value
                continue

            body = line.split(";", 1)[0].strip()
            if not body:
                continue
            command = body.split(None, 1)[0].upper()
            if command == "G90":
                absolute_xyz = True
                continue
            if command == "G91":
                absolute_xyz = False
                continue
            if command == "M82":
                relative_e = False
                continue
            if command == "M83":
                relative_e = True
                continue
            params = {key.upper(): float(value) for key, value in _PARAM_RE.findall(body)}
            if command == "G92":
                if "E" in params:
                    absolute_e_value = params["E"]
                if "X" in params:
                    x = params["X"]
                if "Y" in params:
                    y = params["Y"]
                if "Z" in params:
                    z = params["Z"]
                continue
            if command not in {"G0", "G1", "G2", "G3"}:
                continue

            nx = params.get("X", 0.0) + (0.0 if absolute_xyz and "X" in params else x)
            ny = params.get("Y", 0.0) + (0.0 if absolute_xyz and "Y" in params else y)
            nz = params.get("Z", 0.0) + (0.0 if absolute_xyz and "Z" in params else z)
            if "F" in params:
                feedrate = params["F"]
            if "E" not in params:
                delta_e = 0.0
            elif relative_e:
                delta_e = params["E"]
            else:
                delta_e = params["E"] - absolute_e_value
                absolute_e_value = params["E"]

            xy_moved = math.hypot(nx - x, ny - y) > 1e-9
            if xy_moved and delta_e <= 1e-9:
                break_path = True
            elif xy_moved and delta_e > 1e-9 and break_path:
                path += 1
                break_path = False

            self.moves.append(
                Move(
                    line_no=line_no,
                    command=command,
                    layer=max(layer, 0),
                    role=role,
                    block=block,
                    path=path,
                    x0=x,
                    y0=y,
                    z0=z,
                    x=nx,
                    y=ny,
                    z=nz,
                    e=delta_e,
                    feedrate=feedrate,
                    width=width,
                    height=move_height or layer_height,
                    wipe=wipe,
                )
            )
            x, y, z = nx, ny, nz

        if layer >= 0:
            self.layers.append(LayerInfo(layer, layer_z, layer_height))

        # Some CrealityPrint flavors emit ``;:<z>`` instead of ``;Z:<z>``.
        # Recover the physical print Z from extrusion moves so downstream
        # behavior checks do not depend on that malformed comment spelling.
        extrusion_z: dict[int, list[float]] = defaultdict(list)
        for move in self.moves:
            if move.is_extrusion:
                extrusion_z[move.layer].append(move.z)
        recovered: list[LayerInfo] = []
        for info in self.layers:
            z_value = info.z if info.z is not None else median(extrusion_z.get(info.index, []))
            recovered.append(LayerInfo(info.index, z_value, info.height))
        self.layers = recovered

    def extrusion_moves(self, roles: str | Iterable[str] | None = None) -> list[Move]:
        if roles is None:
            wanted = None
        elif isinstance(roles, str):
            wanted = {roles.lower()}
        else:
            wanted = {role.lower() for role in roles}
        return [
            move for move in self.moves
            if move.is_extrusion and (wanted is None or (move.role or "").lower() in wanted)
        ]

    def paths(self, roles: str | Iterable[str], *, min_length: float = 0.0) -> list[list[Move]]:
        grouped: dict[int, list[Move]] = defaultdict(list)
        for move in self.extrusion_moves(roles):
            grouped[move.path].append(move)
        return [moves for moves in grouped.values() if sum(m.xy_length for m in moves) >= min_length]

    def blocks(self, roles: str | Iterable[str]) -> list[list[Move]]:
        grouped: dict[int, list[Move]] = defaultdict(list)
        for move in self.extrusion_moves(roles):
            grouped[move.block].append(move)
        return list(grouped.values())

    def role_layers(self, roles: str | Iterable[str]) -> set[int]:
        return {move.layer for move in self.extrusion_moves(roles)}

    def layer_bounds(self, roles: str | Iterable[str]) -> dict[int, tuple[float, float, float, float]]:
        points: dict[int, list[tuple[float, float]]] = defaultdict(list)
        for move in self.extrusion_moves(roles):
            points[move.layer].extend(((move.x0, move.y0), (move.x, move.y)))
        return {
            layer: (
                min(x for x, _ in pts), max(x for x, _ in pts),
                min(y for _, y in pts), max(y for _, y in pts),
            )
            for layer, pts in points.items() if pts
        }

    def wipe_moves(self) -> list[Move]:
        return [move for move in self.moves if move.wipe and move.xy_length > 1e-9]

    def arc_count(self, roles: str | Iterable[str] | None = None) -> int:
        if roles is None:
            wanted = None
        elif isinstance(roles, str):
            wanted = {roles.lower()}
        else:
            wanted = {role.lower() for role in roles}
        return sum(
            move.command in {"G2", "G3"} and (wanted is None or (move.role or "").lower() in wanted)
            for move in self.moves
        )


def median(values: Iterable[float]) -> float | None:
    finite = [value for value in values if math.isfinite(value)]
    return statistics.median(finite) if finite else None


def percentile(values: Sequence[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * fraction)))
    return ordered[index]


def circular_distance_180(a: float, b: float) -> float:
    diff = abs((a - b) % 180.0)
    return min(diff, 180.0 - diff)


def path_length(path: Sequence[Move]) -> float:
    return sum(move.xy_length for move in path)


def path_signed_area(path: Sequence[Move]) -> float:
    if not path:
        return 0.0
    points = [(path[0].x0, path[0].y0), *((move.x, move.y) for move in path)]
    return 0.5 * sum(
        x0 * y1 - x1 * y0
        for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1])
    )


def path_bbox(path: Sequence[Move]) -> tuple[float, float, float, float] | None:
    if not path:
        return None
    points = [(path[0].x0, path[0].y0), *((move.x, move.y) for move in path)]
    return min(x for x, _ in points), max(x for x, _ in points), min(y for _, y in points), max(y for _, y in points)


def dominant_angle(moves: Iterable[Move], *, min_length: float = 0.5) -> float | None:
    weighted: list[tuple[float, float]] = []
    for move in moves:
        angle = move.angle
        if angle is not None and move.xy_length >= min_length:
            weighted.append((angle, move.xy_length))
    if not weighted:
        return None
    # Lines are axial (0 == 180), hence the doubled-angle mean.
    sx = sum(weight * math.cos(math.radians(2 * angle)) for angle, weight in weighted)
    sy = sum(weight * math.sin(math.radians(2 * angle)) for angle, weight in weighted)
    return (math.degrees(math.atan2(sy, sx)) / 2.0) % 180.0


def median_speed(moves: Iterable[Move], *, min_length: float = 0.5) -> float | None:
    return median(move.speed for move in moves if move.speed is not None and move.xy_length >= min_length)


def median_width(moves: Iterable[Move], *, min_length: float = 0.2) -> float | None:
    return median(move.width for move in moves if move.width is not None and move.xy_length >= min_length)


def median_height(moves: Iterable[Move], *, min_length: float = 0.2) -> float | None:
    return median(move.height for move in moves if move.height is not None and move.xy_length >= min_length)


def median_e_per_mm(moves: Iterable[Move], *, straight_only: bool = True) -> float | None:
    return median(
        move.e / move.xy_length
        for move in moves
        if move.xy_length >= 0.2 and move.e > 0 and (not straight_only or move.command in {"G0", "G1"})
    )


def nearest_distances(values: Sequence[float]) -> list[float]:
    ordered = sorted(set(round(value, 6) for value in values))
    return [b - a for a, b in zip(ordered, ordered[1:]) if b - a > 1e-6]
