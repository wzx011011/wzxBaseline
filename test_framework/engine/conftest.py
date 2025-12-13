from __future__ import annotations
import os
import time

import pytest

# 动态参数化配置
def pytest_generate_tests(metafunc):
    from test_framework.conftest import parametrize
    parametrize(
        metafunc, 
        {
            "test_performance_open": { # py name, such as   test_3mf_basic.py => test_3mf_basic
                "reopen_item": "reopen", # variable name : baseline key name
            }
        }
    )

