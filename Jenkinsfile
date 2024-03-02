pipeline {
    agent any
    
    stages {
        stage('Build and Run') { // Corrected: Added a stage block here
            // steps {
            //     sh 'docker build -t huy8bit/web:latest .'
            //     // run redis container
            //     sh 'docker container run -d -p 6379:6379 redis:latest'
            //     // run mongo container
            //     sh 'docker container run -d -p 27017:27017 mongo:latest'
            //     // run web container
            //     sh 'docker container run -d -p 8000:8000 huy8bit/web:latest'
            // }
            steps {
                sh 'docker-compose up --build'
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
