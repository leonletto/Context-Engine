# Quick Reference: Using Ollama with Context-Engine

## TL;DR - 3 Steps

```bash
# 1. Install and start Ollama
brew install ollama  # or download from ollama.ai
ollama serve         # in a separate terminal

# 2. Pull a model
ollama pull qwen2.5-coder:1.5b

# 3. Run Context-Engine with Ollama
./scripts/start-with-ollama.sh
```

## Manual Setup (if you prefer)

```bash
# Set environment variables
export REFRAG_DECODER=1
export REFRAG_RUNTIME=ollama
export OLLAMA_URL=http://host.docker.internal:11434  # macOS/Windows
# export OLLAMA_URL=http://172.17.0.1:11434         # Linux alternative
export OLLAMA_MODEL=qwen2.5-coder:1.5b

# Start services
INDEX_MICRO_CHUNKS=1 MAX_MICRO_CHUNKS_PER_FILE=200 make reset-dev-dual
```

## Testing It Works

```bash
# Check Ollama is accessible
curl http://localhost:11434/api/tags

# List running Docker services
docker compose ps

# Test from MCP client using context_answer tool
# (requires your IDE/agent to be connected to port 8001 or 8003)
```

## Switching Back to llama.cpp

```bash
export REFRAG_RUNTIME=llamacpp
export LLAMACPP_URL=http://llamacpp:8080
docker compose restart mcp_indexer
```

## Troubleshooting Quick Fixes

**Connection refused:**
```bash
# Check Ollama is running
ps aux | grep ollama

# Restart if needed
ollama serve
```

**Model not found:**
```bash
# List your models
ollama list

# Pull the one you want
ollama pull qwen2.5-coder:1.5b
```

**Docker can't reach host (Linux):**
```bash
# Use bridge IP
export OLLAMA_URL=http://172.17.0.1:11434

# OR make Ollama listen on all interfaces
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

For more details, see [docs/OLLAMA.md](OLLAMA.md)

