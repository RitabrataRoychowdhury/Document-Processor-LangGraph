#!/bin/bash

# Document Q&A System - Docker Run Script
# Runs the Docker container with proper configuration

echo "🐳 Document Q&A System - Docker Run"
echo "==================================="

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

# Configuration
IMAGE_NAME="document-qa-system"
IMAGE_TAG="latest"
CONTAINER_NAME="document-qa-app"

# Check if Docker is running
print_info "Checking Docker..."
if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if image exists
print_info "Checking Docker image..."
if ! docker images "${IMAGE_NAME}:${IMAGE_TAG}" | grep -q "${IMAGE_NAME}"; then
    print_warning "Docker image not found. Building image first..."
    ./scripts/docker-build.sh
    if [ $? -ne 0 ]; then
        print_error "Failed to build Docker image"
        exit 1
    fi
fi

# Check if .env file exists
print_info "Checking configuration..."
if [ ! -f ".env" ]; then
    print_error ".env file not found. Please create it with your API key."
    exit 1
fi

# Stop existing container if running
print_info "Checking for existing container..."
if docker ps -q -f name="${CONTAINER_NAME}" | grep -q .; then
    print_warning "Stopping existing container..."
    docker stop "${CONTAINER_NAME}" > /dev/null
fi

# Remove existing container if exists
if docker ps -aq -f name="${CONTAINER_NAME}" | grep -q .; then
    print_info "Removing existing container..."
    docker rm "${CONTAINER_NAME}" > /dev/null
fi

# Create necessary directories
print_info "Creating data directories..."
mkdir -p data/database data/documents logs

# Run the container
print_info "Starting Docker container..."
echo ""

docker run -d \
    --name "${CONTAINER_NAME}" \
    -p 8501:8501 \
    --env-file .env \
    -v "$(pwd)/data:/app/data" \
    -v "$(pwd)/logs:/app/logs" \
    --restart unless-stopped \
    "${IMAGE_NAME}:${IMAGE_TAG}"

if [ $? -eq 0 ]; then
    print_status "Container started successfully!"
    echo ""
    print_info "🌐 Web interface available at: http://localhost:8501"
    print_info "📊 Container status:"
    docker ps -f name="${CONTAINER_NAME}"
    echo ""
    print_info "📋 Useful commands:"
    echo "  View logs:     docker logs ${CONTAINER_NAME}"
    echo "  Stop:          docker stop ${CONTAINER_NAME}"
    echo "  Restart:       docker restart ${CONTAINER_NAME}"
    echo "  Shell access:  docker exec -it ${CONTAINER_NAME} /bin/bash"
    echo ""
    print_info "📱 Press Ctrl+C to view logs, or use 'docker logs -f ${CONTAINER_NAME}'"
    
    # Follow logs
    echo ""
    print_info "Following container logs (Ctrl+C to exit)..."
    docker logs -f "${CONTAINER_NAME}"
else
    print_error "Failed to start container!"
    exit 1
fi