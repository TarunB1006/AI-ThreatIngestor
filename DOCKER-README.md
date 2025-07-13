# 🐳 **Docker Setup for AI-Enhanced ThreatIngestor**

## 📋 **Quick Start**

### **🚀 Production Deployment**
```bash
# Build and run production container
docker-compose up -d threatingestor-prod

# Access dashboard at: http://localhost:7862
# Ollama API at: http://localhost:11434
```

### **🛠️ Development Environment**
```bash
# Run development environment
docker-compose --profile dev up -d threatingestor-dev

# Access dev dashboard at: http://localhost:7863
# Jupyter Lab at: http://localhost:8888
```

---

## 🏗️ **Available Containers**

### **📦 Production Container (Dockerfile)**
- **Purpose**: Optimized for production deployment
- **Features**: 
  - Ubuntu 22.04 with Python 3.11
  - Ollama AI service integrated
  - Health checks enabled
  - Persistent data volumes
- **Ports**: 
  - `7862`: ThreatIngestor Dashboard
  - `11434`: Ollama API
- **Usage**: `docker-compose up -d threatingestor-prod`

### **🔧 Development Container (Dockerfile.dev)**
- **Purpose**: Full development environment with testing tools
- **Features**:
  - All production features plus:
  - Jupyter Lab for interactive development
  - Testing frameworks (pytest, coverage)
  - Code quality tools (black, flake8, mypy)
  - Development utilities (vim, htop, tree)
- **Ports**:
  - `7863`: Dashboard (dev port)
  - `11435`: Ollama API (dev port)
  - `8888`: Jupyter Lab
- **Usage**: `docker-compose --profile dev up -d`

---

## 🎯 **Container Commands**

### **Production Commands:**
```bash
# Start production environment
docker-compose up -d threatingestor-prod

# View logs
docker-compose logs -f threatingestor-prod

# Stop production environment
docker-compose down

# Rebuild and restart
docker-compose up -d --build threatingestor-prod
```

### **Development Commands:**
```bash
# Start development environment
docker-compose --profile dev up -d threatingestor-dev

# Start Jupyter Lab environment
docker-compose --profile dev up -d jupyter-dev

# Run tests in container
docker-compose --profile dev run --rm threatingestor-dev test

# Get shell access
docker-compose --profile dev run --rm threatingestor-dev shell

# Run custom command
docker-compose --profile dev run --rm threatingestor-dev python3.11 demo.py
```

---

## 💾 **Data Persistence**

### **Volumes:**
- `threat_db`: Production database storage
- `dev_threat_db`: Development database storage
- `./data`: External data files
- `./logs`: Application logs

### **Backup Database:**
```bash
# Backup production database
docker cp ai-threatingestor-prod:/app/threat_intelligence.db ./backup_$(date +%Y%m%d).db

# Restore database
docker cp ./backup_20250713.db ai-threatingestor-prod:/app/threat_intelligence.db
```

---

## 🔧 **Environment Variables**

### **Available Variables:**
```bash
# Ollama configuration
OLLAMA_HOST=0.0.0.0              # Ollama bind address
OLLAMA_MODELS=/app/models        # Model storage path

# Application settings
PYTHONUNBUFFERED=1               # Real-time Python output
DEVELOPMENT=1                    # Enable development mode

# Database settings
DATABASE_URL=sqlite:///threat_intelligence.db
```

### **Custom Environment File:**
```bash
# Create .env file
cat > .env << EOF
OLLAMA_HOST=0.0.0.0
PYTHONUNBUFFERED=1
LOG_LEVEL=INFO
EOF

# Use with docker-compose
docker-compose --env-file .env up -d
```

---

## 🛠️ **Development Workflow**

### **1. Code Changes:**
```bash
# Mount local code for real-time development
docker-compose --profile dev up -d threatingestor-dev

# Code changes are automatically reflected
# No rebuild needed for Python changes
```

### **2. Dependency Changes:**
```bash
# Rebuild after requirements.txt changes
docker-compose --profile dev up -d --build threatingestor-dev
```

### **3. Testing:**
```bash
# Run full test suite
docker-compose --profile dev run --rm threatingestor-dev test

# Run specific tests
docker-compose --profile dev run --rm threatingestor-dev python3.11 -m pytest tests/test_specific.py -v
```

### **4. Jupyter Development:**
```bash
# Start Jupyter Lab
docker-compose --profile dev up -d jupyter-dev

# Access at http://localhost:8889
# Token will be shown in logs:
docker-compose logs jupyter-dev
```

---

## 🚀 **Production Deployment**

### **Single Container:**
```bash
# Build production image
docker build -t ai-threatingestor:latest .

# Run production container
docker run -d \
  --name ai-threatingestor \
  -p 7862:7862 \
  -p 11434:11434 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  ai-threatingestor:latest
```

### **Docker Swarm/Kubernetes:**
```bash
# Deploy to swarm
docker stack deploy -c docker-compose.yml threatintel

# Generate Kubernetes manifests
docker-compose config > k8s-manifest.yml
```

---

## 🔍 **Troubleshooting**

### **Common Issues:**

**1. Ollama Service Not Starting:**
```bash
# Check Ollama logs
docker-compose logs threatingestor-prod | grep ollama

# Restart container
docker-compose restart threatingestor-prod
```

**2. Port Conflicts:**
```bash
# Check what's using ports
lsof -i :7862
lsof -i :11434

# Kill conflicting processes
sudo kill -9 $(lsof -ti:7862)
```

**3. Database Issues:**
```bash
# Reset database
docker-compose down
docker volume rm ai-threatingestor_threat_db
docker-compose up -d
```

**4. Memory Issues:**
```bash
# Check container memory usage
docker stats ai-threatingestor-prod

# Increase Docker memory limits in Docker Desktop
# Or add memory limits to docker-compose.yml:
# mem_limit: 4g
```

### **Health Checks:**
```bash
# Check container health
docker-compose ps

# Manual health check
curl -f http://localhost:7862/ || echo "Dashboard not ready"
curl -f http://localhost:11434/api/tags || echo "Ollama not ready"
```

---

## 📊 **Container Specifications**

### **Production Container:**
- **Base**: Ubuntu 22.04
- **Python**: 3.11+
- **Memory**: 2GB recommended (4GB+ for AI)
- **Storage**: 5GB minimum
- **Network**: Bridge mode

### **Development Container:**
- **Base**: Ubuntu 22.04 + dev tools
- **Python**: 3.11+ with dev packages
- **Memory**: 4GB recommended (8GB+ for Jupyter)
- **Storage**: 10GB minimum
- **Network**: Bridge mode with port forwarding

---

## 🎯 **Next Steps**

After successful Docker deployment:

1. **✅ Verify Services**: Check dashboard at http://localhost:7862
2. **🤖 Test AI**: Ensure Ollama model is loaded
3. **📡 Test Feeds**: Run manual refresh to verify feed processing
4. **🔄 Enable Real-time**: Start automated threat processing
5. **📊 Monitor**: Check logs and container health

**Your AI-Enhanced ThreatIngestor is now running in Docker! 🐳🛡️**
