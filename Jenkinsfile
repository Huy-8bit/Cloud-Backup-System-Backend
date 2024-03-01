pipeline {
    agent any
    
    stages {
        stage('Build and Run') { // Corrected: Added a stage block here
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
