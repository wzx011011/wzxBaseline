## Jenkins 跨平台打包+回传流水线

此目录提供 `jenkins_release_orchestrator.py`，用于 Jenkins Pipeline 调用三个现有的 Windows/Mac/Linux 任务、汇总失败日志（可选用 LLM）、通过飞书机器人通知，成功后下载测试包并执行测试命令，最后把版本变更和测试关注点回传到禅道。

### 所需环境变量

- `JENKINS_BASE_URL` / `JENKINS_USER` / `JENKINS_TOKEN`：主 Jenkins 实例信息。
- `JENKINS_JOB_WINDOWS` / `JENKINS_JOB_MAC` / `JENKINS_JOB_LINUX`：三个既有跨平台任务的名称。
- `JENKINS_ARTIFACT_WINDOWS` / `JENKINS_ARTIFACT_MAC` / `JENKINS_ARTIFACT_LINUX`（可选）：希望下载的构件路径或文件名，未设置则取首个构件。
- `JENKINS_PARAMS_WINDOWS` / `JENKINS_PARAMS_MAC` / `JENKINS_PARAMS_LINUX`（可选）：任务参数，JSON 字符串。
- `FEISHU_WEBHOOK`：飞书机器人 Webhook 地址。
- `DASHSCOPE_API_KEY`（推荐）/ `DASHSCOPE_API_BASE` / `DASHSCOPE_MODEL`：通义千问（OpenAI 兼容模式）用于失败日志与改动范围的 AI 总结，默认 `https://dashscope.aliyuncs.com/compatible-mode/v1` + `qwen-turbo`。未提供时回退读取 `OPENAI_API_KEY` / `OPENAI_API_BASE` / `OPENAI_MODEL`。
- `CHANGES_REPO`（可选）：用于计算改动范围的 Git 仓库路径或远程地址，未提供则使用当前仓库。脚本会在 `git log/diff` 前执行 `fetch`。
- `RUN_TESTS`（可选）：显式控制是否执行测试（`true/false` 等）；优先级高于 `--skip-tests`。
- `TEST_COMMAND`（可选）：成功后执行的测试命令，默认 `pytest -q`。脚本会注入 `ARTIFACTS_DIR` 与 `ARTIFACT_<PLATFORM>` 环境变量供测试脚本读取。
- `ZENTAO_BASE_URL` / `ZENTAO_ACCOUNT` / `ZENTAO_PASSWORD`（可选）：禅道 API 访问信息。
- `ZENTAO_BUILD_ID`：需要回传的禅道版本/构建 ID。
- `ZENTAO_EXECUTION_ID`（可选）：指定执行/迭代 ID；当未提供 `ZENTAO_BUILD_ID` 时，脚本会在该执行下按名称查找/创建版本。
- `ZENTAO_BUILD_NAME`（可选）：新建版本名称，默认使用当前版本引用（`CURRENT_REF` 自动解析后）。
- `ZENTAO_PRODUCT_ID`（可选，禅道 20.8 开源版建议提供）：创建版本时指定产品 ID，避免接口校验失败。
- `ZENTAO_TOKEN`（可选）：预置的禅道 API token，提供时跳过登录流程。
- `ZENTAO_OBJECT_TYPE` / `ZENTAO_OBJECT_ID`（可选）：需要追加评论的禅道对象（默认 build）。
- `PREVIOUS_REF` / `CURRENT_REF`（可选）：用于生成改动范围的 Git diff 起止引用，未提供则使用最近两个 tag 或 `HEAD~1..HEAD`。

若仅有执行 ID（迭代）而没有现成的版本 ID，可设置 `ZENTAO_EXECUTION_ID` 和可选的 `ZENTAO_BUILD_NAME`，脚本会在该执行下按名称查找，若不存在则自动创建版本后再回传。
在禅道开源版 20.8 中，创建版本接口通常要求提供产品 ID，建议设置 `ZENTAO_PRODUCT_ID`。
脚本对禅道 API 增加了常见路径/协议兼容处理（自动尝试 `http/https` 和 `/zentao` 前缀的 API 路径），用于应对 20.8 开源版默认路径返回 404 的情况；同时支持直接提供 `ZENTAO_TOKEN` 以跳过登录。
REST 登录优先使用 `/api.php/v1/tokens`，若返回 401 请核对账号密码或直接提供 `ZENTAO_TOKEN`。

### Jenkinsfile 示例（每日定时）

```groovy
pipeline {
  agent any
  triggers { cron('H 2 * * *') } // 每天随机分钟的 02:00 左右
  options { timestamps() }
  environment {
    PYTHONUNBUFFERED = '1'
  }
  stages {
    stage('Checkout') {
      steps { checkout scm }
    }
    stage('Install deps') {
      steps {
        sh 'python -m pip install -U pip'
        sh 'python -m pip install -r requirements.txt'
      }
    }
    stage('Cross-platform build & test') {
      steps {
        withCredentials([
          usernamePassword(credentialsId: 'jenkins-main-token', usernameVariable: 'JENKINS_USER', passwordVariable: 'JENKINS_TOKEN'),
          string(credentialsId: 'feishu-webhook', variable: 'FEISHU_WEBHOOK'),
          string(credentialsId: 'dashscope-api-key', variable: 'DASHSCOPE_API_KEY'),
          usernamePassword(credentialsId: 'zentao-login', usernameVariable: 'ZENTAO_ACCOUNT', passwordVariable: 'ZENTAO_PASSWORD')
        ]) {
          sh '''
            export JENKINS_BASE_URL=https://jenkins.example.com
            export JENKINS_JOB_WINDOWS=build-windows
            export JENKINS_JOB_MAC=build-mac
            export JENKINS_JOB_LINUX=build-linux
            python ci/jenkins_release_orchestrator.py --platforms windows mac linux --artifacts-dir artifacts
          '''
        }
      }
    }
  }
}
```

根据节点类型替换 `sh` 为 `bat` 即可在 Windows 代理上运行。

### 本地/手动运行

```bash
python ci/jenkins_release_orchestrator.py --platforms windows mac linux --skip-tests --dry-run
```

- `--dry-run` 仅打印计划动作，不访问 Jenkins。
- `--skip-tests` 只做构建与通知，不执行测试命令；也可通过 `--run-tests false` / 环境变量 `RUN_TESTS=false` 控制。

### 流程概要

1. 触发三个 Jenkins 任务并等待完成；失败时截取末尾日志（可调用 LLM）并推送飞书。
2. 全部成功后下载构件到 `artifacts/<platform>/`。
3. 注入构件路径为环境变量执行测试命令。
4. 汇总构建、测试、Git 改动范围和测试关注点，将结果推送飞书，并调用禅道 API 更新对应版本/构建，必要时追加评论。
