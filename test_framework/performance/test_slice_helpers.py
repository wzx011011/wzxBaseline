from test_framework.performance.case.test_slice import (
    _MAX_GCODE_CASE_COMPONENT_LENGTH,
    _http_list_links,
    _sanitize_path_component,
)


def test_sanitize_path_component_limits_long_pytest_nodeid_with_stable_hash():
    nodeid = "performance/case/test_slice.py::test_feishu_slice[" + "very-long-case-" * 30 + ".3mf]"

    sanitized = _sanitize_path_component(nodeid)

    assert len(sanitized) == _MAX_GCODE_CASE_COMPONENT_LENGTH
    assert sanitized == _sanitize_path_component(nodeid)
    assert sanitized.startswith("performance_case_test_slice.py_test_feishu_slice_")


def test_sanitize_path_component_keeps_long_nodeids_distinct():
    common = "performance/case/test_slice.py::test_feishu_slice[" + "same-prefix-" * 30

    assert _sanitize_path_component(common + "a.3mf]") != _sanitize_path_component(common + "b.3mf]")


def test_http_list_links_unescapes_html_entities_in_href():
    page_html = (
        '<a href="Netflix+&amp;+Chill+Ticket+3MF.3mf">first</a>'
        '<a href="folder/Mage&#38;Slice.3mf">second</a>'
    )

    assert _http_list_links(page_html) == [
        "Netflix+&+Chill+Ticket+3MF.3mf",
        "folder/Mage&Slice.3mf",
    ]
