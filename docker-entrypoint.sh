#!/bin/bash
set -e

# AI-Enhanced ThreatIngestor Production Entrypoint

echo "🛡️  Starting AI-Enhanced ThreatIngestor..."

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

# Start the main application
echo "🚀 Starting ThreatIngestor Dashboard..."
exec python3.11 simple_dashboard.py
