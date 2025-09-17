#!/bin/bash

# Document Q&A System - Docker Build Script
# Builds the Docker image for the application

echo "🐳 Document Q&A System - Docker Build"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Docker is installed
print_info "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

print_status "Docker found: $(docker --version)"

# Check if .env file exists
print_info "Checking configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        print_warning ".env file not found, copying from .env.example"
        cp .env.example .env
        print_info "Please edit .env file with your actual API key before running"
    else
        print_error ".env file not found and no .env.example available"
        exit 1
    fi
else
    print_status "Configuration file found"
fi

# Build the Docker image
IMAGE_NAME="document-qa-system"
IMAGE_TAG="latest"

print_info "Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""

if docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .; then
    print_status "Docker image built successfully!"
    echo ""
    print_info "Image details:"
    docker images "${IMAGE_NAME}:${IMAGE_TAG}"
    echo ""
    print_info "To run the container:"
    echo "  docker run -p 8501:8501 --env-file .env ${IMAGE_NAME}:${IMAGE_TAG}"
    echo ""
    print_info "Or use Docker Compose:"
    echo "  docker-compose up"
else
    print_error "Docker build failed!"
    exit 1
fi

print_status "Build completed successfully! 🎉"