# Build script for Docker image targeting linux/amd64 only

# Set your Docker Hub username
$DOCKER_USERNAME = "hazemhlawa"
$IMAGE_NAME = "dbm"
$VERSION = "1.0.0"

# Create builder instance if it doesn't exist
docker buildx create --name dbm-builder --use

# Build and push linux/amd64 image
docker buildx build --platform linux/amd64 `
    -t "${DOCKER_USERNAME}/${IMAGE_NAME}:latest" `
    -t "${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}" `
    --push `
    .

Write-Host "linux/amd64 build completed and pushed to Docker Hub"
