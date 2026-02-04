pipeline {
  agent { label 'windows' }
  options {
    timestamps()
    disableConcurrentBuilds()
  }
  triggers {
    cron('0 1 * * *') // 每天凌晨1点
  }
  parameters {
    string(name: 'BRANCH', defaultValue: 'release-260330', description: 'Jenkins parameter BRANCH (optional)')
    string(name: 'WEB_BRANCH', defaultValue: 'release-260330', description: 'Jenkins parameter BRANCH (optional)')
    string(name: 'TAG_NAME', defaultValue: '7.1.0', description: 'Tag name to pass to builds (optional)')
    string(name: 'RTYPE', defaultValue: 'Beta', description: 'Release type to pass to builds (optional)')
    booleanParam(name: 'RUN_TESTS', defaultValue: true, description: 'Whether to run tests')
  }
  environment {
    PYTHONUNBUFFERED = '1'
    JENKINS_BASE_URL = "${JENKINS_URL}"
    ARTIFACTS_DIR = "artifacts"
    DASHSCOPE_MODEL = "qwen-turbo"
    RUN_TESTS = "${RUN_TESTS}"
    SKIP_TESTS = "false"
    TAG_NAME = "${TAG_NAME}"
    RTYPE = "${RTYPE}"
    BRANCH = "${BRANCH}"
    WEB_BRANCH = "${WEB_BRANCH}"
    POWERSHELL_HOME = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0"
  }
  stages {
    stage('Checkout') {
      steps { checkout scm }
    }
    stage('Install deps') {
      steps {
        bat '''
python -m pip install -U pip
python -m pip install -r requirements.txt
'''
      }
    }
    stage('Trigger builds + test + notify') {
      steps {
              withCredentials([sshUserPrivateKey(credentialsId: 'cxsw-ssh-key', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')]) {
          bat '''
@echo off
setlocal enabledelayedexpansion

REM Prefer injected token over password login when provided
if not "%ZENTAO_TOKEN%"=="" (
  set "ZENTAO_TOKEN=%ZENTAO_TOKEN%"
) else if not "%ZENTAO_TOKEN_CRED%"=="" (
  set "ZENTAO_TOKEN=%ZENTAO_TOKEN_CRED%"
)

REM LLM config: prefer DashScope, fallback to OpenAI if not set
if "%DASHSCOPE_API_KEY%"=="" (
  if not "%OPENAI_API_KEY%"=="" (
    set "OPENAI_API_KEY=%OPENAI_API_KEY%"
  )
) else (
  set "DASHSCOPE_API_KEY=%DASHSCOPE_API_KEY%"
)

REM Test control
set "SKIP_FLAG="
if /I "%RUN_TESTS%"=="false" (
  set "SKIP_FLAG=--run-tests false"
) else if /I "%SKIP_TESTS%"=="true" (
  set "SKIP_FLAG=--run-tests true"
)

REM Run orchestrator
python ci\\jenkins_release_orchestrator.py --platforms windows macos_x86 macos_arm64 linux --artifacts-dir "%ARTIFACTS_DIR%" --branch "%BRANCH%" --web-branch "%WEB_BRANCH%" --tag-name "%TAG_NAME%" --rtype "%RTYPE%" %SKIP_FLAG%
endlocal
'''
        }
      }
    }
  }
  post {
    failure {
      echo 'Pipeline failed; check Feishu notifications for details.'
    }
  }
}
