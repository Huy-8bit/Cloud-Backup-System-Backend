pipeline {
    agent any
    
    stages {
        steps ('run docker-compose') {
            sh 'docker-compose up --build'
        }
    }

    post {
        always {
            Cleanup()
        }
    }
}
