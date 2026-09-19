pipeline {
  agent any

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Test') {
      steps {
        sh 'python -m venv .venv'
        sh '. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements-cpu.txt && pytest -q'
      }
    }

    stage('Docker Build') {
      steps {
        sh 'docker build -t ai-neural-style-transfer:$BUILD_NUMBER .'
      }
    }
  }

  post {
    always {
      sh 'rm -rf .venv || true'
    }
  }
}
