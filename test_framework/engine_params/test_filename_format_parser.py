from pathlib import Path

from engine_params.src.gcode.process.others import gcode_output_check


DEFAULT_FORMAT = (
    "{input_filename_base}_{filament_type[initial_tool]}_{print_time}.gcode"
)


class _ConfigParser:
    def __init__(self, _: Path, filename_format: str):
        self.filename_format = filename_format

    def load_config(self) -> dict[str, str]:
        return {"filename_format": self.filename_format}


def test_filename_format_expands_72_default_placeholders(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        gcode_output_check,
        "GCodeParser",
        lambda path: _ConfigParser(path, DEFAULT_FORMAT),
    )

    ok, actual, details = gcode_output_check.parse_filename_format(
        tmp_path / "plate_1.gcode", DEFAULT_FORMAT
    )

    assert ok
    assert actual == DEFAULT_FORMAT
    assert details["sample_expanded_filename"] == "behavior_model_PLA_1h2m.gcode"
    assert details["unresolved_placeholders"] == []


def test_filename_format_rejects_unknown_placeholder(
    monkeypatch, tmp_path: Path
) -> None:
    invalid_format = "{input_filename_base}_{unknown}.gcode"
    monkeypatch.setattr(
        gcode_output_check,
        "GCodeParser",
        lambda path: _ConfigParser(path, invalid_format),
    )

    ok, _, details = gcode_output_check.parse_filename_format(
        tmp_path / "plate_1.gcode", invalid_format
    )

    assert not ok
    assert details["unresolved_placeholders"] == ["{unknown}"]
