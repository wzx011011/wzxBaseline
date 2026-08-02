# Jenkins 构建性能趋势报告

`CrealityPrint_Tester` 会为 performance 用例保存被测 exe 的分阶段耗时，并生成不依赖外部前端库的 HTML/SVG 报告。

## Jenkins 参数

- `BUILD_ID`：被测 `CrealityPrint_Release_Package_pipeline` 构建号，也是折线图横轴；可以使用 `lastSuccessfulBuild`。
- `PERFORMANCE_HISTORY_BUILDS`：保留最近多少次 Tester 运行，默认 `50`。
- `PERFORMANCE_REGRESSION_PERCENT`：首次切片相对上一有效构建的下降阈值，默认 `10`。
- `PERFORMANCE_MIN_DELTA_MS`：首次切片绝对下降阈值，默认 `2000ms`。

只有相对变化和绝对变化同时达到阈值时，报告才标记为 `REGRESSION`。失败、崩溃或缺少首次切片耗时的最新结果标记为 `INVALID`，不会把超时时间当作真实性能数据。

## Jenkins 归档产物

- `performance_run.csv`：本次运行的逐用例数据，使用标准 CSV 转义。
- `performance_run.json`：本次运行的结构化数据。
- `performance_history.json`：当前保留窗口内的完整历史快照。
- `performance_trend.html`：可搜索、可按状态筛选的总览页。
- `performance_charts/*.svg`：每个用例一张折线图，包含阶段合计、导入、首次切片、二次切片和导出耗时；鼠标悬停数据点可查看 BUILD_ID 和精确耗时。

在 Jenkins 构建页面进入 `Artifacts`，打开 `test_framework/performance/data/performance_trend.html`。点击模型名称可查看该用例的详细折线图。

## 历史保存方式

持久历史默认存放在 Jenkins workspace 的：

```text
artifacts/tested_builds/<source_job>_<platform>_performance_history.json
```

每次报告同时归档一份历史快照。当前方案依赖同一个 Jenkins agent/workspace 继续运行；如果任务启用了每次清理 workspace，趋势会从当前构建重新开始，需要将历史文件恢复到上述路径。

## 数据字段

每条记录包含源任务、源 `BUILD_ID`、Tester 构建号、执行节点、平台、exe 版本、用例名称、各阶段耗时、状态和错误。`total_ms` 是已测阶段耗时之和，不包含 pytest 初始化和清理时间。
