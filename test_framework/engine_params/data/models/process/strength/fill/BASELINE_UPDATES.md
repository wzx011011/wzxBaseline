# 2026-09-07：确认误报后的有限基线更新

本次仅更新以下 8 份快照，保留既有严格的层数、路径数、点数和坐标比较。
来源为同一组原始 3MF，经现有程序
`F:\work\C3DSlicer\out\weiyusuo-release\build\src\CrealityPrint.exe`
于 2026-09-07 重新切片的输出；没有重新编译。
EXE SHA-256：`68a0bffb273a66015bf270e7b5af9990608a4e98ed96897885205f598e73fb35`。

| 目录 / 基线 | 已核实的变化 |
| --- | --- |
| `bottom_surface_pattern/baseline_bottomsf_hilbert_curve.gcode` | 路径数不变，分段/量化差异，几何覆盖差异约 0.000707 mm |
| `bottom_surface_pattern/baseline_bottomsf_archimedean_chords.gcode` | 32 条路径重排后全部匹配 |
| `bottom_surface_pattern/baseline_bottomsf_octagram_spiral.gcode` | 72 条路径重排/反向后全部匹配 |
| `internal_solid_infill_pattern/baseline_sip_aligned_rectilinear.gcode` | 圆弧拟合、分段及端点量化，几何覆盖差异约 0.001008 mm |
| `internal_solid_infill_pattern/baseline_sip_hilbert_curve.gcode` | 路径数不变，分段/量化差异，几何覆盖差异约 0.001 mm |
| `internal_solid_infill_pattern/baseline_sip_monotonic_line.gcode` | 顺序及量化差异，几何覆盖差异约 0.001008 mm |
| `internal_solid_infill_pattern/baseline_sip_octagram_spiral.gcode` | 每层 85 条路径重排/反向后全部匹配 |
| `internal_solid_infill_pattern/baseline_sip_rectilinear.gcode` | 顺序及量化差异，几何覆盖差异约 0.001008 mm |

核查的是各用例对应挤出角色的实际正向挤出，跟踪挤出模式并排除擦拭。
先在每坐标 0.001 mm 容差内匹配线段多重集；不匹配处展开圆弧并比较覆盖。
圆弧弦高上限 0.00001 mm，采样间隔不超过 0.05 mm，上述距离为采样估计。
这些核查值用于本次人工审核，不是新增的宽松比较阈值。

基线保存完整新导出，故也包含导出器配置/元数据和其他挤出角色的版本变化，
不手工拼接新旧 G-code。仅清理新增行的末尾空白，不改变命令含义。
原始证据位于本地输出目录
`output/weiyusuo_jenkins28_failed42_20260907_102517/analysis19_geometry.json`，
输出目录不属于提交内容。

明确未更新：AI cubic、AI rectilinear、内部填充 monotonic、50% grid/hilbert_curve
稀疏填充、100% 填充搭接。AI rectilinear 的裁减失效必须修复程序；
其余连接变化尚需功能判定，不能作为精度差异放行。

## 2026-09-09：补齐已完成行为核验的 4 份快照

在上节的后续核验中，以下 4 项已确认是连接顺序、分段或端部连接变化，
本次更新完整快照，未修改比较器、层数/路径数/点数约束或坐标容差。

| 基线 | 复核证据 |
| --- | --- |
| `internal_solid_infill_pattern/baseline_sip_monotonic.gcode` | 5 个常规实心层的 64 条主体扫描线保持单向，方向反转为 0；窄残留层不变 |
| `sparse_infill_density/baseline_50%_noai_grid.gcode` | 22 层核心扫描线匹配；两组间距约 1.6283 mm，符合 50% 密度 |
| `sparse_infill_density/baseline_50%_noai_hilbert_curve.gcode` | 22 层核心覆盖差异约 0.000707 mm；网格步长约 0.8142 mm，符合 50% 密度 |
| `infill_wall_overlap/baseline_infill_wall_overlap_100percentage.gcode` | 普通实心/稀疏扫描线到内墙中心距离分别为 0/0.015 mm，符合不同线宽下的 100% 搭接；8 个层/角色的边界极值不变 |

100% 搭接用例包含桥接和端部连接，不能把普通扫描线公式套用到所有路径。
端部连接最大采样差异约 0.217 mm，部分短连接进入核心区域；这不是纯 0.001 mm 差异。
此次放行依据是主体扫描线、墙位置及搭接深度不变，而非把全局容差扩大。
上述几何覆盖距离为采样估计，不是严格连续 Hausdorff 上界。

来源均为 `output/rebuilt_failed42_20260907_124334` 中 2026-09-07 保存的 G-code。
切片 DLL SHA-256：`4200ea86a7cd00279e62b769e23d8c0d65614082283f2d0a574716e7c23ada0c`。
按上表顺序，原始导出文件 SHA-256 为：

```text
9304447d5f316de30b64546cc9d868a399eaf1f628eb9b5631a02f971e0239f2
53e83adfbf36b2c1ae98c6235778604c68e156a9732db813891b834db7e050ac
db3207ba41b5dfd39fe382d09aef1063f22275cb2c0b23ddc510bbc545b7824b
baf089d449166a54269bc457d51350d1732db00a11fcf7ccba6ae8cb9f5fe832
```

基线与这些原始导出逐行去除末尾空白后完全一致。仍保留完整导出的配置/元数据，
没有拼接不同版本的路径。原始核验报告为该本地目录下的 `semantic_verification5.md`
及 `semantic_audit5.json`，测试产物不纳入提交。

本次仅回放已有输出，未重新切片、未编译，也未取得 #30 的原始 G-code。
不能用本地回放结果代替 #30 同版本程序的重新回归。
AI cubic 继续跳过，AI rectilinear 基线不变，多耗材支撑失败不在此次更新范围内。
