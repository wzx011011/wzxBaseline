
import sys
import pytest

# 读取排除列表
with open(r"C:\Users\106660\AppData\Local\Temp\tmpev9475nq.txt", "r", encoding="utf-8") as f:
    deselected = [line.strip() for line in f if line.strip()]

# 构建参数
args = ["engine_params/case/params/", "-v", "--tb=line"]
for test in deselected:
    args.extend(["--deselect", test])

# 运行pytest
sys.exit(pytest.main(args))
