pipeline {
    agent any

    environment {
        // Đặt biến môi trường nếu cần
        DOCKER_COMPOSE_VERSION = '1.29.2'
    }

    stages {
        stage('Checkout') {
            steps {
                script {
                    sh 'git checkout Development'
                }
            }
        }

        stage('Build and Deploy') {
            steps {
                script {
                    // Chạy docker-compose
                    sh 'docker-compose -f docker-compose.yml up --build -d'
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

    // post {
    //     always {
    //         // Các bước để thực hiện sau cùng, ví dụ như gửi thông báo
    //         echo 'Quy trình CI/CD đã hoàn thành.'
    //     }
    // }
}
