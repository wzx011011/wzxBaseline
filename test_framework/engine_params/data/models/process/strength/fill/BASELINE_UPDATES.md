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
