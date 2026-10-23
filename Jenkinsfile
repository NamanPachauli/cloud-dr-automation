
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

        stage('Initialize S3 Bucket') {
            steps {
                bat '''
                @echo off
                echo Waiting for LocalStack S3...

                for /L %%i in (1,1,30) do (
                    docker compose exec -T localstack awslocal s3api list-buckets >nul 2>&1
                    if not errorlevel 1 goto s3_ready
                    timeout /t 2 /nobreak >nul
                )

                echo ERROR: LocalStack S3 did not become ready.
                exit /b 1

                :s3_ready
                docker compose exec -T localstack awslocal s3api head-bucket --bucket cloud-dr-backups >nul 2>&1
                if errorlevel 1 (
                    docker compose exec -T localstack awslocal s3 mb s3://cloud-dr-backups
                    if errorlevel 1 exit /b 1
                )

                docker compose exec -T localstack awslocal s3 ls
                '''
            }
        }

        stage('Wait for Application') {
            steps {
                bat '''
                @echo off
                echo Waiting for application HTTP response...

                for /L %%i in (1,1,30) do (
                    python -c "import requests; r=requests.get('http://127.0.0.1:8082/', timeout=3); print(r.status_code); r.raise_for_status()" >nul 2>&1
                    if not errorlevel 1 goto app_ready
                    timeout /t 2 /nobreak >nul
                )

                echo ERROR: Application did not return a successful HTTP response.
                docker compose logs app
                exit /b 1

                :app_ready
                echo Application is responding.
                '''
            }
        }

        stage('Run Application Tests') {
            steps {
                bat 'set "APP_TEST_URL=http://127.0.0.1:8082" && python -m pytest app\\test_main.py -v'
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

