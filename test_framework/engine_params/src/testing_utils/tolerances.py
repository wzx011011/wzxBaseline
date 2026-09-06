"""Explicit tolerances for emitted G-code snapshot comparisons."""

# XYZ coordinates are emitted at 0.001 mm precision. Allow one output quantum
# per coordinate, plus arithmetic noise (e.g. 110.921 - 110.920 > 0.001).
# This is opt-in for coordinate snapshots, not configuration/count/angle tests.
GCODE_COORDINATE_TOLERANCE_MM = 0.001 + 1e-9
