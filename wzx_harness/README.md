# wzx_harness — 3DPrinter_Qt6 切片性能黑盒测试

P0 版。用 pytest 驱动 `owzx-cli`（3DPrinter_Qt6 的无头切片 CLI）逐模型跑
"加载 → 切片 → 导出"，计时并和持久基线 `data/baseline.csv` 对比：
状态位（崩溃/切片/导出）必须一致，总耗时增长 **>5% 且 ≥1000ms** 判回退
（对齐 C3DBaseline 的二次切片判定规则）。

- 被测对象是构建产物（CLI 可执行文件），不链接产品源码 → 包级黑盒
- Windows / Linux 双平台；基线按 `model + os` 分行，只做同平台对比
- 不含模型文件；模型目录运行时通过参数传入

## 运行

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# 首次运行（录制基线）
.venv/bin/pytest case \
  --slicer-exe /path/to/owzx-cli \
  --models-dir /path/to/models \
  --repeats 3 --case-timeout 1800 --update-baseline -v

# 日常对比（不加 --update-baseline，回退即红）
.venv/bin/pytest case --slicer-exe ... --models-dir ... --repeats 3 -v
```

也可以用环境变量 `OWZX_SLICER_EXE` / `OWZX_MODELS_DIR`（多个目录用 `:` 分隔）
代替命令行参数。`--models-dir` 可重复传多个目录；`--case-regex <正则>`
挑选子集（目录即分类，如 `--case-regex '^smoke/'`）。

## 产物（`artifacts/`，已 gitignore）

| 文件 | 内容 |
|---|---|
| `run_report.csv` | 本次每个模型一行：耗时/状态位/版本/错误 |
| `slice_summary.md` / `.json` | 回退/新基线/改善/持平 汇总表 |
| `<case>__*/` | 每次运行的 gcode 输出（临时目录） |

## 基线规则

- `data/baseline.csv` 每行一个 `model × os`；首跑自动录入，`--update-baseline` 重录
- 判同平台：`(model, os)` 相同才对比；换机器重录该行
- 状态位翻转（crashed/slice_ok/export_ok）直接判回退，不看耗时
- 改善时自动把更快成绩写回基线（避免"曾经很快"的假回退）

## 与 C3DBaseline 的关系

用例结构（参数化 + 目录即分类 + 正则选子集）、判定规则（5% + 1000ms 双门槛）、
产物形态（CSV + MD 汇总）均移植自 C3DBaseline；驱动层从 "TCP 命令后门" 换成
CLI 子进程调用，飞书下载器和 Windows 专用代码未移植。二次切片效率场景
（move 置脏 → 重切）留给 P1 的 `--benchmark-reslice`。

## 用例两套

- `case/test_slice.py` — 性能基线（计时/回退判定，见上文）
- `case/test_stages.py` — **切片流程阶段覆盖**（对应 CrealityPrint GUI 的切片进度条文案）：
  强制 `--enable_support 1` 切片后断言：
  1. 核心阶段齐全且骨干有序：Preparing slice → Slicing mesh → Generating walls →
     Optimizing toolpath → Generating G-code → Slice complete
  2. 支撑阶段真实运行（Generating support / Checking support necessity 二选一）
     + 悬空检测（Detect overhangs）
  3. 逐层进度单调、不虚报（progress ≤ slice finished layers，且 ≥90%）
  4. G-code 文件自洽：LAYER_CHANGE 数 == 文件头 total layer number ≤ 计划层数
  5. 走线类型齐全且支撑真实出料：SUPPORT / SUPPORT INTERFACE 长度 > 0
     （对应 GUI 预览的走线类型表：内墙/外墙/支撑/支撑界面/桥接…）
  6. 软检查：estimated printing time / filament used 统计块存在；
     多物体冲突警告（GUI 功能，CLI 不触发，仅记录）

  ⚠️ 用例假定模型有悬空（如 `bench_overhang_tower.stl`）；球体等无悬空模型
  不会生成支撑，会在此用例上失败——模型库请把无悬空模型排除在本用例外。

## 已知问题（来自 P0 验证过程）

- `3DPrinter_Qt6/build/r7_model.stl`（684 字节）会让 owzx-cli 静默死锁
  （加载后 futex 永久等待）——模型文件或 STL 解析疑有 bug，待查
- **内存分级**：C3DBaseline 的 `maorongxiong.3mf`（407 层多板模型）切片
  G-code 生成阶段峰值内存 ~30GB，31GB 内存的机器直接 OOM（内核击杀
  owzx-cli）。这类重型模型归入 `models/heavy/`，只在大内存测试机上跑；
  冒烟集必须选在本机内存安全范围内
- OOM 时 harness 记 `crashed=True` 并判回退——这是期望行为：模型在
  CI 机上炸内存应当红
