# 🐳 Docker Deployment Guide

Complete guide for running the Document Q&A System using Docker.

## 🚀 Quick Start with Docker

### **Option 1: Docker Compose (Recommended)**
```bash
# Build and start services
./scripts/docker-compose-up.sh

# Or manually
docker-compose up -d
```

### **Option 2: Docker Run**
```bash
# Build image
./scripts/docker-build.sh

# Run container
./scripts/docker-run.sh

# Or manually
docker run -p 8501:8501 --env-file .env document-qa-system
```

## 📋 Prerequisites

### **Required:**
- Docker Engine 20.10+
- Docker Compose 2.0+ (for compose method)
- 2GB+ available RAM
- 1GB+ available disk space

### **Configuration:**
1. **API Key**: Edit `.env` file with your Gemini API key
2. **Ports**: Ensure port 8501 is available
3. **Permissions**: Docker daemon access

## 🛠️ Docker Scripts

### **1. `./scripts/docker-build.sh`**
Builds the Docker image with optimizations.

**Features:**
- ✅ Multi-stage build for smaller image size
- ✅ Security hardening (non-root user)
- ✅ Dependency caching
- ✅ Health checks included

**Usage:**
```bash
./scripts/docker-build.sh
```

### **2. `./scripts/docker-run.sh`**
Runs a single Docker container with proper configuration.

**Features:**
- ✅ Automatic container management
- ✅ Volume mounting for data persistence
- ✅ Environment variable loading
- ✅ Log following

**Usage:**
```bash
./scripts/docker-run.sh
```

### **3. `./scripts/docker-compose-up.sh`**
Uses Docker Compose for service orchestration.

**Features:**
- ✅ Service management
- ✅ Network isolation
- ✅ Volume management
- ✅ Health monitoring
- ✅ Interactive menu

**Usage:**
```bash
./scripts/docker-compose-up.sh
```

## 🏗️ Docker Configuration

### **Dockerfile Features:**
```dockerfile
# Multi-stage build
FROM python:3.11-slim as builder
# ... build dependencies

FROM python:3.11-slim
# ... production image
```

**Security Features:**
- ✅ Non-root user execution
- ✅ Minimal base image (slim)
- ✅ No unnecessary packages
- ✅ Read-only environment file

**Performance Features:**
- ✅ Layer caching optimization
- ✅ Multi-stage build
- ✅ Dependency pre-installation
- ✅ Health checks

### **Docker Compose Features:**
```yaml
services:
  document-qa:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
```

## 📊 Container Management

### **Basic Commands:**
```bash
# Build image
docker build -t document-qa-system .

# Run container
docker run -d -p 8501:8501 --name document-qa --env-file .env document-qa-system

# View logs
docker logs -f document-qa

# Stop container
docker stop document-qa

# Remove container
docker rm document-qa
```

### **Docker Compose Commands:**
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build --force-recreate

# Scale services (if needed)
docker-compose up -d --scale document-qa=2
```

## 🔧 Environment Configuration

### **Required Environment Variables:**
```env
GEMINI_API_KEY=your_actual_api_key_here
DATABASE_PATH=data/database/documents.db
MAX_FILE_SIZE_MB=10
ALLOWED_FILE_TYPES=pdf,txt,docx
STREAMLIT_PORT=8501
DEBUG_MODE=false
```

### **Docker-Specific Variables:**
```env
# Container configuration
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_PORT=8501
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
```

## 📁 Volume Management

### **Persistent Data:**
```yaml
volumes:
  - ./data:/app/data          # Database and documents
  - ./logs:/app/logs          # Application logs
  - ./.env:/app/.env:ro       # Configuration (read-only)
```

### **Data Locations:**
- **Database**: `./data/database/documents.db`
- **Documents**: `./data/documents/`
- **Logs**: `./logs/`
- **Config**: `./.env`

## 🔍 Monitoring & Health Checks

### **Built-in Health Check:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1
```

### **Monitoring Commands:**
```bash
# Check container health
docker ps
docker inspect document-qa | grep Health

# View resource usage
docker stats document-qa

# Check logs
docker logs document-qa --tail 100

# Container shell access
docker exec -it document-qa /bin/bash
```

## 🚨 Troubleshooting

### **Common Issues:**

**"Port 8501 already in use"**
```bash
# Find process using port
lsof -i :8501
# Kill process or use different port
docker run -p 8502:8501 ...
```

**"Permission denied"**
```bash
# Fix script permissions
chmod +x scripts/docker-*.sh

# Fix Docker permissions (Linux)
sudo usermod -aG docker $USER
```

**"Container exits immediately"**
```bash
# Check logs
docker logs document-qa

# Run interactively for debugging
docker run -it --rm document-qa-system /bin/bash
```

**"API key not working"**
```bash
# Check .env file
cat .env | grep GEMINI_API_KEY

# Verify environment in container
docker exec document-qa env | grep GEMINI
```

**"Database connection failed"**
```bash
# Check volume mounting
docker inspect document-qa | grep Mounts

# Verify permissions
ls -la data/database/
```

### **Debug Mode:**
```bash
# Run with debug enabled
docker run -e DEBUG_MODE=true -p 8501:8501 document-qa-system

# Or edit .env file
echo "DEBUG_MODE=true" >> .env
docker-compose restart
```

## 🔒 Security Considerations

### **Production Deployment:**
1. **Use secrets management** instead of .env files
2. **Enable HTTPS** with reverse proxy
3. **Limit container resources**
4. **Regular security updates**
5. **Network isolation**

### **Example Production Setup:**
```yaml
# docker-compose.prod.yml
services:
  document-qa:
    image: document-qa-system:latest
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
    secrets:
      - gemini_api_key
    networks:
      - internal

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    networks:
      - internal
      - external

secrets:
  gemini_api_key:
    external: true

networks:
  internal:
    internal: true
  external:
```

## 📈 Performance Optimization

### **Resource Limits:**
```yaml
services:
  document-qa:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
```

### **Image Optimization:**
- ✅ Multi-stage builds reduce image size by ~60%
- ✅ Alpine base images for smaller footprint
- ✅ Layer caching for faster builds
- ✅ .dockerignore for build context optimization

### **Runtime Optimization:**
- ✅ Health checks for automatic recovery
- ✅ Restart policies for reliability
- ✅ Volume mounting for data persistence
- ✅ Environment-based configuration

## 🎯 Quick Reference

| Task | Command | Description |
|------|---------|-------------|
| **Build** | `./scripts/docker-build.sh` | Build Docker image |
| **Run** | `./scripts/docker-run.sh` | Run single container |
| **Compose** | `./scripts/docker-compose-up.sh` | Use Docker Compose |
| **Logs** | `docker logs -f document-qa` | View container logs |
| **Shell** | `docker exec -it document-qa /bin/bash` | Container shell |
| **Stop** | `docker-compose down` | Stop all services |
| **Health** | `docker ps` | Check container status |

## 🌐 Access Points

- **Web Interface**: http://localhost:8501
- **Health Check**: http://localhost:8501/_stcore/health
- **Container Logs**: `docker logs document-qa`
- **Shell Access**: `docker exec -it document-qa /bin/bash`

---

🎉 **Your Document Q&A System is now containerized and ready for deployment!** 🚀🐳