from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple

from engine_params.src.gcode.GCodeParser import GCodeParser

_PRINT_SEQUENCE_ALIASES: Dict[str, str] = {
    "by object": "by object",
    "by objects": "by object",
    "逐件打印": "by object",
    "逐件": "by object",
    "逐件打印模式": "by object",
    "by layer": "by layer",
    "by layers": "by layer",
    "逐层打印": "by layer",
    "逐层": "by layer",
}


def _normalize_sequence(value: object | None) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    return _PRINT_SEQUENCE_ALIASES.get(text, text)


def parse_print_sequence(
        gcode_path: Path | str,
        expected_sequence: Optional[str] = None,
) -> Tuple[bool, Optional[str], Dict[str, object]]:
    """Inspect configuration and geometry to determine print sequence."""
    parser = GCodeParser(Path(gcode_path))
    cfg = parser.load_config()
    layers = parser.extract_layers()

    is_monotonic = True
    last_z: Optional[float] = None
    for z, _ in layers:
        if last_z is not None and (z + 1e-6) < last_z:
            is_monotonic = False
            break
        last_z = z

    detected_sequence = "by layer" if is_monotonic else "by object"

    raw_sequence = cfg.get("print_sequence")
    normalized_config = _normalize_sequence(raw_sequence)
    normalized_expected = _normalize_sequence(expected_sequence) if expected_sequence is not None else None

    if normalized_expected is None:
        ok = True
    else:
        ok = detected_sequence == normalized_expected

    details: Dict[str, object] = {
        "raw_print_sequence": raw_sequence,
        "normalized_print_sequence": normalized_config,
        "detected_sequence": detected_sequence,
        "expected_sequence": normalized_expected,
        "is_monotonic_z": is_monotonic,
        "layers_count": len(layers),
        "first_layer_print_sequence": cfg.get("first_layer_print_sequence"),
        "other_layers_print_sequence": cfg.get("other_layers_print_sequence"),
    }

    return ok, detected_sequence, details
