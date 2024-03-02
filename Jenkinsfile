pipeline {
    agent any

    stages {


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


}
