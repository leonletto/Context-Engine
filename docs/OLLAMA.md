# Ollama Integration Guide

This guide shows you how to use Ollama instead of llama.cpp for the decoder path in Context-Engine.

## Prerequisites

1. **Install Ollama** on your host machine:
   - macOS: `brew install ollama` or download from https://ollama.ai
   - Linux: `curl -fsSL https://ollama.ai/install.sh | sh`

2. **Start Ollama** (if not already running):
   ```bash
   ollama serve
   ```

3. **Pull a coding model**:
   ```bash
   # Small and fast (recommended)
   ollama pull qwen2.5-coder:1.5b
   
   # Or larger models
   ollama pull qwen2.5-coder:7b
   ollama pull deepseek-coder:6.7b
   ollama pull codellama:7b
   ```

## Configuration

### Option 1: Environment Variables (Recommended)

Set these in your shell before running `make reset-dev-dual`:

```bash
# Enable decoder with Ollama
export REFRAG_DECODER=1
export REFRAG_RUNTIME=ollama
export OLLAMA_URL=http://host.docker.internal:11434
export OLLAMA_MODEL=qwen2.5-coder:1.5b

# Then run
INDEX_MICRO_CHUNKS=1 MAX_MICRO_CHUNKS_PER_FILE=200 make reset-dev-dual
```

### Option 2: Create .env file

Create a `.env` file in the project root:

```ini
# Core settings
COLLECTION_NAME=my-collection
QDRANT_URL=http://qdrant:6333
EMBEDDING_MODEL=BAAI/bge-base-en-v1.5

# Micro-chunking
INDEX_MICRO_CHUNKS=1
MAX_MICRO_CHUNKS_PER_FILE=200

# Ollama decoder
REFRAG_DECODER=1
REFRAG_RUNTIME=ollama
OLLAMA_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen2.5-coder:1.5b
```

Then run:
```bash
make reset-dev-dual
```

## Platform-Specific Notes

### macOS
Use `host.docker.internal` to reach host services from Docker:
```ini
OLLAMA_URL=http://host.docker.internal:11434
```

### Linux
Docker networking differs on Linux. Use one of these approaches:

**Option A:** Use Docker bridge IP
```ini
OLLAMA_URL=http://172.17.0.1:11434
```

**Option B:** Make Ollama listen on all interfaces
```bash
# Start Ollama with
OLLAMA_HOST=0.0.0.0:11434 ollama serve

# Then in .env use
OLLAMA_URL=http://172.17.0.1:11434
```

**Option C:** Use host network mode (add to docker-compose.yml)
```yaml
  mcp_indexer:
    network_mode: "host"
```

### Windows
Use `host.docker.internal` (Docker Desktop only):
```ini
OLLAMA_URL=http://host.docker.internal:11434
```

## Testing the Integration

1. **Check Ollama is accessible**:
   ```bash
   curl http://localhost:11434/api/tags
   ```
   You should see your pulled models listed.

2. **Start Context-Engine services**:
   ```bash
   docker compose up -d mcp mcp_indexer qdrant
   ```

3. **Test the decoder** (from inside a container):
   ```bash
   docker compose exec mcp_indexer python3 -c "
   import os
   os.environ['REFRAG_DECODER'] = '1'
   os.environ['REFRAG_RUNTIME'] = 'ollama'
   os.environ['OLLAMA_URL'] = 'http://host.docker.internal:11434'
   os.environ['OLLAMA_MODEL'] = 'qwen2.5-coder:1.5b'
   from scripts.refrag_ollama import OllamaRefragClient
   client = OllamaRefragClient()
   result = client.generate_with_soft_embeddings('Say hello', max_tokens=20)
   print('Result:', result)
   "
   ```

4. **Use context_answer tool** via MCP client:
   ```json
   {
     "tool": "context_answer",
     "arguments": {
       "query": "How does hybrid search work?",
       "limit": 5
     }
   }
   ```

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `REFRAG_DECODER` | `0` | Enable decoder: `1` or `true` |
| `REFRAG_RUNTIME` | `llamacpp` | Runtime: `ollama` or `llamacpp` |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `qwen2.5-coder:1.5b` | Model name (must be pulled first) |
| `OLLAMA_CHAT_TEMPLATE` | (auto-detect) | Chat template: `qwen` or `phi` (usually auto-detected) |
| `OLLAMA_TIMEOUT_SEC` | `120` | HTTP timeout for Ollama requests |
| `DECODER_MAX_TOKENS` | `300` | Max tokens to generate |
| `DECODER_TEMPERATURE` | `0.1` | Sampling temperature (0.0-1.0) |
| `DECODER_TOP_K` | `40` | Top-k sampling |
| `DECODER_TOP_P` | `0.92` | Top-p (nucleus) sampling |
| `DECODER_REPEAT_PENALTY` | `1.15` | Repetition penalty |

### Chat Template Formatting

Context-Engine automatically formats prompts with the appropriate chat template based on your model:

- **Qwen models** (qwen2.5-coder, qwq, etc.): Uses `<|im_start|>role\ncontent<|im_end|>` format
- **Phi models** (phi-3, phi-4): Uses `<|role|>content<|end|>` format

The chat template is auto-detected from the model name. If you need to override it:
```bash
export OLLAMA_CHAT_TEMPLATE=qwen  # or 'phi'
```

**Example formatted prompt for Qwen:**
```
<|im_start|>system
You are a helpful coding assistant. Give brief, direct answers.<|im_end|>
<|im_start|>user
Explain this function<|im_end|>
<|im_start|>assistant
```

**Example formatted prompt for Phi:**
```
<|system|>You are a helpful coding assistant. Give brief, direct answers.<|end|>
<|user|>Explain this function<|end|>
<|assistant|>
```

## Troubleshooting

### "Connection refused" error
- Check Ollama is running: `curl http://localhost:11434/api/tags`
- Verify the URL is correct for your platform (see Platform-Specific Notes above)
- On Linux, try `172.17.0.1` instead of `localhost`

### "Model not found" error
- Pull the model first: `ollama pull qwen2.5-coder:1.5b`
- Verify model name: `ollama list`

### Slow responses
- Try a smaller model: `qwen2.5-coder:1.5b` is faster than `7b`
- Reduce `DECODER_MAX_TOKENS` to generate less text
- Increase `OLLAMA_TIMEOUT_SEC` if requests are timing out

### Generation timeouts or hangs
If the model times out or produces no output:
- **Chat templates are now auto-formatted** - Context-Engine automatically adds the proper chat template tokens (`<|im_start|>`, `<|im_end|>`, etc.) based on your model
- If auto-detection fails, override with: `export OLLAMA_CHAT_TEMPLATE=qwen` or `phi`
- Verify your model is an instruct/chat variant (e.g., `qwen2.5-coder:1.5b-instruct`)
- Check generation with: `ollama run qwen2.5-coder:1.5b "Say hello"`

### "unsupported REFRAG_RUNTIME" error
- Ensure you set `REFRAG_RUNTIME=ollama` (lowercase)
- Restart the MCP services after changing .env: `docker compose restart mcp_indexer`

## Comparing Ollama vs llama.cpp

| Feature | Ollama | llama.cpp |
|---------|--------|-----------|
| **Setup** | Install on host | Runs in Docker |
| **Model Management** | `ollama pull MODEL` | Download GGUF manually |
| **Platform Issues** | No ARM64 issues | May need platform override |
| **Soft Embeddings** | Not supported | Planned (patched server) |
| **API** | REST JSON | REST JSON |
| **Performance** | Native speed | May use emulation on ARM |

## Recommended Models

For code-related tasks (sorted by speed/size):

1. **qwen2.5-coder:1.5b** - Fast, good for summaries (recommended)
2. **qwen2.5-coder:7b** - Better quality, slower
3. **deepseek-coder:6.7b** - Excellent for code understanding
4. **codellama:7b** - General-purpose code model

Pull with:
```bash
ollama pull qwen2.5-coder:1.5b
```

## Advanced: Custom Model Parameters

You can fine-tune generation per request or via environment:

```bash
# Via environment (applies globally)
export DECODER_TEMPERATURE=0.3
export DECODER_TOP_P=0.95
export DECODER_REPEAT_PENALTY=1.2

# These override the defaults in the Ollama adapter
```

## Switching Back to llama.cpp

To switch back:

```bash
# In .env or environment
REFRAG_RUNTIME=llamacpp
LLAMACPP_URL=http://llamacpp:8080

# Start llama.cpp
docker compose up -d llamacpp
```

