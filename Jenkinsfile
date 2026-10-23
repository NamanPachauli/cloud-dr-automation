
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Validate Tools') {
            steps {
                bat 'python --version'
                bat 'docker --version'
                bat 'docker compose version'
            }
        }

        stage('Install Test Dependencies') {
            steps {
                bat 'python -m pip install -r app\\requirements.txt'
                bat 'python -m pip install pytest requests'
            }
        }

        stage('Build Application') {
            steps {
                bat 'docker compose build app'
            }
        }

        stage('Start Services') {
            steps {
                bat 'docker compose up -d localstack app'
            }
        }

        stage('Run Application Tests') {
            steps {
                bat 'set APP_TEST_URL=http://127.0.0.1:8082 && python -m pytest app\\test_main.py -v'
            }
        }
    }

    post {
        always {
            bat 'docker compose down'
            echo 'Review every stage result before considering this build successful.'
        }
    }
}
