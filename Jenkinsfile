pipeline {
  agent { label 'windows' }
  options {
    timestamps()
    disableConcurrentBuilds()
  }
  parameters {
    string(name: 'BRANCH', defaultValue: 'release-1130', description: 'Jenkins parameter BRANCH (optional)')
    string(name: 'TAG_NAME', defaultValue: '7.0.0', description: 'Tag name to pass to builds (optional)')
    string(name: 'RTYPE', defaultValue: 'Beta', description: 'Release type to pass to builds (optional)')
  }
  environment {
    PYTHONUNBUFFERED = '1'
    JENKINS_BASE_URL = "${JENKINS_URL}"
    ARTIFACTS_DIR = "artifacts"
    DASHSCOPE_MODEL = "qwen-turbo"
    SKIP_TESTS = "false"
    TAG_NAME = "${TAG_NAME}"
    RTYPE = "${RTYPE}"
    BRANCH = "${BRANCH}"
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
        withCredentials([
          usernamePassword(credentialsId: 'jenkins-api-token', usernameVariable: 'JENKINS_USER', passwordVariable: 'JENKINS_TOKEN'),
          string(credentialsId: 'feishu-webhook', variable: 'FEISHU_WEBHOOK'),
          string(credentialsId: 'dashscope-api-key', variable: 'DASHSCOPE_API_KEY'),
          string(credentialsId: 'openai-key', variable: 'OPENAI_API_KEY'),
          usernamePassword(credentialsId: 'zentao-login', usernameVariable: 'ZENTAO_ACCOUNT', passwordVariable: 'ZENTAO_PASSWORD'),
          string(credentialsId: 'zentao-token', variable: 'ZENTAO_TOKEN_CRED')
        ]) {
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
if /I "%SKIP_TESTS%"=="true" set "SKIP_FLAG=--skip-tests"

REM Run orchestrator
python ci\\jenkins_release_orchestrator.py --platforms windows mac linux --artifacts-dir "%ARTIFACTS_DIR%" --branch "%BRANCH%" --tag-name "%TAG_NAME%" --rtype "%RTYPE%" %SKIP_FLAG%
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
