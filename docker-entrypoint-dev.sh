#!/bin/bash
set -e

# AI-Enhanced ThreatIngestor Development Entrypoint

echo "🛡️  Starting AI-Enhanced ThreatIngestor (Development Mode)..."

# Start Ollama service in background
echo "🤖 Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to start..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "✅ Ollama is ready!"
        break
    fi
    echo "   Waiting... (attempt $i/30)"
    sleep 2
done

# Pull the AI model if not exists
echo "📥 Ensuring AI model is available..."
ollama pull tinyllama || echo "⚠️  Failed to pull model, will try at runtime"

# Check database
if [ ! -f "threat_intelligence.db" ]; then
    echo "🗄️  Initializing database..."
    python3.11 populate_db.py
fi

# Handle different startup modes
case "${1:-dashboard}" in
    "dashboard")
        echo "🚀 Starting ThreatIngestor Dashboard (Development)..."
        exec python3.11 simple_dashboard.py
        ;;
    "jupyter")
        echo "📊 Starting Jupyter Lab for development..."
        exec jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root
        ;;
    "shell")
        echo "🐚 Starting development shell..."
        exec /bin/bash
        ;;
    "test")
        echo "🧪 Running tests..."
        if [ -d "tests" ]; then
            exec python3.11 -m pytest tests/ -v
        else
            echo "❌ No tests directory found"
            exit 1
        fi
        ;;
    *)
        echo "🛠️  Running custom command: $*"
        exec "$@"
        ;;
esac
