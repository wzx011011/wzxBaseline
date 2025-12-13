pipeline {
  agent any
  options {
    timestamps()
    disableConcurrentBuilds()
  }
  parameters {
    string(name: 'BRANCH', defaultValue: '', description: 'Jenkins parameter BRANCH (optional)')
    string(name: 'TAG_NAME', defaultValue: '', description: 'Tag name to pass to builds (optional)')
    string(name: 'RTYPE', defaultValue: '', description: 'Release type to pass to builds (optional)')
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
        sh 'python -m pip install -U pip'
        sh 'python -m pip install -r requirements.txt'
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
          sh '''#!/usr/bin/env bash
set -e
export BRANCH="${BRANCH}"
export TAG_NAME="${TAG_NAME}"
export RTYPE="${RTYPE}"
python ci/jenkins_release_orchestrator.py --platforms windows mac linux --artifacts-dir "${ARTIFACTS_DIR}" --branch "${BRANCH}" --tag-name "${TAG_NAME}" --rtype "${RTYPE}"
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
