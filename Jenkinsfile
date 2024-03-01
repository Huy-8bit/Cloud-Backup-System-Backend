pipeline {
    agent any

    environment {

    }

    stages {
        steps{
            sh 'docker-compose up --build'
        }

        


    post {
        always {
            Cleanup()
        }
    }
}
