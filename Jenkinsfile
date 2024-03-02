pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build and Run') {
            steps {
                script {
                    docker.image('docker/compose:1.29.2').inside {
                        sh 'docker-compose up --build'
                    }
                }
            }
        }
    }


    post {
        always {
            // Corrected: Ensure this is a valid step or script
            // Cleanup() // This needs to be a valid Jenkins command or script block
            echo 'Cleanup steps go here'
        }
    }
}
