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
    POWERSHELL_HOME = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0"
    PYTHONHOME = "C:\\Users\\cx2056\\AppData\\Local\\Programs\\Python\\Python310"
    PATH = "C:\\Windows\\System32;C:\\Windows\\System32\\WindowsPowerShell\\v1.0;C:\\Users\\cx2056\\AppData\\Local\\Programs\\Python\\Python310;${PATH}"
  }
  stages {
    stage('Checkout') {
      steps { checkout scm }
    }
    stage('Install deps') {
      steps {
        powershell '''
python -m pip install -U pip
python -m pip install -r requirements.txt
'''
      }
    }
    stage('Trigger builds + test + notify') {
      steps {
              withCredentials([sshUserPrivateKey(credentialsId: 'cxsw-ssh-key', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')]) {
          powershell '''
# Prefer injected token over password login when provided
if (-not [string]::IsNullOrEmpty($env:ZENTAO_TOKEN)) {
  $env:ZENTAO_TOKEN = $env:ZENTAO_TOKEN
} elseif (-not [string]::IsNullOrEmpty($env:ZENTAO_TOKEN_CRED)) {
  $env:ZENTAO_TOKEN = $env:ZENTAO_TOKEN_CRED
}

# LLM config: prefer DashScope, fallback to OpenAI if not set
if ([string]::IsNullOrEmpty($env:DASHSCOPE_API_KEY)) {
  if (-not [string]::IsNullOrEmpty($env:OPENAI_API_KEY)) {
    $env:OPENAI_API_KEY = $env:OPENAI_API_KEY
  }
} else {
  $env:DASHSCOPE_API_KEY = $env:DASHSCOPE_API_KEY
}

# Test control
$cmdArgs = @(
  'ci\\jenkins_release_orchestrator.py'
  '--platforms' 'windows' 'mac' 'linux'
  '--artifacts-dir' $env:ARTIFACTS_DIR
  '--branch' $env:BRANCH
  '--tag-name' $env:TAG_NAME
  '--rtype' $env:RTYPE
)
if ($env:SKIP_TESTS -eq 'true') {
  $cmdArgs += '--skip-tests'
}

# Run orchestrator
& python @cmdArgs
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
