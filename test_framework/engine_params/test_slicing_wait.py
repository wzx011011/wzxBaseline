from concurrent.futures import Future
from pathlib import Path
from types import SimpleNamespace

import pytest

from engine_params.conftest import slice_and_export
from engine_params.src.slicerctl.slicing import SlicingWaitTimeout, wait_for_slicing_done


def _completed_future(value):
    future = Future()
    future.set_result(value)
    return future


class FakeInjector:
    def __init__(self, progress_states, output: Path | None = None):
        self.progress_states = iter(progress_states)
        self.output = output
        self.commands = []
        self.slice_completed = False

    def submit(self, command, payload, **_kwargs):
        self.commands.append(command)
        if command == "get_slicing_progress":
            progress = next(self.progress_states)
            self.slice_completed = bool(progress.get("all_plate_finished"))
            return _completed_future(
                {
                    "code": 0,
                    "payload": {
                        "all_plate_finished": progress.get("all_plate_finished"),
                        "progress": {
                            "state": progress.get("state"),
                            "percentage": progress.get("percentage"),
                        },
                    },
                }
            )
        if command == "export_gcode":
            assert self.slice_completed, "export happened before slicing completed"
            output = Path(payload["output"])
            output.write_text("; generated G-code\nG1 X1 Y1\n", encoding="utf-8")
        return _completed_future({"code": 0, "payload": {}})


def test_wait_for_slicing_done_observes_progress_transition():
    injector = FakeInjector(
        [
            {"state": "progress", "percentage": 25, "all_plate_finished": False},
            {"state": "no_slicing", "percentage": 100, "all_plate_finished": True},
        ]
    )

    progress = wait_for_slicing_done(injector, timeout=1, poll_interval=0)

    assert progress["all_plate_finished"] is True
    assert injector.commands == ["get_slicing_progress", "get_slicing_progress"]


def test_wait_for_slicing_done_times_out_when_never_complete():
    class NeverDoneInjector:
        def submit(self, command, _payload, **_kwargs):
            assert command == "get_slicing_progress"
            return _completed_future(
                {
                    "code": 0,
                    "payload": {
                        "all_plate_finished": False,
                        "progress": {"state": "progress", "percentage": 10},
                    },
                }
            )

    with pytest.raises(SlicingWaitTimeout, match="slicing not finished"):
        wait_for_slicing_done(
            NeverDoneInjector(),
            timeout=0.02,
            poll_interval=0.001,
            stall_timeout=0,
        )


def test_slice_and_export_exports_only_after_slicing_completed(tmp_path: Path):
    model = tmp_path / "case.3mf"
    model.write_bytes(b"3mf")
    output = tmp_path / "case.gcode"
    injector = FakeInjector(
        [
            {"state": "began", "percentage": 0, "all_plate_finished": False},
            {"state": "progress", "percentage": 70, "all_plate_finished": False},
            {"state": "no_slicing", "percentage": 100, "all_plate_finished": True},
        ],
        output=output,
    )
    request = SimpleNamespace(
        param={
            "input_3mf": str(model),
            "output_gcode": str(output),
            "timeouts": {"slice": 1, "poll": 0, "stall": 0, "wait": 1, "settle": 0.01},
        }
    )

    result = slice_and_export.__wrapped__(request, injector, lambda: output)

    assert result == output
    assert output.stat().st_size > 0
    assert "click_button" in injector.commands
    assert "trigger_slice" not in injector.commands
    assert injector.commands.index("export_gcode") > max(
        index for index, command in enumerate(injector.commands) if command == "get_slicing_progress"
    )
