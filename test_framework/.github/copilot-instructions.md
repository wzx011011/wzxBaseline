# C3DBaseline 测试框架 Copilot 指南

## 项目概述
针对 **Creality Print 7.0 Beta** 切片器的自动化 G-code 校验框架。通过从 3MF 模型生成 G-code 并使用多级检测策略验证输出，测试切片参数。

**核心工作流**: 3MF 模型 → 切片器 API → G-code → 解析器 → 校验器 → 测试结果

## 架构与组件

### 1. 目录结构（关键导航）
```
engine_params/
├── case/params/<module>/          # 测试入口 (test_*.py)
│   └── test_<group>.py             # 包含 test_<parameter>() 函数
├── src/gcode/<module>/             # 校验逻辑
│   └── <group>_check.py            # 包含 parse_<parameter>() 函数
├── data/
│   ├── case_input/<module>/<group>/<param>.json  # 测试用例定义
│   └── models/<module>/<group>/<param>/*.3mf     # 测试模型
└── output/                         # 自动管理的 G-code 输出 (--clean-gcode)
```

**命名约定（关键 - 违反将导致自动发现失败）**:
- 测试文件: `engine_params/case/params/<module>/test_<group>.py`
- 测试函数: `def test_<parameter>(slice_and_export, expected_*, ...)`
- 校验函数: `engine_params/src/gcode/<module>/<group>_check.py::parse_<parameter>()`
- JSON 配置: `engine_params/data/case_input/<module>/<group>/<parameter>.json`
- 模型文件: `engine_params/data/models/<module>/<group>/<parameter>/<name>.3mf`

### 2. 测试框架流程（自动参数化）

**动态参数注入** (`conftest.py::pytest_generate_tests`):
1. 从 `case_input/` 读取 `<parameter>.json`
2. 将 `input_3mf` 文件名解析为 `data/models/` 中的绝对路径
3. 按**声明顺序**将参数注入测试函数：
   - `slice_and_export` (fixture, indirect)
   - `expected_*` 值（来自 JSON）
   - 额外参数如 `baseline_gcode`（通过 `RESOLVERS` 自动解析）

**Fixture 执行流程** (`slice_and_export`):
1. `reset_project` - 清理切片器状态
2. `trigger_load_project2` - 通过 Bambu Studio API 加载 3MF
3. `click_button(SLICE_BTN_ID)` - 触发切片
4. `export_gcode` - 导出到 `gcode_dir/`（自动管理）
5. `wait_for_file_written` - **基于 Watchdog** 的事件检测（无轮询）

### 3. 校验层次（L1/L2/L3 策略）

**Level 1 - 配置对比**（最快，52/66 参数）:
```python
cfg = parser.load_config()  # 读取 "; CONFIG_BLOCK_START"
actual = cfg.get("prime_tower_width")  # 直接键值查找
```
使用场景：G-code 配置块中的简单数值/布尔/字符串值。

**Level 2 - 特征检测**（中等，9/66 参数）:
```python
# 检测特征的存在/缺失
tower_blocks = parser.get_extrusion_blocks_per_layer(ExtrusionType.PRIME_TOWER.value)
enabled = any(blocks for blocks in tower_blocks)

# 螺旋模式：检查 Z 轴连续性
z_values = [cmd.z for cmd in parser.parse_g1_commands() if cmd.has_z]
is_spiral = all(z_values[i] < z_values[i+1] for i in range(len(z_values)-1))
```
使用场景：布尔参数、TYPE 标记的存在、几何模式。

**Level 3 - 路径分析**（复杂，4/66 参数）:
```python
# 边界框验证
coords = parser.get_coordinates(layer=0, extrusion_type="Prime tower")
width = max(c.x for c in coords) - min(c.x for c in coords)

# 模糊皮肤：路径偏差分析
outer_wall = parser.get_coordinates(extrusion_type="Outer wall")
deviations = [distance_to_ideal_contour(pt) for pt in outer_wall]
std_dev = statistics.stdev(deviations)  # 应匹配 fuzzy_skin_thickness
```
使用场景：几何验证、比较实际路径与预期尺寸。

## 关键实现模式

### 测试函数模板
```python
@pytest.mark.engine_params
def test_<parameter>(
    slice_and_export: Path,      # 自动注入，触发切片
    expected_value: str,          # 来自 JSON "expected_value"
    baseline_gcode: Path = None,  # 从 "baseline_gcode" 键自动解析
):
    """测试 <parameter> (Level X - 策略)"""
    gcode_path = slice_and_export
    ok, actual, details = parse_<parameter>(gcode_path, expected_value)
    
    assert ok, f"{parameter} 期望 {expected_value}，实际 {actual}：{details}"
```

### 校验函数模板
```python
def parse_<parameter>(
    gcode_path: Path,
    expected_value: Any,
) -> Tuple[bool, Any, Dict]:
    """
    返回: (成功: bool, 实际值, 详情: dict)
    详情应包括: detection_method, message, raw_data
    """
    parser = GCodeParser(gcode_path)
    
    # Level 1: 配置
    cfg = parser.load_config()
    actual = cfg.get("<parameter>")
    
    return (
        actual == expected_value,
        actual,
        {"detection_method": "Level 1 - Config", "message": "..."}
    )
```

### JSON 配置格式
```json
{
  "cases": [
    {
      "project_name": "描述性测试名称",
      "input_3mf": "model_file.3mf",          // 仅文件名，自动解析
      "expected_value": "expected_result",     // 任意 JSON 类型
      "baseline_gcode": "baseline.gcode",      // 可选，自动解析
      "extra_param": 0.1                       // 支持自定义参数
    }
  ]
}
```

## 开发命令

### 运行测试
```powershell
# 设置必需的环境变量
$env:CREALITY_PRINTER_PATH = "C:\Program Files\Creality\Creality Print 7.0 Beta\CrealityPrint.exe"
$env:PYTHONPATH = "E:\wzx\C3DBaseline\test_framework"

# 运行所有测试
pytest engine_params/case/params/others/test_special_mode.py -v

# 运行特定参数测试
pytest engine_params/case/params/others/test_special_mode.py::test_slicing_mode -v

# 运行时清理输出
pytest --clean-gcode -v

# 自定义 G-code 输出位置
pytest --gcode-root="D:\custom_output" --gcode-scope=module
```

### 添加新参数测试
1. **创建 JSON 配置**: `data/case_input/<module>/<group>/<param>.json`
2. **生成 3MF 模型**: 使用 `create_<group>_3mf_files.py` 或手动导出
3. **添加校验函数**: `src/gcode/<module>/<group>_check.py::parse_<param>()`
4. **添加测试函数**: `case/params/<module>/test_<group>.py::test_<param>()`
5. **运行测试**: 框架自动发现并参数化

### 3MF 文件生成
```python
# 基于模板（不修改参数，需要手动 UI 配置）
TEMPLATE_3MF = "data/models/template_model.3mf"
shutil.copy2(TEMPLATE_3MF, f"output/{param_name}_{value}.3mf")
# 然后在切片器 UI 中手动配置并重新导出

# 程序化修改（已弃用 - 切片器会忽略配置更改）
# 不要使用：修改 Metadata/project_settings.config 不影响切片
```

## 常见陷阱与解决方案

### 1. 枚举值大小写敏感
**问题**: PrintConfig.hpp 定义 PascalCase (`Regular`)，G-code 使用小写 (`regular`)。
**解决方案**: JSON 期望值使用实际 G-code 格式（小写/带空格）。
```json
// 正确
{"expected_value": "by layer"}  // 不是 "ByLayer"
{"expected_value": "regular"}   // 不是 "Regular"
```

### 2. Watchdog 文件检测
**始终使用**: `wait_for_file_written(path, timeout=60, settle_time=1.0)`
- 事件驱动（无忙等待）
- 检测写入完成（大小/mtime 稳定 + 文件锁释放）
- 跨平台（Windows 通过 open() 尝试检测写锁）

### 3. G-code TYPE 标记（精确字符串）
```python
ExtrusionType.PRIME_TOWER.value    # ";TYPE:Prime tower" (不是 "Wipe tower")
ExtrusionType.OUTER_WALL.value     # ";TYPE:Outer wall" (不是 "External perimeter")
ExtrusionType.SKIRT.value          # ";TYPE:Skirt" (与 Brim 分开)
# 还有: ";WIPE_TOWER_START" / ";WIPE_TOWER_END" 标记
```

### 4. 引擎不可用处理
通过 `--engine-unavail` 配置：
- `xfail`（默认）：标记为预期失败（基础设施问题）
- `skip`：完全跳过测试
- `error`：抛出 ERROR（不是 FAIL）

## 关键文件参考

- **根目录 conftest.py**: 旧式 fixtures (creality_printer_path, app_respone)
- **engine_params/conftest.py**: 现代引擎会话，slice_and_export fixture
- **engine_params/pytest_engine_params.py**: CLI 选项注册（必须通过 `-p` 加载）
- **src/slicerctl/**: 切片器 API 客户端（基于 socket 的 IPC 与 CrealityPrint.exe 通信）
- **src/gcode/GCodeParser.py**: 高性能解析器（基于 mmap，1300+ 行）
- **multimaterial_others_validation_design.md**: 完整校验策略文档

## 外部依赖

- **Creality Print 7.0 Beta**: 必需的切片器（通过 `"test#157369"` 参数启用测试模式）
- **Watchdog**: 文件系统事件监控（`pip install watchdog`）
- **pytest**: 测试框架，带自定义参数化钩子

## 文档资源

- **README.md**: 设置、环境变量、工作流说明
- **workflow_prompt.md**: 添加新测试用例的分步指南
- **process_parameters.md**: 完整参数参考（来自 C3DSlicer 源码）
- **Bambu Lab Wiki**: 参数行为文档（如擦料塔、冲刷选项）
