# 支撑参数测试用例格式修复报告

## 修复日期
2025-12-22

## 问题分析

通过分析 C3DSlicer 源码（E:\wzx\C3DSlicer\C3DSlicer），发现测试用例的期望值格式与 G-code 实际输出格式不匹配：

### 根本原因
- **JSON 配置**使用 C++ 枚举名（如 `stNormalAuto`）和字符串布尔值（`"true"`/`"false"`）
- **G-code 输出**使用字符串映射表定义的小写格式（如 `normal(auto)`）和整数布尔值（`0`/`1`）
- **校验函数**进行字符串比较，无法正确处理整数类型

---

## 源码分析结果

### 1. 枚举类型参数

#### support_type (支撑类型)
**枚举定义** (`PrintConfig.hpp:201-203`):
```cpp
enum SupportType {
    stNormalAuto, stTreeAuto, stNormal, stTree
};
```

**字符串映射** (`PrintConfig.cpp:283-288`):
```cpp
static t_config_enum_values s_keys_map_SupportType{
    { "normal(auto)",   stNormalAuto },    // 0
    { "tree(auto)",     stTreeAuto },      // 1
    { "normal(manual)", stNormal },        // 2
    { "tree(manual)",   stTree }           // 3
};
```

**修复映射**:
| 旧期望值 (错误) | 新期望值 (正确) | G-code 输出 |
|----------------|----------------|------------|
| `stNormalAuto` | `normal(auto)` | `normal(auto)` |
| `stTreeAuto`   | `tree(auto)`   | `tree(auto)`   |

---

#### support_style (支撑样式)
**枚举定义** (`PrintConfig.hpp:181-183`):
```cpp
enum SupportMaterialStyle {
    smsDefault, smsGrid, smsSnug, smsTreeSlim, 
    smsTreeStrong, smsTreeHybrid, smsTreeOrganic
};
```

**字符串映射** (`PrintConfig.cpp:256-264`):
```cpp
static t_config_enum_values s_keys_map_SupportMaterialStyle {
    { "default",        smsDefault },      // 0
    { "grid",           smsGrid },         // 1
    { "snug",           smsSnug },         // 2
    { "tree_slim",      smsTreeSlim },     // 3
    { "tree_strong",    smsTreeStrong },   // 4
    { "tree_hybrid",    smsTreeHybrid },   // 5
    { "organic",        smsTreeOrganic }   // 6
};
```

**修复映射**:
| 旧期望值 (错误) | 新期望值 (正确) | G-code 输出 |
|----------------|----------------|------------|
| `smsDefault`   | `default`      | `default`  |
| `smsGrid`      | `grid`         | `grid`     |
| `smsTreeOrganic` | `organic`    | `organic`  |

---

#### support_interface_pattern (接触面图案)
**枚举定义** (`PrintConfig.hpp:192-194`):
```cpp
enum SupportMaterialInterfacePattern {
    smipAuto, smipRectilinear, smipConcentric, 
    smipRectilinearInterlaced, smipGrid, smipMonotonicLine
};
```

**字符串映射** (`PrintConfig.cpp:267-274`):
```cpp
static t_config_enum_values s_keys_map_SupportMaterialInterfacePattern {
    { "auto",           smipAuto },                     // 0
    { "rectilinear",    smipRectilinear },              // 1
    { "concentric",     smipConcentric },               // 2
    { "rectilinear_interlaced", smipRectilinearInterlaced }, // 3
    { "grid",           smipGrid },                     // 4
    { "monotonicline",  smipMonotonicLine }             // 5
};
```

**修复映射**:
| 旧期望值 (错误) | 新期望值 (正确) | G-code 输出 |
|----------------|----------------|------------|
| `smipAuto`      | `auto`         | `auto`     |
| `smipRectilinear` | `rectilinear` | `rectilinear` |
| `smipConcentric` | `concentric`  | `concentric`  |
| `smipGrid`      | `grid`         | `grid`     |

---

### 2. 布尔类型参数

**G-code 输出格式**: `0` (false) / `1` (true)

**旧期望值** (错误): `"false"` / `"true"` (字符串)
**新期望值** (正确): `0` / `1` (整数)

影响的参数：
- `enable_support`
- `support_on_build_plate_only`
- `support_critical_regions_only`
- `support_remove_small_overhang`
- `support_interface_not_for_body`
- `support_interface_loop_pattern`

---

## 修复内容

### 阶段一：JSON 配置文件修复（已完成）

修改了 10 个 JSON 配置文件：

#### 枚举值修复（3个文件）
1. `support_basic/support_type.json`
   - `stNormalAuto` → `normal(auto)`
   - `stTreeAuto` → `tree(auto)`

2. `support_basic/support_style.json`
   - `smsDefault` → `default`
   - `smsGrid` → `grid`
   - `smsTreeOrganic` → `organic`

3. `support_advanced/support_interface_pattern.json`
   - `smipAuto` → `auto`
   - `smipRectilinear` → `rectilinear`
   - `smipConcentric` → `concentric`
   - `smipGrid` → `grid`

#### 布尔值修复（7个文件）
4. `support_basic/enable_support.json`
   - `"false"` → `0`, `"true"` → `1`

5. `support_basic/support_on_build_plate_only.json`
   - `"false"` → `0`, `"true"` → `1`

6. `support_basic/support_critical_regions_only.json`
   - `"false"` → `0`, `"true"` → `1`

7. `support_basic/support_remove_small_overhang.json`
   - `"false"` → `0`, `"true"` → `1`

8. `support_filament/support_interface_not_for_body.json`
   - `"false"` → `0`, `"true"` → `1`

9. `support_advanced/support_interface_loop_pattern.json`
   - `"false"` → `0`, `"true"` → `1`

---

### 阶段二：校验函数修复（已完成）

修改了 `engine_params/src/gcode/process/support_check.py`：

#### 布尔值参数校验函数（4个函数）
修复了字符串比较为整数比较，避免 `.lower()` 调用导致 AttributeError：

```python
# 修复前（错误）
return (
    str(actual_cfg).lower() == expected_value.lower(),  # ❌ 字符串比较
    actual_cfg,
    {...}
)

# 修复后（正确）
actual_value = int(actual_cfg) if actual_cfg is not None else None
expected_int = int(expected_value) if isinstance(expected_value, (str, int)) else expected_value

return (
    actual_value == expected_int,  # ✅ 整数比较
    actual_value,
    {...}
)
```

修复的函数：
1. `parse_support_critical_regions_only()`
2. `parse_support_remove_small_overhang()`
3. `parse_support_interface_not_for_body()`
4. `parse_support_interface_loop_pattern()`

---

## 测试验证结果

### ✅ 格式修复验证（使用默认 3MF）

#### 枚举值测试
```powershell
pytest test_support.py::test_support_type -v
# 结果: 2 passed (support_type_normal, support_type_tree)
# ✅ 枚举格式修复成功！
```

#### 布尔值测试
```powershell
pytest test_support.py::test_support_critical_regions_only -v
# 结果: 1 passed (disabled), 1 failed (enabled - 3MF未配置)
# ✅ 布尔值格式修复成功，disabled 测试通过！
```

### ⚠️ 完整测试（需要配置 3MF）

运行所有 64 个测试用例：
```powershell
pytest test_support.py -v
# 预期结果:
# - 15 passed (使用默认值的测试)
# - 49 failed (需要手动配置 3MF 文件)
```

**失败原因**: 所有 3MF 文件从 `template_model.3mf` 复制而来，使用默认参数值。

---

## 后续任务

### 🔧 必须完成（由用户手动操作）
**任务**: 在 Creality Print 7.0 Beta 中配置 64 个 3MF 文件
- 参考: `SUPPORT_3MF_CONFIG_CHECKLIST.md`（完整配置清单）
- 预计时间: 15-25 分钟
- 完成后所有测试应能通过

### 📋 可选优化（低优先级）
1. **拆分测试文件**（可选）
   - 当前: `test_support.py`（25个测试函数，687行）
   - 建议: 拆分为 5 个文件按参数组（`test_support_basic.py`, `test_support_raft.py`, ...）
   - 好处: 更易维护，符合现有项目结构

2. **拆分校验文件**（可选）
   - 当前: `support_check.py`（25个校验函数）
   - 建议: 拆分为 5 个文件（`support_basic_check.py`, `support_raft_check.py`, ...）
   - 好处: 代码组织更清晰

---

## 经验总结

### 教训
1. **永远以 G-code 实际输出为准**
   - 不要假设配置值格式，必须查看源码或实际 G-code
   - C++ 枚举名 ≠ G-code 字符串（映射表决定输出格式）

2. **类型一致性很重要**
   - Python 动态类型可能隐藏问题（字符串 vs 整数）
   - 校验函数应明确处理类型转换

3. **源码是最权威的文档**
   - `PrintConfig.hpp` 定义枚举
   - `PrintConfig.cpp` 定义字符串映射
   - `Config.hpp::serialize()` 控制输出格式

### 最佳实践
1. **添加新参数时**:
   - 先查源码确认 G-code 格式
   - JSON 期望值使用实际输出格式
   - 校验函数处理类型转换

2. **测试驱动开发**:
   - 用默认值测试先验证格式
   - 再配置 3MF 测试实际功能

3. **文档先行**:
   - 源码分析结果记录下来
   - 配置清单帮助手动操作
   - 修复报告便于后续维护

---

## 相关文件

### 已修改文件（10个 JSON + 1个 Python）
- `engine_params/data/case_input/process/support/**/*.json` (10个)
- `engine_params/src/gcode/process/support_check.py`

### 参考文档
- `SUPPORT_TESTS_STRUCTURE.md` - 目录结构文档
- `SUPPORT_3MF_CONFIG_CHECKLIST.md` - 3MF 配置清单
- `process_parameters.md` - 参数完整参考

### 源码参考（C3DSlicer）
- `E:\wzx\C3DSlicer\C3DSlicer\src\libslic3r\PrintConfig.hpp`
- `E:\wzx\C3DSlicer\C3DSlicer\src\libslic3r\PrintConfig.cpp`
- `E:\wzx\C3DSlicer\C3DSlicer\src\libslic3r\Config.hpp`
- `E:\wzx\C3DSlicer\C3DSlicer\src\libslic3r\GCode.cpp`

---

**状态**: ✅ 格式修复完成，等待 3MF 文件配置
**下一步**: 用户手动配置 64 个 3MF 文件（参考 CHECKLIST）
