pipeline {
    agent any
    environment {
        SERVICE = 'exchange'           // Docker Hub repository: <user>/exchange
        TRIVY_VERSION = '0.76.2'
        PYTHON_IMAGE = 'python:3.12-slim'
    }
    stages {
        stage('Test') {
            steps {
                // the Jenkins image has no Python: run pytest in a throwaway container.
                // The workspace goes in through stdin (tar), because the container runs on the
                // host's Docker and cannot mount a path that exists only inside the Jenkins container.
                sh '''
                    tar -c --exclude=.git --exclude=.venv . | docker run --rm -i $PYTHON_IMAGE sh -c "
                        mkdir /app && cd /app && tar -x &&
                        pip install --quiet --no-cache-dir -r requirements-dev.txt &&
                        python -m pytest -q
                    "
                '''
            }
        }
        // bottleneck: vulnerability scanning, the build stops on a HIGH or CRITICAL with a fix available
        stage('Scan Image') {
            steps {
                sh 'docker build -t $SERVICE:scan-$BUILD_ID .'
                sh 'docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v trivy-cache:/root/.cache aquasec/trivy:$TRIVY_VERSION image --timeout 15m --scanners vuln --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 $SERVICE:scan-$BUILD_ID'
            }
            post {
                always {
                    sh 'docker rmi $SERVICE:scan-$BUILD_ID || true'
                }
            }
        }
        stage('Build & Push Image') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credential',
                    usernameVariable: 'USERNAME',
                    passwordVariable: 'TOKEN')]) {
                    sh 'echo $TOKEN | docker login -u $USERNAME --password-stdin'
                    sh 'docker buildx create --use --platform=linux/arm64,linux/amd64 --node multi-platform-builder-$SERVICE --name multi-platform-builder-$SERVICE'
                    sh 'docker buildx build --platform=linux/arm64,linux/amd64 --push --tag $USERNAME/$SERVICE:latest --tag $USERNAME/$SERVICE:$BUILD_ID -f Dockerfile .'
                    sh 'docker buildx rm --force multi-platform-builder-$SERVICE'
                }
            }
        }
    }
}
