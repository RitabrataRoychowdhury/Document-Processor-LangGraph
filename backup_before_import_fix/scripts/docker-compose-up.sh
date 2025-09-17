#!/bin/bash

# Document Q&A System - Docker Compose Script
# Uses Docker Compose for easier management

echo "🐳 Document Q&A System - Docker Compose"
echo "======================================="

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

# Check if Docker Compose is installed
print_info "Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Use docker-compose or docker compose based on availability
COMPOSE_CMD="docker-compose"
if ! command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker compose"
fi

print_status "Docker Compose found"

# Check if .env file exists
print_info "Checking configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        print_warning ".env file not found, copying from .env.example"
        cp .env.example .env
        print_warning "Please edit .env file with your actual API key"
        echo ""
        read -p "❓ Continue with default configuration? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Please update your .env file and run this script again"
            exit 1
        fi
    else
        print_error ".env file not found and no .env.example available"
        exit 1
    fi
else
    print_status "Configuration file found"
fi

# Create necessary directories
print_info "Creating data directories..."
mkdir -p data/database data/documents logs

# Ask user what to do
echo ""
echo "🎯 What would you like to do?"
echo "   1) Start services (build if needed)"
echo "   2) Start services (force rebuild)"
echo "   3) Stop services"
echo "   4) View logs"
echo "   5) Show status"
echo ""
read -p "Enter your choice (1-5) [1]: " -n 1 -r
echo

# Set default choice
if [ -z "$REPLY" ]; then
    REPLY="1"
fi

case $REPLY in
    1)
        print_info "Starting services..."
        $COMPOSE_CMD up -d
        if [ $? -eq 0 ]; then
            print_status "Services started successfully!"
            echo ""
            print_info "🌐 Web interface available at: http://localhost:8501"
            print_info "📊 Service status:"
            $COMPOSE_CMD ps
            echo ""
            print_info "📋 Useful commands:"
            echo "  View logs:     $COMPOSE_CMD logs -f"
            echo "  Stop:          $COMPOSE_CMD down"
            echo "  Restart:       $COMPOSE_CMD restart"
            echo "  Shell access:  $COMPOSE_CMD exec document-qa /bin/bash"
        else
            print_error "Failed to start services!"
            exit 1
        fi
        ;;
    2)
        print_info "Force rebuilding and starting services..."
        $COMPOSE_CMD up -d --build --force-recreate
        if [ $? -eq 0 ]; then
            print_status "Services rebuilt and started successfully!"
            echo ""
            print_info "🌐 Web interface available at: http://localhost:8501"
            $COMPOSE_CMD ps
        else
            print_error "Failed to rebuild and start services!"
            exit 1
        fi
        ;;
    3)
        print_info "Stopping services..."
        $COMPOSE_CMD down
        print_status "Services stopped"
        ;;
    4)
        print_info "Showing logs..."
        $COMPOSE_CMD logs -f
        ;;
    5)
        print_info "Service status:"
        $COMPOSE_CMD ps
        ;;
    *)
        print_error "Invalid choice. Please run the script again."
        exit 1
        ;;
esac