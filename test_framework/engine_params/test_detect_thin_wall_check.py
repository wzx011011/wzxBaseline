from pathlib import Path
from types import SimpleNamespace

import pytest

from engine_params.src.gcode.constants import ExtrusionType
from engine_params.src.gcode.process.strength import walls_check


class _FakeParser:
    def __init__(self, enabled: bool, path_count: int):
        self.enabled = enabled
        self.path_count = path_count

    def load_config(self):
        return {"detect_thin_wall": SimpleNamespace(value=int(self.enabled))}

    def get_type_contours_per_layer(self, **_kwargs):
        region = SimpleNamespace(paths=[object() for _ in range(self.path_count)])
        return [
            SimpleNamespace(
                index=1,
                regions={0: {ExtrusionType.OUTER_WALL.value: region}},
            )
        ]


@pytest.mark.parametrize(
    ("enabled", "path_count"),
    [(True, 2), (False, 1)],
)
def test_parse_detect_thin_wall_uses_model_path_count(monkeypatch, tmp_path: Path, enabled, path_count):
    gcode = tmp_path / "case.gcode"
    gcode.write_text("; test\n", encoding="utf-8")
    parser = _FakeParser(enabled, path_count)
    monkeypatch.setattr(walls_check, "GCodeParserEx", lambda _path: parser)

    ok, _, details = walls_check.parse_detect_thin_wall(gcode, enabled)

    assert ok
    assert details["config_on"] is enabled
    assert details["actual_on"] is enabled
