# CrealityPrint 性能冒烟流水线建设说明

## 1. 建设目标

在开发侧 Jenkins 节点 `windows-tester1` 新建一条独立的性能冒烟流水线，用少量固定 3MF 模型快速验证 CrealityPrint 的核心性能流程是否正常。

首期使用 3 个模型。每个模型独立生成一条 pytest 用例，执行以下流程：

1. 打开并导入 3MF 模型；
2. 执行首次切片，并等待首帧渲染完成；
3. 导出 `.gcode.3mf`；
4. 记录打开、首次切片和导出的耗时及成功状态；
5. 生成 Allure 和性能结果文件。

首期不启用移动模型后的二次切片测试，即 `ENABLE_SECOND_SLICE=false`。

## 2. 总体方案

```text
Jenkins 性能冒烟 Job
  -> 在 windows-tester1 上运行
  -> 从指定上游 Job 下载 CrealityPrint 安装包
  -> 从专属 HTTP 目录发现并缓存 3MF 模型
  -> 一个 3MF 文件展开为一条 pytest 性能用例
  -> 执行打开、首次切片、导出流程
  -> 发布 Allure，并归档性能报告和切片软件日志
```

本方案对应以下内容：

- Jenkins Job：`CrealityPrint_Performance_Smoke`
- Pipeline 文件：仓库根目录下的 `Jenkinsfile_performance_smoke`（已创建）
- 远程模型目录：`http://172.20.180.14/shared/performance_smoke_3mf/`
- 开发机本地缓存：`test_framework/artifacts/http_3mf_smoke`

模型文件不提交到 Git 代码仓，Git 中只保存 Pipeline、测试代码和本说明文件。

## 3. 模型数量与自动生成用例规则

当前 `test_framework/performance/case/test_slice.py` 会递归读取 `HTTP_3MF_ROOT` 指定目录中的 `.3mf` 文件，并通过 pytest 参数化机制生成用例。

对应关系如下：

```text
远程目录中有 3 个 .3mf  -> 收集为 3 条用例
以后增加第 4 个 .3mf    -> 下次运行自动收集为 4 条用例
删除其中 1 个 .3mf       -> 下次运行自动减少 1 条用例
其他扩展名文件            -> 不生成性能用例
```

支持在远程根目录下继续建立子目录，脚本会递归发现子目录里的 `.3mf` 文件。

增加模型时不需要增加新的 Python 测试函数，也不需要修改 `TEST_COMMAND`。只需要把模型上传到性能冒烟专属目录，然后重新运行流水线。

### 3.1 首期模型选择建议

首期 3 个模型建议覆盖不同负载：

1. 普通模型：体积较小、稳定成功，用于识别整体功能故障；
2. 中等复杂模型：例如哥斯拉，用于观察模型树、渲染和常规复杂切片；
3. 大型或铺满盘模型：例如 Tiger，用于观察高负载切片和导出。

已经确认属于越界、无效数据或必然无法切片的模型，不应放入首期性能冒烟集合，否则会让冒烟流水线稳定失败。

## 4. 模型目录维护规则

远程目录建议只保存当前需要执行的冒烟模型，不要放完整的几百个性能模型。

建议结构：

```text
performance_smoke_3mf/
  normal/
    normal_model.3mf
  complex/
    godzilla.3mf
  stress/
    tiger_full_plate.3mf
```

维护注意事项：

- 文件名尽量保持唯一、简短，并避免频繁修改；
- 替换模型内容时优先使用新文件名；
- 脚本使用远程文件大小校验本地缓存。如果同名模型内容发生变化但文件大小完全相同，旧缓存可能不会自动更新；此时应更换文件名或清理 `http_3mf_smoke` 缓存；
- 从远程目录删除模型后，下次不会再生成对应测试用例，但开发机上的旧缓存文件可能继续保留，不影响本次用例收集；
- 不要把冒烟目录放在完整性能目录内部，否则完整性能流水线递归扫描时可能重复执行这些模型。

## 5. Jenkins Job 建议参数

| 参数 | 建议值 | 说明 |
| --- | --- | --- |
| `AGENT_LABEL` | `windows-tester1` | 开发侧 GUI 自动化节点 |
| `JOB_NAME` | 按实际产品构建流水线填写 | 下载被测安装包的上游 Job |
| `BUILD_ID` | `lastSuccessfulBuild` 或指定编号 | 被测产品构建编号 |
| `ARTIFACT_PATH` | 空或指定 ZIP | 上游存在多个产物时使用 |
| `PLATFORM` | `windows` | 被测平台 |
| `TEST_COMMAND` | `performance/case/test_slice.py::test_feishu_slice -m performance` | 只运行模型性能流程 |
| `HTTP_3MF_ROOT` | `http://172.20.180.14/shared/performance_smoke_3mf/` | 冒烟模型来源 |
| `HTTP_3MF_DOWNLOAD_DIR` | `artifacts/http_3mf_smoke` | 相对于 `test_framework` 的模型缓存路径 |
| `ENABLE_SECOND_SLICE` | `false` | 首期不运行二次切片 |
| `IDLE_NO_SLICING_RETRIES` | `1` | `-1/no_slicing` 时允许重试一次 |
| `LOAD_TIMEOUT_SECONDS` | `300` | 单个模型打开超时，单位为秒 |
| `ALLURE_CMD` | `Allure` | Jenkins 全局 Allure 工具名 |

性能冒烟应允许对同一个产品包重复运行，因此不建议启用 `SKIP_TESTED_BUILD`，也不应固定传入 `--skip-tested-build`。

## 6. Pipeline阶段建议

当前 `Jenkinsfile_performance_smoke` 包含以下阶段：

1. `Checkout`：拉取包含最新产品侧耗时统计适配的自动化分支；
2. `Install deps`：安装 Python 依赖并清理本 Job 的旧 Allure 临时结果；
3. `Download artifact and run smoke tests`：下载、解压产品包并执行性能冒烟；
4. `Allure results`：无论测试是否失败，都尽量发布已有 Allure 结果；
5. `Archive performance reports`：归档 CSV、JSON、HTML、图表、标准输出日志和 CrealityPrint 日志。

可复用 `Jenkinsfile2` 中的产品包下载、解压、测试运行和报告归档逻辑，但测试节点、模型目录、测试命令和报告名称应改为冒烟专用配置。

## 7. Jenkins页面配置

可以复制现有 Jenkins Job，但复制后必须检查：

1. SCM仓库仍为 `C3DBaseline`；
2. Branch Specifier 指向包含最新耗时统计修改的分支；
3. Script Path 从原来的 `Jenkinsfile_params` 或 `Jenkinsfile2` 改为 `Jenkinsfile_performance_smoke`；
4. 执行节点为 `windows-tester1`；
5. 删除参数功能测试专用的 `TEST_QUALITY`、`TEST_SPEED` 等复选框；
6. 增加本说明第5节列出的性能冒烟参数；
7. 检查是否复制了不需要的定时触发器、上游触发器和通知配置。

页面参数由 Pipeline 文件中的 `parameters {}` 定义。只在 Jenkins 页面临时修改参数定义并不可靠，后续加载 Pipeline 文件时可能被文件中的定义重新更新。

## 8. GUI节点与并发要求

`#22.txt` 已证明 `windows-tester1` 能够运行 CrealityPrint GUI 自动化，但性能测试期间必须避免其他任务干扰。

要求：

- 同一时间只能有一条任务控制该节点上的 CrealityPrint GUI；
- 参数测试流水线和性能冒烟流水线不能并发运行；
- 最好将节点的 GUI 测试执行器限制为1，或使用 Jenkins Lockable Resources 为相关 Job 加同一把锁；
- 测试期间不要进行远程人工操作、文件复制、杀毒全盘扫描或其他高负载任务；
- 开发机性能结果应建立自己的历史基线，不与测试侧机器的绝对耗时直接比较。

## 9. 报告与验收标准

首次配置完成后，应确认：

1. 日志打印的 `base_url` 是性能冒烟专属目录；
2. pytest 收集数量与远程目录中的 `.3mf` 数量一致，首期应为3条；
3. 每个模型都有打开、首次切片和导出结果；
4. 首次切片结束时间包含首帧渲染完成；
5. Allure中显示3条独立的模型用例；
6. Jenkins归档了性能CSV、趋势文件、`slicer_stdout` 和 CrealityPrint日志；
7. 某个模型失败时，Allure和已有性能结果仍能发布；
8. 同一个产品构建可以被手动重复执行。

## 10. 首期实施范围

首期实施内容：

- 创建3模型的专属远程目录；
- 新增性能冒烟 Pipeline 文件（仓库侧已完成，提交合入后由 Jenkins 使用）；
- 复制并配置开发侧 Jenkins Job；
- 验证3条用例自动收集和完整执行；
- 验证打开、首次切片、导出耗时以及日志、报告归档。

首期不包含：

- 二次切片性能；
- 几百模型的完整性能回归；
- 跨机器绝对耗时比较；
- 自动挑选模型；
- 失败模型的自动替换。
