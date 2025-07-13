#!/bin/bash

# 🛡️ ThreatIngestor AI Setup Script
# This script sets up the AI-enhanced ThreatIngestor with Ollama integration

set -e  # Exit on any error

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🛡️  ThreatIngestor AI-Enhanced Setup Script"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

# Check if running on supported OS
check_os() {
    print_info "Checking operating system..."
    OS=$(uname -s)
    case $OS in
        Linux*)     MACHINE=Linux;;
        Darwin*)    MACHINE=Mac;;
        CYGWIN*)    MACHINE=Cygwin;;
        MINGW*)     MACHINE=MinGw;;
        *)          MACHINE="UNKNOWN:${OS}"
    esac
    
    if [[ "$MACHINE" == "UNKNOWN"* ]]; then
        print_error "Unsupported operating system: $OS"
        exit 1
    fi
    
    print_success "Operating system detected: $MACHINE"
}

# Check Python version
check_python() {
    print_info "Checking Python version..."
    
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        PYTHON_CMD="python3"
    elif command -v python >/dev/null 2>&1; then
        PYTHON_VERSION=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        PYTHON_CMD="python"
    else
        print_error "Python not found. Please install Python 3.8+"
        exit 1
    fi
    
    # Check if version is >= 3.8
    MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    
    if [[ $MAJOR -gt 3 ]] || [[ $MAJOR -eq 3 && $MINOR -ge 8 ]]; then
        print_success "Python $PYTHON_VERSION found"
    else
        print_error "Python 3.8+ required, found $PYTHON_VERSION"
        exit 1
    fi
}

# Setup virtual environment
setup_venv() {
    print_info "Setting up Python virtual environment..."
    
    if [[ ! -d ".venv" ]]; then
        $PYTHON_CMD -m venv .venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    if [[ "$MACHINE" == "Mac" || "$MACHINE" == "Linux" ]]; then
        source .venv/bin/activate
    else
        source .venv/Scripts/activate
    fi
    
    print_success "Virtual environment activated"
}

# Install Python dependencies
install_dependencies() {
    print_info "Installing Python dependencies..."
    
    # Upgrade pip first
    pip install --upgrade pip
    
    # Install requirements
    if [[ -f "requirements-hackathon.txt" ]]; then
        pip install -r requirements-hackathon.txt
        print_success "Hackathon dependencies installed"
    else
        pip install -r requirements.txt
        print_success "Basic dependencies installed"
    fi
}

# Install Ollama
install_ollama() {
    print_info "Installing Ollama for AI integration..."
    
    if command -v ollama >/dev/null 2>&1; then
        print_warning "Ollama already installed"
        return 0
    fi
    
    case $MACHINE in
        Mac)
            if command -v brew >/dev/null 2>&1; then
                brew install ollama
            else
                curl -fsSL https://ollama.ai/install.sh | sh
            fi
            ;;
        Linux)
            curl -fsSL https://ollama.ai/install.sh | sh
            ;;
        *)
            print_warning "Please install Ollama manually from https://ollama.ai/download"
            return 1
            ;;
    esac
    
    print_success "Ollama installed"
}

# Start Ollama service
start_ollama() {
    print_info "Starting Ollama service..."
    
    # Check if already running
    if pgrep ollama >/dev/null 2>&1; then
        print_warning "Ollama service already running"
        return 0
    fi
    
    # Start service in background
    ollama serve > /dev/null 2>&1 &
    
    # Wait for service to start
    sleep 3
    
    if pgrep ollama >/dev/null 2>&1; then
        print_success "Ollama service started"
    else
        print_error "Failed to start Ollama service"
        return 1
    fi
}

# Download AI models
download_models() {
    print_info "Downloading AI models..."
    
    # Get available RAM (approximate)
    if [[ "$MACHINE" == "Mac" ]]; then
        TOTAL_RAM_GB=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024/1024)}')
    elif [[ "$MACHINE" == "Linux" ]]; then
        TOTAL_RAM_GB=$(free -g | awk '/^Mem:/{print $2}')
    else
        TOTAL_RAM_GB=8  # Default assumption
    fi
    
    print_info "Detected ${TOTAL_RAM_GB}GB RAM"
    
    # Choose model based on RAM
    if [[ $TOTAL_RAM_GB -ge 16 ]]; then
        MODEL="llama2:13b"
        print_info "Downloading high-performance model (7.3GB)..."
    elif [[ $TOTAL_RAM_GB -ge 8 ]]; then
        MODEL="mistral"
        print_info "Downloading balanced model (4.1GB)..."
    else
        MODEL="tinyllama"
        print_info "Downloading lightweight model (637MB)..."
    fi
    
    if ollama pull $MODEL; then
        print_success "Model $MODEL downloaded successfully"
    else
        print_warning "Failed to download $MODEL, trying fallback..."
        if ollama pull tinyllama; then
            print_success "Fallback model tinyllama downloaded"
        else
            print_error "Failed to download any model"
            return 1
        fi
    fi
}

# Initialize database
init_database() {
    print_info "Initializing database..."
    
    $PYTHON_CMD -c "
from app.core.database import init_database
try:
    init_database()
    print('✅ Database initialized successfully')
except Exception as e:
    print(f'❌ Database initialization failed: {e}')
    exit(1)
"
}

# Test AI integration
test_ai() {
    print_info "Testing AI integration..."
    
    $PYTHON_CMD -c "
from app.core.llm_service import get_llm_service
try:
    llm = get_llm_service()
    available = llm.is_available()
    print(f'🤖 AI Service Status: {'Available' if available else 'Offline'}')
    
    if available:
        result = llm.summarize_threat('Test', 'Sample APT malware targeting banks')
        print(f'📝 Test Analysis: {result['summary'][:50]}...')
        print('✅ AI integration working correctly')
    else:
        print('⚠️  AI service offline but system will use fallback analysis')
except Exception as e:
    print(f'❌ AI integration test failed: {e}')
"
}

# Create sample configuration
create_config() {
    print_info "Creating sample configuration..."
    
    if [[ ! -f "myfeeds.yaml" ]]; then
        cat > myfeeds.yaml << 'EOF'
# Sample AI-Enhanced ThreatIngestor Configuration
# Edit this file to customize your threat intelligence sources

# AI Configuration
ai:
  enabled: true
  model: "mistral"
  timeout: 30
  fallback: true

# Feed Sources
feeds:
  - name: "Krebs on Security"
    url: "https://krebsonsecurity.com/feed/"
    category: "security_blog"
    
  - name: "SANS Internet Storm Center"
    url: "https://isc.sans.edu/rssfeed.xml"
    category: "research"
    
  - name: "Malware Traffic Analysis"
    url: "https://www.malware-traffic-analysis.net/blog-entries.rss"
    category: "malware"

# Processing Options
processing:
  ai_enabled: true
  batch_size: 10
  confidence_threshold: 0.7
EOF
        print_success "Sample configuration created: myfeeds.yaml"
    else
        print_warning "Configuration file myfeeds.yaml already exists"
    fi
}

# Main setup function
main() {
    echo "Starting setup process..."
    echo ""
    
    check_os
    check_python
    setup_venv
    install_dependencies
    
    echo ""
    print_info "🤖 Setting up AI components..."
    
    if install_ollama && start_ollama; then
        download_models
        print_success "AI setup completed"
    else
        print_warning "AI setup failed, but ThreatIngestor will work with fallback analysis"
    fi
    
    echo ""
    print_info "🗄️  Setting up database and configuration..."
    
    init_database
    create_config
    
    echo ""
    print_info "🧪 Running tests..."
    test_ai
    
    echo ""
    echo "════════════════════════════════════════════════════════════════════════════════"
    print_success "🎉 Setup completed successfully!"
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo ""
    echo "🚀 Next steps:"
    echo ""
    echo "   1. Start the dashboard:"
    echo "      python app.py --dashboard"
    echo ""
    echo "   2. Visit the web interface:"
    echo "      http://localhost:7860"
    echo ""
    echo "   3. Process threat feeds:"
    echo "      python app.py --process-feeds"
    echo ""
    echo "   4. Run comprehensive demo:"
    echo "      python demo.py"
    echo ""
    echo "   5. Edit configuration:"
    echo "      vim myfeeds.yaml"
    echo ""
    echo "📚 Documentation:"
    echo "   • AI Integration Guide: docs/AI-INTEGRATION-GUIDE.md"
    echo "   • Module Architecture: docs/MODULE-ARCHITECTURE.md"
    echo "   • Hackathon Details: README-HACKATHON.md"
    echo ""
    echo "🆘 Need help? Check GitHub Issues or Discussions"
    echo ""
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "ThreatIngestor AI Setup Script"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --no-ai        Skip AI/Ollama installation"
        echo "  --light        Install lightweight model only"
        echo ""
        exit 0
        ;;
    --no-ai)
        SKIP_AI=true
        ;;
    --light)
        FORCE_LIGHT=true
        ;;
esac

# Run main setup
main

echo "Happy threat hunting! 🛡️"
