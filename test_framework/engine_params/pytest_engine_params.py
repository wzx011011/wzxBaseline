def pytest_addoption(parser):
    grp = parser.getgroup("slicer")
    grp.addoption("--slicer-exe", help="CrealityPrint.exe path (higher priority than CREALITY_PRINTER_PATH)")
    grp.addoption("--slicer-datadir", default="", help="Isolated CrealityPrint data directory for this test run")
    grp.addoption("--slicer-log", default="slicer_stdout.log")
    grp.addoption("--slicer-host", default="127.0.0.1")
    grp.addoption("--slicer-port", type=int, default=12345)
    grp.addoption("--slicer-timeout", type=float, default=30.0)
    grp.addoption("--slicer-inter-delay", type=float, default=0.20)
    grp.addoption("--slicer-retries", type=int, default=1)
    grp.addoption("--slicer-backoff", type=float, default=0.5)
    grp.addoption(
        "--slicer-arg",
        action="append",
        default=[],
        help="Append slicer CLI arg (can be used multiple times)",
    )
    grp.addoption(
        "--slicer-args-str",
        default="",
        help="Space-separated slicer CLI args, merged with --slicer-arg",
    )

    grp.addoption(
        "--gcode-root",
        default=r"D:\C3DBaseline\test_framework\engine_params\output",
        help="G-code output root",
    )
    grp.addoption(
        "--gcode-scope",
        choices=["function", "module", "session"],
        default="module",
        help="Auto allocate output sub-directory by scope",
    )
    grp.addoption(
        "--clean-gcode",
        action="store_true",
        default=False,
        help="Clean generated G-code after tests",
    )
    grp.addoption(
        "--engine-unavail",
        choices=("skip", "xfail", "error"),
        default="xfail",
        help="How to handle engine unavailable: xfail/skip/error",
    )

    grp.addoption(
        "--feishu-case-regex",
        dest="feishu_case_regex",
        default="",
        help="3MF case regex filter; higher priority than FEISHU_CASE_REGEX",
    )
    grp.addoption(
        "--feishu-notify",
        dest="feishu_notify",
        choices=("on", "off"),
        default="",
        help="Enable/disable Feishu post-test notification; higher priority than FEISHU_NOTIFY",
    )
