#!/bin/bash
set -e

# Set your Docker Hub username
DOCKER_USERNAME="hazemhlawa"
IMAGE_NAME="dbm"
VERSION="1.0.0"

# Create builder instance if it doesn't exist
docker buildx create --name dbm-builder --use || true

# Remove any existing builder to avoid caching issues
docker buildx rm dbm-builder || true
docker buildx create --name dbm-builder --use

# Build and push linux/amd64 image
docker buildx build --platform linux/amd64 \
    --no-cache \
    -t "${DOCKER_USERNAME}/${IMAGE_NAME}:latest" \
    -t "${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}" \
    --push \
    .

echo "linux/amd64 build completed and pushed to Docker Hub"