#!/bin/bash
# Quick start script for using Context-Engine with Ollama

set -e

echo "🚀 Context-Engine + Ollama Quick Start"
echo "======================================="
echo

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not found. Please install it first:"
    echo "   macOS: brew install ollama"
    echo "   Linux: curl -fsSL https://ollama.ai/install.sh | sh"
    echo "   Visit: https://ollama.ai"
    exit 1
fi

echo "✅ Ollama is installed"

# Check if Ollama is running
if ! curl -s http://host.docker.internal:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama service not running. Starting it..."
    echo "   (If this doesn't work, run 'ollama serve' in another terminal)"
    ollama serve > /dev/null 2>&1 &
    sleep 2
fi

echo "✅ Ollama is running"

# Check for a recommended model
MODEL=${OLLAMA_MODEL:-qwen2.5-coder:1.5b}
if ! ollama list | grep -q "$MODEL"; then
    echo "📥 Pulling recommended model: $MODEL"
    echo "   (This may take a few minutes...)"
    ollama pull "$MODEL"
else
    echo "✅ Model $MODEL is available"
fi

# Export environment variables
export REFRAG_DECODER=1
export REFRAG_RUNTIME=ollama
export OLLAMA_MODEL="$MODEL"

# Platform-specific URL
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    export OLLAMA_URL="http://172.17.0.1:11434"
    echo "🐧 Linux detected - using Docker bridge IP: $OLLAMA_URL"
else
    export OLLAMA_URL="http://host.docker.internal:11434"
    echo "🍎 macOS/Windows detected - using host.docker.internal"
fi

echo
echo "✅ Environment configured:"
echo "   REFRAG_DECODER=1"
echo "   REFRAG_RUNTIME=ollama"
echo "   OLLAMA_URL=$OLLAMA_URL"
echo "   OLLAMA_MODEL=$MODEL"
echo

# Enable micro-chunking (recommended)
export INDEX_MICRO_CHUNKS=1
export MAX_MICRO_CHUNKS_PER_FILE=500

echo "🚀 Starting Context-Engine with Ollama..."
echo

# Run the reset-dev-dual command
exec make reset-dev-dual

