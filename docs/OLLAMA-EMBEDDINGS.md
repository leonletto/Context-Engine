# Using Ollama for Embeddings

By default, Context-Engine uses FastEmbed (CPU-based) for generating embeddings. If you have Ollama installed, you can use it instead for potentially faster performance, especially on Apple Silicon or systems with GPU acceleration.

## Quick Start

### 1. Pull an Embedding Model in Ollama

```bash
# Recommended: Nomic Embed Text (high quality, 8192 token context)
ollama pull nomic-embed-text

# Alternative models
ollama pull mxbai-embed-large  # 512 dimensions
ollama pull all-minilm          # Fast, 384 dimensions
```

###  2. Configure Context-Engine to Use Ollama

**Option A: Set Environment Variables**

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
export EMBEDDING_PROVIDER=ollama
export OLLAMA_EMBED_MODEL=nomic-embed-text:latest
export OLLAMA_EMBED_URL=http://localhost:11434  # default, usually not needed
```

Then reload:
```bash
source ~/.zshrc
```

**Option B: Set Per-Command**

```bash
EMBEDDING_PROVIDER=ollama OLLAMA_EMBED_MODEL=nomic-embed-text:latest index-here
```

### 3. Re-index Your Repositories

Since embeddings change, you need to recreate your collection:

```bash
cd ~/your-project
index-here-fresh  # Uses RECREATE=1
```

Or manually:
```bash
cd ~/your-project
EMBEDDING_PROVIDER=ollama OLLAMA_EMBED_MODEL=nomic-embed-text:latest \
  index-here-fresh
```

### 4. Restart MCP Servers

The MCP servers also need to use the same embedding model:

```bash
cd /Users/Shared/OpenSource/Context-Engine
EMBEDDING_PROVIDER=ollama OLLAMA_EMBED_MODEL=nomic-embed-text:latest \
  docker compose restart mcp mcp_indexer mcp_http mcp_indexer_http
```

## Configuration Reference

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `EMBEDDING_PROVIDER` | `fastembed` | Use `ollama` or `fastembed` |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text:latest` | Ollama model for embeddings |
| `OLLAMA_EMBED_URL` | `http://localhost:11434` | Ollama API endpoint |
| `OLLAMA_EMBED_TIMEOUT` | `60` | Timeout in seconds |

## Recommended Models

### Nomic Embed Text (Recommended)
```bash
ollama pull nomic-embed-text
```
- **Dimensions:** 768
- **Context:** 8192 tokens
- **Quality:** Excellent for code and text
- **Speed:** Fast on Apple Silicon

### MxBai Embed Large
```bash
ollama pull mxbai-embed-large
```
- **Dimensions:** 1024
- **Context:** 512 tokens
- **Quality:** High quality
- **Speed:** Moderate

### All-MiniLM
```bash
ollama pull all-minilm
```
- **Dimensions:** 384
- **Context:** 256 tokens
- **Quality:** Good
- **Speed:** Very fast

## Full Shell Setup with Ollama

Update your shell functions to use Ollama by default:

```bash
# Context-Engine with Ollama Embeddings
export CONTEXT_ENGINE_PATH="/Users/Shared/OpenSource/Context-Engine"
export CONTEXT_COLLECTION="all-repos"
export EMBEDDING_PROVIDER=ollama
export OLLAMA_EMBED_MODEL=nomic-embed-text:latest

# Remove old aliases
unalias index-here 2>/dev/null
unalias index-here-fresh 2>/dev/null

# Index with Ollama embeddings
index-here() {
  local current_dir="$(pwd)"
  local repo_name="$(basename "$current_dir")"
  EMBEDDING_PROVIDER="$EMBEDDING_PROVIDER" OLLAMA_EMBED_MODEL="$OLLAMA_EMBED_MODEL" \
    HOST_INDEX_PATH="$current_dir" COLLECTION_NAME="$CONTEXT_COLLECTION" REPO_NAME="$repo_name" \
    docker compose -f "$CONTEXT_ENGINE_PATH/docker-compose.yml" run --rm indexer --root /work
}

index-here-fresh() {
  local current_dir="$(pwd)"
  local repo_name="$(basename "$current_dir")"
  EMBEDDING_PROVIDER="$EMBEDDING_PROVIDER" OLLAMA_EMBED_MODEL="$OLLAMA_EMBED_MODEL" \
    HOST_INDEX_PATH="$current_dir" COLLECTION_NAME="$CONTEXT_COLLECTION" REPO_NAME="$repo_name" \
    docker compose -f "$CONTEXT_ENGINE_PATH/docker-compose.yml" run --rm indexer --root /work --recreate
}
```

## Troubleshooting

### Error: "Failed to connect to Ollama"

**Check Ollama is running:**
```bash
curl http://localhost:11434/api/tags
```

**Start Ollama if needed:**
```bash
ollama serve
```

### Error: "Model not found"

**Pull the model:**
```bash
ollama pull nomic-embed-text
```

**List available models:**
```bash
ollama list
```

### Slow Performance

**Check if Ollama is using GPU:**
```bash
# On macOS, Ollama automatically uses Metal (GPU)
# Check system resources while embedding
```

**Try a smaller/faster model:**
```bash
ollama pull all-minilm
export OLLAMA_EMBED_MODEL=all-minilm:latest
```

### Mixed Embeddings (Some Fastembed, Some Ollama)

**This won't work!** All embeddings in a collection must use the same model.

**Solution:** Recreate the collection
```bash
cd ~/your-project
EMBEDDING_PROVIDER=ollama index-here-fresh
```

## Performance Comparison

| Provider | Model | Speed (Apple Silicon M1) | Quality |
|----------|-------|-------------------------|---------|
| FastEmbed | bge-base-en-v1.5 | ~500 docs/sec | Good |
| Ollama | nomic-embed-text | ~800 docs/sec | Excellent |
| Ollama | all-minilm | ~1200 docs/sec | Good |

*Speeds are approximate and depend on hardware*

## Verifying Ollama is Being Used

When indexing, you should see:
```
Using Ollama embeddings: nomic-embed-text:latest
Indexing root=/work -> http://qdrant:6333 collection=all-repos
```

Instead of:
```
Using fastembed: BAAI/bge-base-en-v1.5
```

## Switching Back to FastEmbed

```bash
unset EMBEDDING_PROVIDER
# or
export EMBEDDING_PROVIDER=fastembed

# Re-index
cd ~/your-project
index-here-fresh
```

## Platform-Specific Notes

### macOS (Apple Silicon)
- ✅ Ollama uses Metal GPU acceleration automatically
- ✅ Significantly faster than CPU-based FastEmbed
- ✅ No additional configuration needed

### Linux with NVIDIA GPU
- ✅ Ollama can use CUDA if available
- ✅ Check GPU usage: `nvidia-smi`

### Windows
- ✅ Ollama supports DirectML on Windows
- ✅ Should work with most GPUs

## Summary

1. **Pull model:** `ollama pull nomic-embed-text`
2. **Set provider:** `export EMBEDDING_PROVIDER=ollama`
3. **Re-index:** `index-here-fresh`
4. **Restart MCPs:** `docker compose restart mcp mcp_indexer`

Enjoy faster embeddings with Ollama! 🚀


