pipeline {
    agent {
        docker {
            image 'python:3.11-slim'
            args '-v /var/run/docker.sock:/var/run/docker.sock -u root'
        }
    }
    environment {
        DOCKERHUB_CREDENTIALS = credentials('dockerhub')
    }
    stages {
        stage('Clone Repository') {
            steps {
                git branch: 'main', credentialsId: 'github', url: 'https://github.com/hazemhlawa/dbm.git'
            }
        }
        stage('Build Docker Image') {
            steps {
                sh 'docker build -t hazemhlawa/dbm:v3.1 .'
            }
        }
        stage('Push to DockerHub') {
            steps {
                sh '''
                echo $DOCKERHUB_CREDENTIALS_PSW | docker login -u $DOCKERHUB_CREDENTIALS_USR --password-stdin
                docker push hazemhlawa/dbm:v3.1
                '''
            }
        }
        stage('Deploy to EC2') {
            steps {
                sshagent(credentials: ['ec2-ssh-credentials']) {
                    sh '''
                    ssh -o StrictHostKeyChecking=no -i cicd-ssh-key.pem ubuntu@54.158.239.227 << EOF
                        cd ~/FIRST_DBM/DBM
                        docker-compose pull
                        docker-compose up -d
                        exit
                    EOF
                    '''
                }
            }
        }
    }
    post {
        always {
            cleanWs()
        }
    }
}
