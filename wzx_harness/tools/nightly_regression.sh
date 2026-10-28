#!/bin/bash
# nightly_regression.sh — wzx_harness 夜间全量回归
#
# 建议安装（crontab -e）：
#   30 2 * * *  /home/admins/公共/CP/C3DBaseline/wzx_harness/tools/nightly_regression.sh >> /home/admins/公共/CP/C3DBaseline/wzx_harness/artifacts/nightly_cron.log 2>&1
#
# 行为：
#   1. git pull 两仓库（3DPrinter_Qt6 + wzxBaseline）
#   2. 增量重编 owzx-cli（有变更才编译）
#   3. Linux 门禁（14 套件）
#   4. 模型池全量回归（46 模型 × 双引擎，基线对比，回退即红）
#   5. 结果写入 artifacts/nightly_<date>/，失败非零退出

set -u
HARNESS="/home/admins/公共/CP/C3DBaseline/wzx_harness"
QT_REPO="/home/admins/公共/CP/3DPrinter_Qt6"
DATE=$(date +%Y%m%d)
OUT="$HARNESS/artifacts/nightly_$DATE"
mkdir -p "$OUT"

echo "[$(date '+%F %T')] 1/4 git pull"
git -C "$QT_REPO" pull --ff-only origin feature/lan-printers >/dev/null 2>&1 || echo "  (QT pull skipped/failed — 继续用本地)"
git -C "$HARNESS" pull --ff-only github feature/wzx-harness >/dev/null 2>&1 || echo "  (harness pull skipped/failed — 继续用本地)"

echo "[$(date '+%F %T')] 2/4 增量重编 owzx-cli"
cmake --build "$QT_REPO/build" --target owzx-cli -j12 > "$OUT/build.log" 2>&1 || {
  echo "BUILD FAILED"; exit 2; }

echo "[$(date '+%F %T')] 3/4 Linux 门禁"
bash "$QT_REPO/scripts/verify_linux.sh" > "$OUT/gate.log" 2>&1
GATE_RC=$?
echo "门禁 rc=$GATE_RC"

echo "[$(date '+%F %T')] 4/4 模型池回归（46 模型 × 双引擎）"
cd "$HARNESS"
.venv/bin/pytest case/test_slice.py \
  --slicer-exe "$QT_REPO/build/owzx-cli" \
  --orca-exe "$QT_REPO/third_party/OrcaSlicer/build/src/orca-slicer" \
  --models-dir /home/admins/公共/CP/wzx_models \
  --case-timeout 1800 -v > "$OUT/regression.log" 2>&1
REG_RC=$?

cp "$HARNESS/artifacts/run_report.csv" "$OUT/" 2>/dev/null
cp "$HARNESS/artifacts/slice_summary.md" "$OUT/" 2>/dev/null

PASSED=$(grep -cE "PASSED" "$OUT/regression.log" 2>/dev/null || echo 0)
FAILED=$(grep -cE "FAILED" "$OUT/regression.log" 2>/dev/null || echo 0)
echo "[$(date '+%F %T')] 完成: 门禁=$GATE_RC 回归 PASS=$PASSED FAIL=$FAILED → $OUT"

# 门禁或回归任一失败 → 非零退出（供监控报警）
[ $GATE_RC -eq 0 ] && [ $REG_RC -eq 0 ] || exit 1
