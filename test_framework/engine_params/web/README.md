# C3DBaseline 测试运行器 Web 界面

## 📁 文件说明

- **start_test.py** - 一键启动脚本（推荐使用）
- **start_test.bat** - Windows 快捷启动脚本（双击即可运行）
- **test_selector_template.html** - HTML 模板文件
- **test_selector_hierarchical.html** - 生成的测试选择器页面（包含实际测试数据）
- **tests_data.json** - 测试用例数据（410+ 测试）
- **generate_test_selector.py** - 测试用例收集脚本
- **test_runner_server.py** - Web 服务器，提供测试运行功能

## 🚀 快速开始

### 方法1：一键启动（推荐）

**使用 Python 脚本：**
```powershell
cd E:\wzx\C3DBaseline\test_framework\web
python start_test.py
```

**或双击快捷方式：**
直接双击 `start_test.bat` 文件

**启动参数（可选）：**
```powershell
python start_test.py --port 9000           # 指定端口
python start_test.py --no-browser          # 不自动打开浏览器
python start_test.py --skip-generate       # 跳过测试收集（使用现有数据）
python start_test.py --help                # 查看所有选项
```

### 方法2：手动启动

1. 生成测试数据（可选，如果已有数据可跳过）：
   ```powershell
   cd E:\wzx\C3DBaseline\test_framework\web
   python generate_test_selector.py
   ```

2. 启动 Web 服务器：
   ```powershell
   python test_runner_server.py --port 8888
   ```

3. 在浏览器打开：http://localhost:8888

## 📋 功能特性

### 测试选择
- **完整层级结构**：模块 → 组 → 子组 → 测试文件 → 测试参数
- **410+ 测试用例**：包含所有参数化的测试实例
- **灵活选择**：支持在任何层级批量选择/取消选择
- **实时搜索**：输入关键词快速过滤测试，自动展开匹配项
- **全选/反选**：快速操作所有测试用例

### 测试执行
- **智能按钮切换**：
  - 未运行时：▶️ 运行选中的测试（蓝色）
  - 运行中时：⏹️ 取消测试（红色）
  - 点击自动切换状态
- **实时进度条**：
  - 动态显示测试进度百分比
  - 渐变色进度条带光泽动画
  - 显示完成数量（如：5/10 (50%)）
- **实时输出**：测试执行过程实时显示在右侧面板
- **彩色高亮**：
  - 🟢 绿色 - PASSED
  - 🔴 红色 - FAILED
  - 🟠 橙色 - ERROR
  - 🟡 黄色 - SKIPPED
- **随时取消**：可中断正在运行的测试（需确认）
- **清空输出**：一键清除输出内容

### 界面布局
- **左右分栏**：左侧选择测试（50%），右侧查看输出（50%）
- **自适应高度**：输出区域自动占据可用空间
- **折叠展开**：支持多级折叠，方便浏览大量测试
- **防溢出优化**：长文本自动换行，不会挤出显示区域

## 🔧 技术实现

### 前端技术
- **纯原生实现**：HTML + CSS + JavaScript，无需额外框架
- **CSS 动画**：进度条光泽流动效果（@keyframes shimmer）
- **Flexbox 布局**：响应式左右分栏，防止内容溢出
- **状态管理**：JavaScript 智能切换运行/取消按钮

### 后端技术
- **Web 服务器**：Python HTTPServer + 自定义 Handler
- **测试集成**：pytest 子进程执行 + 实时输出捕获
- **命令行优化**：自动处理 Windows 命令行长度限制（临时脚本方案）

### 通信机制
- **SSE (Server-Sent Events)**：实时输出流推送
- **EventSource API**：客户端接收实时数据
- **队列缓冲**：使用 Python queue.Queue 管理输出流

### 性能优化
- **智能缓存**：基于目录哈希的变化检测
- **增量更新**：24 小时内缓存有效
- **快速启动**：缓存命中时收集速度 <1 秒（vs 15 秒）

### 数据收集
- **pytest --collect-only**：获取所有测试用例（包括参数化）
- **正则解析**：提取测试路径和参数
- **层级构建**：自动生成 5 级树形结构

## 📝 注意事项

### 环境配置
1. **Python 版本**：需要 Python 3.7 或更高版本
2. **环境变量**：
   - `PYTHONPATH`：start_test.py 会自动设置
   - `CREALITY_PRINTER_PATH`：需手动配置（指向 CrealityPrint.exe）

### 端口管理
3. **默认端口**：8888（可通过 `--port` 参数自定义）
4. **自动清理**：start_test.py 会自动终止占用端口的旧进程
5. **手动清理**：`netstat -ano | findstr :8888` 查看，`taskkill /F /PID <PID>` 终止

### 数据缓存
6. **缓存文件**：`.test_cache.json`（自动生成）
7. **缓存有效期**：24 小时或测试文件变化时失效
8. **强制更新**：删除 `.test_cache.json` 或运行 `python generate_test_selector.py`

### 进程管理
9. **服务器窗口**：独立 Console 窗口运行，关闭即可停止
10. **后台持久化**：关闭启动脚本不会停止服务器
11. **浏览器独立**：关闭浏览器不影响服务器运行

## 🐛 故障排查

**问题：一键启动失败**
- 检查是否在 `web/` 目录下运行
- 确认 Python 环境正确（需要 Python 3.7+）
- 查看错误提示，按 Enter 前复制错误信息

**问题：端口被占用且无法自动清理**
- 手动查找进程：`netstat -ano | findstr :8888`
- 手动终止：`taskkill /F /PID <进程ID>`
- 或使用 `--port` 参数指定其他端口

**问题：浏览器未自动打开**
- 手动访问：http://localhost:8888
- 或使用 `--no-browser` 参数，自己控制打开时机

**问题：测试列表显示为空**
- 运行：`python generate_test_selector.py` 重新生成
- 检查 `engine_params/case/params/` 目录是否存在

**问题：CrealityPrint 连接失败**
- 确保 `CREALITY_PRINTER_PATH` 环境变量正确
- 确认软件版本为 Creality Print 7.0 Beta
- 检查软件是否正在运行（需要先启动软件）

## 📦 更新测试数据

当测试用例有更新时：

```powershell
# 方法1：使用一键启动（会自动重新生成）
python start_test.py

# 方法2：只更新数据不启动服务器
python generate_test_selector.py

# 方法3：使用启动参数跳过生成
python start_test.py --skip-generate  # 使用现有数据
```

## 🎯 最佳实践

### 启动方式
1. **首次使用**：运行 `python start_test.py` 完成所有设置
2. **日常测试**：双击 `start_test.bat` 快速启动（推荐）
3. **调试模式**：使用 `--no-browser -v` 参数查看详细日志
4. **团队协作**：使用 `--port` 指定不同端口避免冲突

### 测试技巧
5. **搜索定位**：在搜索框输入关键词快速过滤测试
6. **分批执行**：先选择少量测试验证环境，再执行完整测试
7. **进度监控**：观察进度条和百分比了解执行进度
8. **中途取消**：运行中可点击红色"取消测试"按钮停止

### 性能优化
9. **利用缓存**：测试文件未变化时使用 `--skip-generate` 快速启动
10. **清理缓存**：遇到测试列表异常时删除 `.test_cache.json` 强制更新
11. **端口清理**：遇到端口占用时，start_test.py 会自动处理

### 输出管理
12. **实时查看**：右侧控制台实时显示测试输出，自动滚动到最新
13. **颜色识别**：通过颜色快速识别测试结果（绿=通过，红=失败）
14. **清空输出**：测试前点击"清空"按钮清除旧输出

## 📊 统计信息

- **测试用例总数**：410+
- **层级深度**：5 级（模块 → 组 → 子组 → 文件 → 参数）
- **启动速度**：缓存命中 <1 秒，完整收集 ~15 秒
- **支持平台**：Windows（主要），Linux/Mac（部分功能）

## 🔗 相关文档

- **测试框架 README**：`../README.md`
- **参数校验设计**：`../engine_params/multimaterial_others_validation_design.md`
- **参数参考文档**：`../engine_params/process_parameters.md`

## 💡 提示与技巧

### 快捷键
- 浏览器刷新页面即可重新加载测试列表
- 使用浏览器的查找功能（Ctrl+F）可在输出中搜索

### 常见场景
- **选择所有失败的测试重跑**：在输出中搜索 "FAILED"，记录测试名称，手动选择
- **只运行某个模块**：展开对应模块，点击模块旁的复选框全选
- **快速验证环境**：选择 1-2 个简单测试先运行，确认环境正常

## 🎉 更新日志

### v2.0 (2025-12-16)
- ✅ 添加智能按钮切换（运行/取消）
- ✅ 添加实时进度条显示
- ✅ 添加进度百分比和数量统计
- ✅ 优化布局防止内容溢出
- ✅ 添加智能缓存机制
- ✅ 创建一键启动脚本
- ✅ 完善命令行参数支持
