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

## Orca 对比（--orca-exe）实测记录（2026-10-23，Linux）

同模型双引擎对比首次实测（OrcaSlicer 2.5.0-dev CLI，源码同源子模块构建）：

| 模型 | owzx(ms) | Orca(ms) | owzx/Orca |
|---|---:|---:|---:|
| hotend.stl | 290 | 144 | 2.02 |
| bench_sphere_400k.stl | 4855 | 2862 | 1.70 |
| bench_overhang_tower.stl | 5541 | 2428 | 2.28 |
| tuboshu.3mf（拥挤双板） | 360746 | **拒绝导出** | — |

解读注意：

1. **比值主要反映默认配置差异，不是封装开销**。owzx 的 STL 走内置默认
   （Creality 系 profile），Orca CLI 用它自己的默认（层厚 0.2mm vs 前者更细），
   切片工作量差 ~2 倍，与比值同量级。受控对比需两边钉相同 layer_height。
2. **Orca CLI 对拥挤板是硬拒绝**：tuboshu 双板切片 6 分钟后死于 G-code 路径
   冲突校验（-101，"Potentially lost branch"）。GUI 里这只是个可继续的警告，
   CLI 直接不导出；`--no-check` 也绕不过。owzx 对同一模型正常导出 1.5GB。
3. Orca CLI 的事实标准用法与坑：`--slice 0 --outputdir <dir>`；布尔选项不吞
   下一个 token（必须 `--key=value`）；3MF 内嵌工程配置与 CLI 覆盖可能冲突
   （wipe tower + relative-E 组合会 -51/-205）。

### 受控对比：同一个 3MF 工程文件、参数强制一致（2026-10-23）

方法：切片测试_无支撑.3mf（内嵌 Creality 工程参数，layer_height=0.2），
Orca 原生读取内嵌配置；owzx-cli 由 harness 自动解出内嵌
project_settings.config 经 --load-settings 注入。**双方 G-code 层数
756 = 756，参数一致性有硬证据**：

| 模型 | owzx | Orca | owzx/Orca |
|---|---:|---:|---:|
| 切片测试_无支撑.3mf（756 层） | 11.74s | 11.48s | **1.023** |

结论：参数一致后两者性能基本持平（±2%，噪声范围内）。此前 STL 对比
的 1.7~2.3× 全部来自"两边各用各的默认参数"（owzx 默认 0.08mm 层厚 vs
Orca 0.2mm），与封装层性能无关。

顺带发现的两个产品事实：

1. **owzx-cli 加载 3MF 时不读内嵌工程参数**（几何照收、配置走自己的
   preset，同一文件切出 1891 层 vs Orca 756 层）。GUI 加载工程文件应
   会应用参数，CLI 漏了——harness 已用自动提取+--load-settings 绕过，
   产品侧值得补。
2. **Orca CLI 加载 owzx 导出的工程 3MF 直接段错误**（exit 139，可稳定
   复现）——第三方产 3mf 的兼容性/健壮性问题，属 Orca 侧。

### 受控对比：有支撑场景（2026-10-23）

用 tools/make_support_tower_3mf.py 把悬空测试塔（23 万三角形、100mm、逐级
悬垂）换进 Creality 工程 3MF 的几何槽，内嵌参数仅翻转 enable_support=1，
其余（layer_height=0.2 / line_width=0.42）保持不变。双引擎各 3 次取最优：

| 模型 | owzx | Orca | owzx/Orca | 一致性证据 |
|---|---:|---:|---:|---|
| 切片测试_有支撑塔.3mf（697 层） | 3.09s | 2.60s | **1.19** | 层数 697=697，支撑标记 458=458 |

（owzx 经 --load-settings 注入同一份内嵌配置；runs 稳定在 ±10ms。）

结论：无支撑 1.02×，有支撑 1.19×——支撑路径下 owzx 比 Orca 慢约 19%，
量级健康，不构成回退告警；后续换版本重跑此场景即可盯住该比值。

### 大模型验证：200 万三角形 + 支撑（2026-10-23）

bench_sphere_2m（200 万三角形）经 make_support_tower_3mf.py 换几何并开
支撑（layer_height=0.2），双引擎各跑 2 次：

| 模型 | owzx | Orca | 说明 |
|---|---:|---:|---|
| sphere2m_support.3mf | 24.3~25.1s（rc=0） | 26.3~26.4s（**rc=156，-100 失败**） | 切片阶段观测耗时基本持平 |

结论确认：支撑塔小模型的 1.19× 是 ~500ms 固定开销（启动+加载+场景准备）
被小基数放大的结果；25s 级模型上比值收敛到 ~1.0，绝对差 ≈ 固定开销。
**但注意**：此场景 owzx 3 跑中有 1 次 rc=156 非确定性失败（原因未查明），
Orca CLI 两次均 -100 失败——大支撑模型的 CLI 稳定性两边都需要盯。

### 阶段级对比表（用户切分的流程段，2026-10-23 定版）

每次运行（含双引擎）都会产出 `artifacts/stage_comparison.md`：按 CP 流程
段（正在准备→应用参数→网格切片→墙/填充→支撑/悬空→优化→G-code→导出）
逐段给出 owzx 耗时（进度标记窗口法），Orca CLI 不吐阶段进度，只给总时长。
`run_report.csv` 新增 `stages_json` 列存同结构数据。要点：

- 正在准备（含进程启动+加载）≈ 0.6~0.9s，即与 Orca 差距的固定开销主体
- 无支撑大模型的大头在 墙(3.8s)/填充(4.7s)/填充路径(2.6s)——优化优先级参考

### 模型池试点（效率 39 + 卡在25% 8，2026-10-23）

tools/sync_model_pool.py 从内网共享同步模型库（分类树保留、>30MB 自动进
heavy/ 分层、可续传）。试点 28 个轻量模型双引擎基线：**15 过 / 13 失败，
失败全部是产品侧问题**——这正是模型池的价值：

- **7× SIGSEGV（exit -11）**：切片启动即崩。名单：效率/BBL/{24针织雪人,
  30yoda, 多色恐龙, 满盘卡皮巴拉（BBL）}, 效率/CP/{Creatures_mc拖入3mf崩溃,
  树状支撑_哥斯拉 (2)}, 效率/CP/雪人满盘——多色/AMS 配置的 3MF 是高危区
  （这批模型在 CrealityPrint 自己的测试集里是通过的）
- **6× rc=156**：`{if multicolor_method}` 等自定义 G-code 模板变量
  owzx 不识别（machine_start_gcode Parsing error）——模板方言兼容缺口
- 另有 1× std::bad_alloc（16拉布布，内存型，与 maorongxiong 同类）

基线只记录成功运行（by design）：24 行已入库（含逐段耗时 stages_json）。
失败清单就是给产品侧的 bug 候选列表；修复后重跑 --update-baseline 补录。

后续批次：crash(84)/compat(229) 不依赖 Orca、可全量；全池一轮 owzx 约
4~8h，适合夜间定时；重模型 heavy/ 留大内存机器。

### 13 失败模型修复记录（2026-10-25，12/13 修复）

产品侧四层修复后复测：**12/13 通过**（原 0/13）。修复清单（3DPrinter_Qt6
补丁列车 + 服务层）：

| 补丁 | 根因 | 修复 |
|---|---|---|
| 0009 | `{if multicolor_method}` 无定义（CP 方言） | PrintConfig 加 coBool 定义 + FullPrintConfig 静态成员（两者缺一不可：defs map 不进 FullPrintConfig 实例） |
| 0010 | Brim.cpp `filament_map[extruder-1]` 越界（map 默认 {1}） | 索引钳制 |
| 0011 | mm 分割 `segmentation[layer][extruder]` 双维越界 | 尺寸守卫 |
| 0012 | ToolOrdering `filament_map.values[filament]` 越界读+堆写 | 索引钳制（堆破坏元凶，延迟引爆在 brim） |
| 0013 | `flush_length_5..8` 未定义（`g_max_flush_count=4`） | 上限提到 8 |
| 0014 | WipeTower2::prime 单工具列表 `tools[-1]` 下溢 + m_filpar 维度错配 | 前工具回退 + 表尺寸覆盖 + 双下标钳制 |
| 服务层 | 模型自带 printable_area 未翻译为 bed_shape（350 模型落 220 床） | MODEL-BED 翻译（模型床优先） |

共性：**多耗材(≥3)/多色路径在此前从未被完整跑通过**，五处越界 + 两处
方言缺口全部由模型池试点暴露。

剩余 1 个：Creatures_mc拖入3mf崩溃.3mf —— normal 构建仍在 DynamicConfig
析构时段错误（更早的堆破坏下游），ASan 下转为"Prime Tower 出界"校验
错误。塔位语义需要产品决策（CP 侧塔位钳制策略），已单独立项跟踪。

### 对齐纪律（2026-10-25 定稿）

两条对齐线，边界如下——任何产品/测试改动前先对照：

1. **引擎核心对齐上游 Orca**：切片算法、路径规划、G-code 生成决策一律以
   上游行为为锚，回归判定以 Orca 为参照。禁止 CP 语义进入这一层。
2. **输入/配置方言层允许 CP 兼容超集**：3MF 解析、自定义 G-code 模板变量、
   配置键（如 multicolor_method、flush_length_5..8）——因为我们的输入是
   CP 生成的文件（模型池、用户模型）。每处兼容必须：
   - 注释标注 `CP-DIALECT` 并写明上游对照行为；
   - 缺省值**派生自上游行为**（例：上游无守卫=恒输出 → 派生为"耗材>1 即 true"），
     而不是猜测 CP 行为硬编码；
   - 新键需要**同时**加 PrintConfig defs 和 FullPrintConfig 静态成员
     （defs map 不进静态类实例，只加 defs 不生效——0009 的教训）。

实例复盘：0009 第一版默认 false 是在猜 CP 行为（越线），修订为按耗材数
派生（对齐上游"无守卫"语义）——多色模型 G-code 现在正确输出工具更换宏。

### 上游对照审计（2026-10-25，对照 SoftFever/OrcaSlicer main）

| 我们的修复 | 上游 main 现状 | 定性 |
|---|---|---|
| 0009 multicolor_method | **无此变量**（CP fork 专属方言） | 输入方言扩展，超出上游 |
| 0013 flush 上限 4→8 | 同款 `g_max_flush_count = 4` | 上游同款限制，5 色模板上游也会失败 |
| 0012 ToolOrdering 钳制 | **同款越界**（`filament_map.values[filament]`，还有第二处 lambda 同病） | 修了上游也没修的真 bug |
| 0014 WipeTower prime 守卫 | **同款 `tools[idx_tool-1]` 下溢**（单工具列表即崩） | 同上 |
| 0011 mm 分割守卫 | **同款未守卫** `segmentation[layer_id][extruder_id]` | 同上 |
| 0010 Brim 钳制 | 上游 Brim 无 filament_map 代码——多耗材 brim 是 fork 层（Creality 系）代码 | fork 层 bug，上游无此代码 |
| MODEL-BED 翻译 | 上游引擎同样不翻译（信任配置+校验拒绝）；重算塔位是 GUI 职责 | CLI 补 GUI 等价职责 |

要点：**"上游"有两级** —— SoftFever/OrcaSlicer（公共）与 wzx011011/OrcaSlicer
fork（子模块实际指向，携带 Creality 系多喷嘴/多耗材 brim 代码）。 filament_map
是 SoftFever 的多喷嘴特性，但四处索引越界在公共上游原样存在——模型池试点
等于替上游做了一次多色路径压测。已验证 12/13 的修复全部先于上游。

### 鳄鱼修改眼睛 39% 差距定位（2026-10-25，进行中→已立项）

逐段定位（157s 总差 44s vs Orca 113s）：

| 阶段 | 耗时 | 判定 |
|---|---:|---|
| 3MF 导入 | **27.0s** | 🚨 异常（24MB 文件；其他模型同环节 <1s）。gdb 采样 22 次：热路径为**单线程 miniz 解压 + _BBS_3MF_Importer 对象回调**，无内存错误（ASan 干净）。根因未闭：Orca 侧导入时间无法从 CLI 分解（全程静默），export-3mf 隔离实验被双方 CLI 语义挡住。已立项：需读 ProjectService/Import3mf 路径找 fork 层多余工作 |
| 切片(网格/墙/填充/支撑) | ~8.5s | 正常 |
| 生成G-code | 117s | 涂色模型合法重（mm 分割）；**G-code 内容与 Orca 持平**（130.8 vs 129.1MB、72 层一致）——排除"多打内容" |
| 导出 | 0.3s | 正常 |

注：本次复测 163s vs 基线 157s 有 ~6s 运行波动；G-code 体量持平说明瓶颈
是处理速度而非内容差异。导入修复后预期总差距缩至 ~17s（比值 ~1.10）。

### 导入 27s 根因收窄（同日续）

排除法完成：
- **解压不是瓶颈**：python zlib 解全部条目仅 0.5s（24MB→128MB）
- **热点已定位**：gdb 采样 22 次中的真实工作帧 = `_BBS_3MF_Importer::
  ObjectImporter::_extract_object_from_archive` + 逐顶点/属性回调
  （单对象 230 万三角形 ≈ 690 万顶点的 XML 逐属性解析）
- 该导入器为 BBS/Orca 同源代码；Orca 侧导入耗时无法从 CLI 分解（全程
  静默），其总时长 111.5s 含导入
- **待做**：导入器性能专项（多线程解析/跳过冗余属性），收益 = 大型涂色
  3MF 的打开速度（GUI 同路径受益）；当前单点数据已可接受——鳄鱼总比值
  1.39 中的 27s 为已定位的独立瓶颈，25 模型中位比值 1.005 为验收口径

### Perf 实锤：95% CPU = 接缝放置器射线求交（上游同款算法）

perf record 全程采样（199Hz）聚合：**94.99% CPU** 集中于
`AABBTreeIndirect::intersect_ray_recursive_all_hits`，次热点
`tsp_remove_crossings` 23%。调用方 = `SeamPlacer`（GCode 导出阶段的
raycasting visibility——为每个接缝候选点对网格投射射线判可见性）。

对照 SoftFever/OrcaSlicer main 的 SeamPlacer.cpp：**同款
intersect_ray_all_hits + raycasting_visibility，上游原样存在**。
即：鳄鱼生成G-code 117s 的大头是上游接缝放置器的可见性射线，两家都付，
不是我们的封装层偏离。Orca 侧无法分解验证（CLI 无阶段输出）。

至此鳄鱼 1.39× 的完整归因：
- 27s 导入：BBS_3MF_Importer 单线程 XML 解析（独立性能专项，已立项）
- ~20s 差值：正在准备/配置合并（服务层，含 27s 内的杂项）
- 其余：接缝射线 + mm 分割 + G-code 生成——上游同款引擎成本

25 模型聚合中位比值 1.005 仍为验收口径；鳄鱼属重涂色边界样本。
