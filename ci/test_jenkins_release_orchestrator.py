import io
import os
import sys

from ci.jenkins_release_orchestrator import run_tests


def test_run_tests_survives_stdout_encoding_errors(tmp_path, monkeypatch):
    class AsciiOnlyStdout(io.StringIO):
        encoding = "ascii"

        def write(self, text):
            text.encode(self.encoding)
            return super().write(text)

    fake_stdout = AsciiOnlyStdout()
    monkeypatch.setattr(sys, "stdout", fake_stdout)
    script = tmp_path / "emit_utf8.py"
    script.write_text("import sys\nsys.stdout.buffer.write(bytes([0xc6, 0xac, 0x0a]))\n", encoding="utf-8")

    outcome = run_tests(
        f'"{sys.executable}" "{script}"',
        env=os.environ.copy(),
        cwd=tmp_path,
    )

    assert outcome.status == "SUCCESS"
    assert outcome.return_code == 0
    assert "\\u01ac" in fake_stdout.getvalue()


def test_run_tests_sequence_does_not_invoke_shell(tmp_path):
    outcome = run_tests(
        [sys.executable, "-c", "import sys; print(sys.argv[1])", "left|right"],
        env=os.environ.copy(),
        cwd=tmp_path,
    )

    assert outcome.status == "SUCCESS"
    assert outcome.output.strip() == "left|right"
