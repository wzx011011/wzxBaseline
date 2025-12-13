pipeline {
  agent any
  options {
    timestamps()
    disableConcurrentBuilds()
  }
  environment {
    PYTHONUNBUFFERED = '1'
    JENKINS_BASE_URL = "${JENKINS_URL}"
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
python ci/jenkins_release_orchestrator.py --platforms windows mac linux
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
