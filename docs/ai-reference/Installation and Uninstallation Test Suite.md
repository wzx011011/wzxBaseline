## Installation and Uninstallation Test Suite

本测试计划用于规范客户端安装/卸载套件的自动化测试，采用 pytest 作为测试框架。

---

### 1. 测试目标

- 验证安装程序在不同场景下可以成功完成安装、升级、修复和卸载。
- 确保安装/卸载过程不会破坏系统环境，不留下严重的垃圾数据或错误配置。
- 验证安装过程中的错误处理、回滚机制和日志记录是否符合预期。
- 为 CI/CD Pipeline 提供稳定的回归测试集，支持 Allure 等报告工具。

---

### 2. 测试范围

- 安装场景
  - 全新安装（系统无残留）
  - 覆盖安装（已有旧版本）
  - 升级安装（从低版本升级到高版本）
  - 修复安装（安装目录或关键文件损坏后的重装/修复）
- 卸载场景
  - 正常卸载
  - 卸载后重新安装
  - 部分文件被手工删除后的卸载
- 配置与数据
  - 安装路径配置（自定义路径、多磁盘）
  - 用户数据与配置文件保留策略
  - 日志文件和缓存目录处理
- 系统集成
  - 环境变量、PATH 注册
  - 桌面快捷方式、开始菜单项、文件关联
  - 注册表项写入与清理（Windows）

不在本计划范围内的内容（如深度性能测试、功能业务测试）由其他测试套件覆盖。

---

### 3. 测试环境

- 操作系统：
  - Windows 10/11（x64）
  - 如有需要，可扩展到 macOS / Linux
- 权限：
  - 管理员权限安装/卸载
  - 普通用户安装（如安装器支持）
- 安装来源：
  - CI 产出的安装包（Jenkins 构建产物）
  - 本地构建安装包（开发调试）

环境准备由 pytest fixture 负责，例如：

- `installer_path`：定位当前测试用安装包路径。
- `install_root`：测试安装根目录（临时目录，测试完成后清理）。
- `os_env`：按需要注入环境变量（如 PATH、代理设置等）。

---

### 4. 用例设计（pytest 视角）

#### 4.1 目录结构建议

```text
tests/
  installation/
    conftest.py
    test_fresh_install.py
    test_upgrade_install.py
    test_repair_install.py
    test_uninstall.py
    test_integration_shortcuts.py
``+

#### 4.2 关键 fixture

- `installer_path`：返回当前测试使用的安装包。
- `clean_env`：在每次测试前清理残留（卸载 + 删除安装目录、缓存目录、注册表残留）。
- `installed_app`：执行一次安装，yield 后负责卸载和清理。
- `os_info`：封装当前系统信息（版本、语言、是否管理员）。

#### 4.3 核心测试场景

1. 全新安装
   - 前提：系统无残留（由 `clean_env` 保证）。
   - 步骤：运行安装器，选择默认选项或命令行静默参数。
   - 断言：
     - 安装目录存在且文件完整。
     - 主程序可启动且退出码为 0。
     - 必要的环境变量/快捷方式/注册表项存在。

2. 升级安装
   - 前提：已安装旧版本。
   - 步骤：使用较新版本安装包直接运行。
   - 断言：
     - 安装后版本号为新版本。
     - 用户配置/数据得以保留。
     - 旧版本相关残留（如旧路径）符合预期策略。

3. 修复安装
   - 前提：已有安装，但关键文件被删除或损坏。
   - 步骤：再次运行安装器，选择修复/重装。
   - 断言：
     - 缺失文件被恢复。
     - 注册表和环境变量保持一致。

4. 正常卸载
   - 前提：已有安装。
   - 步骤：通过卸载程序或命令行参数执行卸载。
   - 断言：
     - 程序目录被移除或只剩允许保留的用户数据。
     - 环境变量、PATH、快捷方式、注册表项被清理。

5. 卸载后重新安装
   - 前提：已完成一次正常卸载。
   - 步骤：再次执行全新安装。
   - 断言：
     - 安装过程顺利，无残留导致的冲突。
     - 程序可正常运行。

6. 错误与回滚
   - 模拟磁盘空间不足或权限不足（如将安装目录切换为只读）。
   - 断言：
     - 安装失败时给出清晰错误信息。
     - 没有留下半安装状态（不会出现半拉子的目录或部分注册表项）。

---

### 5. pytest 套件管理（单一 Suite）

本安装/卸载测试只作为一个整体套件管理，不再按 install/uninstall/upgrade 等进行拆分。

- 统一标记：
  - 所有安装/卸载相关用例统一加上 `@pytest.mark.installation_suite`。

- 目录建议：
  - 在现有 `test_framework` 目录下，为安装/卸载套件单独建立子目录，例如：
    - `test_framework/installation_suite/`
  - 该目录中的所有用例都属于同一个 Suite，并统一使用 `@pytest.mark.installation_suite`。

- 运行示例：
  - 本地运行整个安装/卸载套件：
    - `pytest test_framework -m installation_suite`
  - 在 CI（例如 Jenkins）中：
    - 测试命令中使用 `-m installation_suite`，并指定 Allure 结果输出目录。

---

### 6. 报告与追踪

- 使用 pytest + Allure 生成报告：
  - 所有安装/卸载用例输出到统一的 `allure-results` 目录。
  - Jenkins Pipeline 中在测试前清理旧的 `allure-results`，避免历史污染。
- 每个用例应包含：
  - 前置条件描述（前提状态）。
  - 步骤说明（命令行参数、交互选择）。
  - 预期结果（文件/目录/注册表/进程状态等）。

---

### 7. 针对 CrealityPrint_7.0.1.4171_Beta.exe（NSIS）的具体方案

- 安装包信息：
  - 类型：NSIS 安装包
  - 默认路径：`D:\迅雷下载\CrealityPrint_7.0.1.4171_Beta.exe`

- 安装前签名校验：
  - 在开始任何安装用例前，先校验安装包的数字签名。
  - Windows 下可使用 PowerShell 的 `Get-AuthenticodeSignature`：
    - `powershell -Command "Get-AuthenticodeSignature 'D:\迅雷下载\CrealityPrint_7.0.1.4171_Beta.exe' | ConvertTo-Json"`
  - 关键断言：
    - `Status` 为 `Valid`。
    - 颁发者信息中的公司名称包含预期的 Publisher（例如 Creality 或内部签名实体）。
  - 在 pytest 中建议：
    - 为 `installation_suite` 增加一个前置用例或 fixture，例如 `verify_installer_signature(installer_path)`：
      - 如果签名无效或缺失，直接 `pytest.fail`，阻止后续安装相关用例执行。

- NSIS 常用参数约定：
  - 静默安装：`/S`
  - 自定义安装目录（注意 `/D=` 必须是最后一个参数）：`/D=C:\Program Files\CrealityPrint`
  - 典型命令示例：
    - `CrealityPrint_7.0.1.4171_Beta.exe /S /D=C:\Program Files\CrealityPrint`

- 卸载命令约定（NSIS 默认）：
  - 安装后会生成卸载程序，通常位于：
    - `C:\Program Files\CrealityPrint\uninst.exe` 或类似路径
  - 静默卸载：
    - `"C:\Program Files\CrealityPrint\uninst.exe" /S`

- 与 installation_suite 的对应关系（建议实现）：
  - `installer_path` fixture：
    - 通过 `--installer-path` 指向 `D:\迅雷下载\CrealityPrint_7.0.1.4171_Beta.exe`。
  - `installed_app` fixture：
    - 使用 `subprocess.run` 执行安装命令，例如：
      - `CrealityPrint_7.0.1.4171_Beta.exe /S /D={install_root}`
    - yield 之后调用卸载程序：
      - `{install_root}\uninst.exe /S`
  - 核心用例：
    - `test_fresh_install`：全新静默安装 + 启动一次主程序验证。
    - `test_uninstall_then_reinstall`：安装 -> 卸载 -> 再安装，验证整个流程可重复。

- 建议的运行方式：
  - 本地：
    - `pytest test_framework -m installation_suite --installer-path "D:\迅雷下载\CrealityPrint_7.0.1.4171_Beta.exe"`
  - CI：
    - 将安装包下载到固定目录（例如 `artifacts/installer/`），再通过 `--installer-path` 指向该路径。

---

### 8. 后续扩展

- 增加多语言环境（简体中文、英文等）下的安装/卸载验证。
- 针对不同发行渠道（官网安装包、自动更新包等）编写专门用例。
- 将安装/卸载测试集成到发布流程的 Gate 中，在发布前强制通过。

