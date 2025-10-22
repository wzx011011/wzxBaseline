from __future__ import annotations
import os
import time

import pytest

# 动态参数化配置
def pytest_generate_tests(metafunc):
    from ...conftest import parametrize
    parametrize(
    metafunc,
    {
        "test_engine_case": {"engine_case_item": "engine_case"},
        "test_precision": {
            "efc_case": "elefant_foot_compensation",
            "efc_layers_case": "elefant_foot_compensation_layers",
        },
    },
    )


