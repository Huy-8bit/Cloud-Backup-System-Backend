pipeline {
    agent any

    environment {
        // Đặt biến môi trường nếu cần
        // DOCKER_COMPOSE_VERSION = '1.29.2'
    }

    stages {
        // stage('Checkout') {
        //     steps {
        //         script {
        //             sh 'git checkout Development'
        //         }
        //     }
        // }

        stage('Build and Deploy') {
            steps {
                script {
                    // Chạy docker-compose
                    sh 'docker-compose up --build'
                }
            }
        }

    //     stage('Cleanup') {
    //         steps {
    //             script {
    //                 // Dọn dẹp sau khi deploy (tùy chọn)
    //                 sh 'docker-compose down'
    //             }
    //         }
    //     }
    // }

    post {
        always {
            Cleanup()
        }
    }
}
