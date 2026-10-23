
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Validate Project Files') {
            steps {
                bat 'python --version'
                bat 'docker --version'
                bat 'docker compose version'
            }
        }

        stage('Build Application') {
            steps {
                bat 'docker compose build app'
            }
        }

        stage('Run Health Check') {
            steps {
                bat 'python scripts\\health_check.py'
            }
        }
    }

    post {
        always {
            echo 'Cloud DR pipeline finished. Review stage results before marking the build successful.'
        }
    }
}
