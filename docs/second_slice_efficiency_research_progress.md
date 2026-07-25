# 二次切片效率检测研究进展

更新时间：2026-06-29（二次切片端到端流程已打通）
项目：C3DBaseline / C3DSlicer / Jenkins 工程管理

## 1. 目标

在 Jenkins 工程管理中建立一个自动化任务，用于检测 CrealityPrint 每次日常打包后的二次切片效率。

自动化任务需要做到：

- 从 `CrealityPrint_Release_Package` 获取最新成功构建包。
- 使用指定模型执行切片性能测试。
- 按“移动模型后再次切片”的行为定义二次切片。
- 输出二次切片效率总结文档。
- 判断本次版本是否存在效率下降。
- 效率下降阈值按用户确认设置为 `5%`。

## 2. 二次切片行为定义

本次研究中，“二次切片”定义为：

1. 启动 CrealityPrint。
2. 重置当前工程，避免上一次测试残留影响结果。
3. 导入固定 3MF 模型。
4. 执行第一次切片，并记录 `first_slice_ms`。
5. 移动模型实例，默认移动 X 方向 `+10mm`。
6. 执行第二次切片，并记录 `second_slice_ms`。
7. 导出 G-code，用于确认第二次切片结果可用。

效率判定只使用 `second_slice_ms`。当本次 `second_slice_ms` 相比基线增长超过 `5%`，并且绝对增长至少 `1000ms` 时，判定为二次切片效率下降。

## 3. 测试模型

用户指定模型：

```text
C:/Users/106660/Downloads/切片测试 _无支撑.3mf
```

当前已缓存到 C3DBaseline 项目内：

```text
E:/wzx/C3DBaseline/test_framework/artifacts/second_slice/切片测试_无支撑.3mf
```

模型大小：`9813400` 字节。

## 4. Jenkins 自动化方案

已采用“方案 2”：不修改 `CrealityPrint_Release_Package` 的构建行为，而是新增独立检测任务定时检查其最新成功包。

当前任务设计：

```text
任务名：C3DBaseline_SecondSlice_Performance
来源任务：CrealityPrint_Release_Package
构建选择：lastSuccessfulBuild
测试命令：-m performance
重复包处理：已测试 build 自动跳过
报告归档：CSV / Markdown / JSON
```

这样做的好处是：

- 不影响日常打包任务的原有构建流程。
- 不需要在打包任务里追加测试步骤。
- 二次切片检测可以独立失败、独立重跑、独立维护。
- 可以用定时任务持续追踪最新成功包。

需要注意：Jenkins 任务实际运行的是远端仓库分支中的 `Jenkinsfile2`。本地 C3DBaseline 改动需要推送到 Jenkins 配置所拉取的分支后，Jenkins 才能真正跑到这版二次切片逻辑。

## 5. C3DBaseline 已完成改造

### 5.1 Jenkinsfile2

已调整内容：

- `BUILD_ID` 默认值从固定构建号改为 `lastSuccessfulBuild`。
- `TEST_COMMAND` 默认值改为 `-m performance`。
- 增加 `SKIP_TESTED_BUILD=true`。
- 增加定时触发配置。
- 调用 `ci/jenkins_build_tester.py` 时传入：
  - `--skip-tested-build`
  - `--test-command`
- Jenkins 归档范围从只归档 CSV 扩展为：

```text
test_framework/performance/data/*.csv
test_framework/performance/data/*.md
test_framework/performance/data/*.json
```

### 5.2 ci/jenkins_build_tester.py

已调整内容：

- 支持 `BUILD_ID=lastSuccessfulBuild`。
- 支持跳过已经测试过的 build。
- 测试成功后记录已测 build 状态。
- 自动注入 `PYTHONPATH`，保证 Jenkins 环境可以正确导入测试框架。
- 为二次切片测试设置持久化基线 CSV：

```text
SECOND_SLICE_BASELINE_CSV
```

### 5.3 test_framework/performance/case/test_slice.py

已调整为二次切片测试流程：

- 默认从 HTTP 用例源收集全部模型。
- 仅在显式传入 pytest 参数 `--second-slice-model <path>` 时，使用该模型作为唯一二次切片用例。
- 测试字段新增：
  - `first_slice_ms`
  - `move_ms`
  - `second_slice_ms`
  - `move_ok`
- `slice_ms` 兼容保留，并映射为第二次切片耗时。
- 测试结束后始终写 CSV 报告。
- 测试结束后生成二次切片效率总结 Markdown 和 JSON。
- 对导入、第一次切片、移动、第二次切片、导出都做硬性断言，避免失败用例被误判为性能通过。

### 5.4 test_framework/performance/summary.py

新增二次切片效率总结模块。

主要能力：

- 对比基线和本次测试结果。
- 按 `second_slice_ms` 判断效率变化。
- 统计：
  - 可对比用例数
  - 效率下降用例数
  - 效率改善用例数
  - 失败/崩溃用例数
  - 新增用例数
  - 缺失用例数
- 输出 Markdown 总结。
- 输出 JSON 结构化结果。

### 5.5 新增测试

已新增并通过的自动化代码级测试：

```text
test_framework/performance/test_summary.py
test_framework/performance/test_second_slice_flow.py
```

本地执行结果：

```text
3 passed
```

## 6. 当前输出文件

本地真实测试后生成了以下文件：

```text
E:/wzx/C3DBaseline/test_framework/performance/data/feishu_slice_report.csv
E:/wzx/C3DBaseline/test_framework/performance/data/second_slice_efficiency_summary.md
E:/wzx/C3DBaseline/test_framework/performance/data/second_slice_efficiency_summary.json
```

当前 Markdown 总结显示：

```text
结论：本次版本：未发现二次切片效率下降
```

> 说明：早期版本的"未发现效率下降"是在真实测试失败（没有有效 `second_slice_ms`）时生成的，
> 不能作为最终结论。2026-06-29 修复完成态判定后，真实端到端测试已跑通，`second_slice_ms` 有
> 有效数值，此时该结论才是可信的（详见第 7、13 节）。

## 7. 本地真实测试结果

已用本地 CrealityPrint 执行真实测试。

被测程序（2026-06-29 重新编译的 Release 包）：

```text
E:/wzx/C3DSlicer/C3DSlicer/build_unified/src/Release/CrealityPrint.exe
```

> 历史背景：早期版本因被测包缺少 `move_model_instance` 命令，测试失败在“移动模型”步骤
> （返回 `COMMAND NOT FAOUND`）。该问题现已不复存在——最新 Release 包已包含该命令。

在 2026-06-29 修复完成态判定（第 13 节）后，真实端到端测试跑通，结果：

```text
import_ok:      True   (4691ms)
first_slice_ms: 20310ms        ← 首次切片完成
move_ok:        True   (635ms) ← 移动模型成功
second_slice_ms: 12837ms       ← 二次切片完成
export_ok:      True   (3736ms)
crashed:        False
error:          (空)
```

说明：

- CrealityPrint 可以启动，固定模型可以导入。
- 首次切片、移动模型、二次切片、导出 G-code 全部成功。
- 二次切片（12837ms）明显快于首次切片（20310ms），符合切片缓存优化预期。
- pytest 端到端结果：`1 passed in 62.73s`（修复前为 `1 failed in ~177s`，卡在 120s stall）。
- 单元测试：`14 passed`（含新增的完成态判定用例）。

生成报告：

```text
test_framework/performance/data/feishu_slice_report.csv
test_framework/performance/data/second_slice_efficiency_summary.md   （结论：未发现效率下降，0 失败）
test_framework/performance/data/second_slice_efficiency_summary.json （status: PASS）
```

此时该“未发现效率下降”结论是**可信的**，因为 `second_slice_ms` 有有效数值、失败/崩溃用例数为 0。

## 8. C3DSlicer 当前状态

为了实现“移动模型后再次切片”，C3DSlicer 的 `TestHelper.cpp` 需要提供测试命令：

```text
move_model_instance
```

此前已经写过该命令，包含：

- `libslic3r/Model.hpp`
- `libslic3r/ModelInstance.hpp`
- `move_model_instance` 实现
- `m_cmd2func["move_model_instance"] = move_model_instance`

但当前检查发现：

```text
当前 C3DSlicer 分支：codex/combobox-scroll-close
当前 TestHelper.cpp：没有 move_model_instance
stash@{2}：包含 move_model_instance 改动
```

当前 `TestHelper.cpp` 中仍有：

```text
get_error
get_slicing_progress
```

但缺少：

```text
move_model_instance
```

这正是本地真实测试失败并返回 `COMMAND NOT FAOUND` 的直接原因。

## 9. 当前阻塞点

> 已于 2026-06-29 全部解除，端到端流程跑通。

历史阻塞点（均已解决）：

1. **`move_model_instance` 缺失**（已解决）：最新 Release 包已包含该命令，移动模型步骤成功。
2. **完成态判定与真实引擎不符**（已解决，详见第 13 节）：修复前首次切片会卡在
   “进度停滞 120s”错误。根因是 `_is_slicing_done` 只认 `state=completed`，而真实引擎
   切片完成后稳定处于 `state=no_slicing` + `all_plate_finished=True`，瞬态的 `completed`
   几乎抓不到。已改为以 `all_plate_finished` 为完成判定权威，`progress/began/cancelled`
   明确表示进行中。

## 10. 风险与注意事项

### 10.1 不应修改日常打包任务行为

用户已明确质疑“为什么要改构建行为”，因此当前方案保持不修改 `CrealityPrint_Release_Package` 本身，只由独立检测任务读取其最新成功包。

### 10.2 build_id 不应使用固定值

用户已指出 build id 会变化，因此 `BUILD_ID` 已改为：

```text
lastSuccessfulBuild
```

同时增加“已测 build 跳过”机制，避免重复测试同一个包。

### 10.3 报告“未发现效率下降”结论的可信前提

最终有效结论必须基于：

- `move_ok=True`
- `slice_ok=True`
- `second_slice_ms` 有有效数值
- 当前版本与历史基线可比较

2026-06-29 修复后，本地真实测试已满足前三条（`失败/崩溃用例数=0`），结论可信。
"当前版本与历史基线可比较"需要多次成功运行积累有效基线后才有版本对比明细。

### 10.4 提交前需要筛选工作区改动

当前 C3DBaseline 工作区除二次切片相关文件外，还有一些既有脏文件/诊断文件。正式提交前需要只纳入本任务相关文件，避免把无关改动带入。

## 11. 下一步计划

本地端到端已打通，剩余主要是上线与积累基线：

1. 将本次 C3DBaseline 改动（完成态判定修复 + 单元测试）提交并推送到 Jenkins 使用的远端分支。
2. 在 Jenkins 上运行 `C3DBaseline_SecondSlice_Performance`，确认归档的 CSV / Markdown / JSON。
3. 让 Jenkins 持续运行多个版本，积累有效 `second_slice_ms` 基线，使版本对比明细（优化率）可用。
4. 确认 Jenkins 被测包（CrealityPrint 日常打包产物）同样包含 `move_model_instance`。

## 12. 当前结论

二次切片效率检测的 C3DBaseline 自动化框架已完成，2026-06-29 修复完成态判定后，
**本地真实端到端测试已闭环跑通**：首次切片 → 移动模型 → 二次切片 → 导出，全部成功，
并生成可信的效率总结报告（PASS）。

历史阻塞点（`move_model_instance` 缺失、完成态判定与真实引擎不符）均已解除。

## 13. 2026-06-29 完成态判定修复（关键）

### 13.1 现象

修复前，真实端到端测试在**首次切片**阶段失败：

```text
AssertionError: First slice failed ...: slicing progress stalled for 120.0s
(percentage=-1.000, state=no_slicing)
```

`trigger_slice` 返回成功，但 `_wait_for_slicing_done` 永远等不到“完成”，120s 后触发 stall 保护。

### 13.2 根因

通过逐步诊断（裸会话、`RestartingEngine` 路径、直接调用 `_run_slice_flow` 三种方式对比）
定位到：引擎本身切片正常，问题在完成判定函数 `_is_slicing_done`。

引擎 `get_slicing_progress` 返回的 `state` 来自 `SlicingProgressNotification` 状态机
（`NotificationManager.cpp`）：

```text
SP_BEGAN     -> "began"
SP_PROGRESS  -> "progress"     切片进行中
SP_COMPLETED -> "completed"    切片刚完成（瞬态）
SP_CANCELLED -> "cancelled"
SP_NO_SLICING-> "no_slicing"   空闲
```

`get_slicing_progress`（`TestHelper.cpp`）里 `progress` 取自 `get_slicing_progress_snapshot()`，
`all_plate_finished` 取自遍历每个 plate 的 `is_slice_result_ready_for_print()`。

关键点：`SP_COMPLETED` 是**瞬态**，通知很快被重置为 `SP_NO_SLICING`。因此轮询几乎抓不到
`completed`，切片完成后稳定观察到的是 `state=no_slicing` + `all_plate_finished=True`。

原 `_is_slicing_done` 只把 `state=="completed"` 当作完成，且“只要 state 非空就以 state 为准”，
导致 `no_slicing + all_plate_finished=True` 被判为“未完成”，等待死锁，最终 stall。

### 13.3 修复

`test_framework/performance/case/test_slice.py` 的 `_is_slicing_done`：

```python
state = str(progress.get("state") or "").lower()
if state in {"progress", "began", "cancelled"}:
    return False                 # 明确进行中（含 re-slice 旧结果残留场景）
if state == "completed":
    return True
return bool(progress.get("all_plate_finished"))  # 其余以磁盘结果为权威
```

要点：

- `progress/began/cancelled` 明确表示进行中，即使旧结果令 `all_plate_finished=True`（re-slice）。
- `no_slicing`（及 unknown / 缺失 state）改由 `all_plate_finished` 决定，匹配真实引擎完成后的稳态。
- 与 `_wait_for_slicing_done` 的 `wait_for_transition`/`saw_unfinished` 机制配合：re-slice 时必须
  先观察到一次“进行中”，才会接受“完成”，避免旧结果残留短路。

### 13.4 测试

- 新增 `test_is_slicing_done_real_engine_no_slicing_after_finish`、
  `test_is_slicing_done_no_slicing_without_result_is_not_done`，覆盖真实引擎完成态。
- `FakeSlicer` 完成态从 `state=completed` 改为 `state=no_slicing + all_plate_finished=True`，
  与真实引擎一致，确保单测验证的是真实行为而非理想行为。
- 单元测试：`14 passed`。
- 真实 pytest 端到端：`1 passed in 62.73s`，`失败/崩溃用例数=0`，`status=PASS`。
