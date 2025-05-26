# Build script for multi-platform Docker image

# Set your Docker Hub username
$DOCKER_USERNAME = "hazemhlawa"
$IMAGE_NAME = "dbm"
$VERSION = "1.0.0"

# Create builder instance if it doesn't exist
docker buildx create --name dbm-builder --use

# Build and push multi-platform image
docker buildx build --platform linux/amd64,linux/arm64,linux/arm/v7 `
    -t "${DOCKER_USERNAME}/${IMAGE_NAME}:latest" `
    -t "${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}" `
    --push `
    .

Write-Host "Multi-platform build completed and pushed to Docker Hub"
