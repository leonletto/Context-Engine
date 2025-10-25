# Shell Command Setup - Quick Indexing

This guide shows you how to create simple shell commands so you can index repositories from anywhere with just `index-here`.

> **⚠️ Important:** These commands directly call Docker Compose instead of Make to ensure the correct directory is indexed. This avoids the issue where `make -C` changes the working directory before running.

## Quick Setup (Copy & Paste)

### For macOS/Linux (Bash or Zsh)

Add these lines to your shell config file:

**Bash:** `~/.bashrc` or `~/.bash_profile`  
**Zsh:** `~/.zshrc`

```bash
# Context-Engine Quick Index Commands (COMPLETE VERSION)
export CONTEXT_ENGINE_PATH="/Users/Shared/OpenSource/Context-Engine"
export CONTEXT_COLLECTION="all-repos"
export EMBEDDING_PROVIDER=ollama
export OLLAMA_EMBED_MODEL=nomic-embed-text:137m-v1.5-fp16
export OLLAMA_EMBED_TIMEOUT=120  # Per-request timeout (default: 120s)
export OLLAMA_EMBED_RETRIES=3    # Number of retry attempts (default: 3)
export OLLAMA_EMBED_WORKERS=4    # Concurrent requests (default: 4, gives ~2.6x speedup)

# Remove old aliases
unalias index-here 2>/dev/null
unalias index-here-fresh 2>/dev/null

# Index current directory
index-here() {
  local current_dir="$(pwd)"
  local repo_name="$(basename "$current_dir")"
  INDEX_MICRO_CHUNKS=1 \
  MAX_MICRO_CHUNKS_PER_FILE=500 \
  EMBEDDING_PROVIDER="$EMBEDDING_PROVIDER" \
  OLLAMA_EMBED_MODEL="$OLLAMA_EMBED_MODEL" \
  OLLAMA_EMBED_TIMEOUT="$OLLAMA_EMBED_TIMEOUT" \
  OLLAMA_EMBED_RETRIES="$OLLAMA_EMBED_RETRIES" \
  OLLAMA_EMBED_WORKERS="$OLLAMA_EMBED_WORKERS" \
  HOST_INDEX_PATH="$current_dir" \
  COLLECTION_NAME="$CONTEXT_COLLECTION" \
  REPO_NAME="$repo_name" \
    docker compose -f "$CONTEXT_ENGINE_PATH/docker-compose.yml" run --rm indexer --root /work
}

# Index current directory with custom name
index-here-as() {
  if [ -z "$1" ]; then
    echo "Usage: index-here-as <repo-name>"
    return 1
  fi
  local current_dir="$(pwd)"
  INDEX_MICRO_CHUNKS=1 \
  MAX_MICRO_CHUNKS_PER_FILE=500 \
  EMBEDDING_PROVIDER="$EMBEDDING_PROVIDER" \
  OLLAMA_EMBED_MODEL="$OLLAMA_EMBED_MODEL" \
  OLLAMA_EMBED_TIMEOUT="$OLLAMA_EMBED_TIMEOUT" \
  OLLAMA_EMBED_RETRIES="$OLLAMA_EMBED_RETRIES" \
  OLLAMA_EMBED_WORKERS="$OLLAMA_EMBED_WORKERS" \
  HOST_INDEX_PATH="$current_dir" \
  COLLECTION_NAME="$CONTEXT_COLLECTION" \
  REPO_NAME="$1" \
    docker compose -f "$CONTEXT_ENGINE_PATH/docker-compose.yml" run --rm indexer --root /work
}

# Recreate index (fresh start)
index-here-fresh() {
  local current_dir="$(pwd)"
  local repo_name="$(basename "$current_dir")"
  INDEX_MICRO_CHUNKS=1 \
  MAX_MICRO_CHUNKS_PER_FILE=500 \
  EMBEDDING_PROVIDER="$EMBEDDING_PROVIDER" \
  OLLAMA_EMBED_MODEL="$OLLAMA_EMBED_MODEL" \
  OLLAMA_EMBED_TIMEOUT="$OLLAMA_EMBED_TIMEOUT" \
  OLLAMA_EMBED_RETRIES="$OLLAMA_EMBED_RETRIES" \
  OLLAMA_EMBED_WORKERS="$OLLAMA_EMBED_WORKERS" \
  HOST_INDEX_PATH="$current_dir" \
  COLLECTION_NAME="$CONTEXT_COLLECTION" \
  REPO_NAME="$repo_name" \
    docker compose -f "$CONTEXT_ENGINE_PATH/docker-compose.yml" run --rm indexer --root /work --recreate --no-skip-unchanged
}
```

### Apply the Changes

```bash
# Reload your shell config
source ~/.zshrc    # for Zsh
# or
source ~/.bashrc   # for Bash
```

## Usage Examples

Now you can use these simple commands from anywhere:

### 1. Index Current Directory (Incremental)
```bash
cd ~/my-project
index-here
```
**What it does:** Only indexes new/changed files (smart caching)

### 2. Index with Custom Name
```bash
cd ~/my-project
index-here-as myapp-backend
```
**What it does:** Same as `index-here` but with a custom repository name

### 3. Fresh Index (Complete Rebuild)
```bash
cd ~/my-project
index-here-fresh
```
**What it does:** 
- Drops and recreates the collection
- Forces re-indexing of ALL files (ignores cache)
- Use this when you want to completely rebuild the index

**When to use `index-here-fresh`:**
- After major refactoring
- If search results seem stale
- When switching embedding models
- To clean up the index from scratch

### 4. Index from Anywhere
```bash
index-path ~/other-project
index-path ~/another-project custom-name
```

---

## Advanced: Multiple Collections

If you work with different collections, add these functions:

```bash
# Index into a specific collection
index-to() {
  if [ -z "$1" ]; then
    echo "Usage: index-to <collection-name>"
    return 1
  fi
  make -C "$CONTEXT_ENGINE_PATH" index-here COLLECTION="$1"
}

# Switch default collection
set-collection() {
  if [ -z "$1" ]; then
    echo "Current collection: $CONTEXT_COLLECTION"
    return 0
  fi
  export CONTEXT_COLLECTION="$1"
  echo "Collection set to: $CONTEXT_COLLECTION"
}
```

**Usage:**
```bash
# Index into specific collection
cd ~/frontend-app
index-to frontend-collection

# Change default collection
set-collection my-work-repos
index-here  # now uses my-work-repos
```

---

## Advanced: Auto-Index on Directory Change

Want to automatically suggest indexing when you enter a git repo? Add this:

```bash
# Auto-suggest indexing for git repos (Zsh)
chpwd() {
  if [ -d .git ] && [ ! -f .indexed ]; then
    echo "💡 This looks like a repo. Run 'index-here' to index it."
  fi
}

# Mark as indexed
alias mark-indexed="touch .indexed && echo '✅ Marked as indexed'"
```

Or for Bash:

```bash
# Auto-suggest indexing for git repos (Bash)
cd() {
  builtin cd "$@"
  if [ -d .git ] && [ ! -f .indexed ]; then
    echo "💡 This looks like a repo. Run 'index-here' to index it."
  fi
}
```

---

## Full Configuration Example

Here's a complete `~/.zshrc` snippet with everything:

```bash
# ============================================
# Context-Engine Quick Commands
# ============================================

# Configuration
export CONTEXT_ENGINE_PATH="/Users/Shared/OpenSource/Context-Engine"
export CONTEXT_COLLECTION="all-repos"

# Basic commands
index-here() {
  local current_dir="$(pwd)"
  local repo_name="$(basename "$current_dir")"
  HOST_INDEX_PATH="$current_dir" COLLECTION_NAME="$CONTEXT_COLLECTION" REPO_NAME="$repo_name" \
    docker compose -f "$CONTEXT_ENGINE_PATH/docker-compose.yml" run --rm indexer --root /work
}

index-here-fresh() {
  local current_dir="$(pwd)"
  local repo_name="$(basename "$current_dir")"
  HOST_INDEX_PATH="$current_dir" COLLECTION_NAME="$CONTEXT_COLLECTION" REPO_NAME="$repo_name" \
    docker compose -f "$CONTEXT_ENGINE_PATH/docker-compose.yml" run --rm indexer --root /work --recreate
}

# Index with custom name
index-here-as() {
  if [ -z "$1" ]; then
    echo "Usage: index-here-as <repo-name>"
    return 1
  fi
  local current_dir="$(pwd)"
  HOST_INDEX_PATH="$current_dir" COLLECTION_NAME="$CONTEXT_COLLECTION" REPO_NAME="$1" \
    docker compose -f "$CONTEXT_ENGINE_PATH/docker-compose.yml" run --rm indexer --root /work
}

# Index a specific path
index-path() {
  if [ -z "$1" ]; then
    echo "Usage: index-path <path> [repo-name]"
    return 1
  fi
  local target_path="$(cd "$1" && pwd)"
  local repo_name="${2:-$(basename $target_path)}"
  HOST_INDEX_PATH="$target_path" COLLECTION_NAME="$CONTEXT_COLLECTION" REPO_NAME="$repo_name" \
    docker compose -f "$CONTEXT_ENGINE_PATH/docker-compose.yml" run --rm indexer --root /work
}

# Index to specific collection
index-to() {
  if [ -z "$1" ]; then
    echo "Usage: index-to <collection-name>"
    return 1
  fi
  local current_dir="$(pwd)"
  local repo_name="$(basename "$current_dir")"
  HOST_INDEX_PATH="$current_dir" COLLECTION_NAME="$1" REPO_NAME="$repo_name" \
    docker compose -f "$CONTEXT_ENGINE_PATH/docker-compose.yml" run --rm indexer --root /work
}

# Switch collection
set-collection() {
  if [ -z "$1" ]; then
    echo "Current collection: $CONTEXT_COLLECTION"
    return 0
  fi
  export CONTEXT_COLLECTION="$1"
  echo "Collection set to: $CONTEXT_COLLECTION"
}

# Show status
index-status() {
  echo "Context-Engine Path: $CONTEXT_ENGINE_PATH"
  echo "Current Collection: $CONTEXT_COLLECTION"
  echo "Current Directory: $(pwd)"
}
```

After adding this, reload your shell:
```bash
source ~/.zshrc
```

---

## Quick Test

```bash
# Check it works
cd ~
index-status

# Try indexing
cd ~/some-project
index-here
```

You should see the indexing process start!

---

## Customization

### Change the Default Collection

Edit the line in your shell config:
```bash
export CONTEXT_COLLECTION="my-custom-collection"
```

### Change Context-Engine Location

Edit the path:
```bash
export CONTEXT_ENGINE_PATH="/path/to/your/Context-Engine"
```

### Add Micro-Chunking by Default

```bash
alias index-here="INDEX_MICRO_CHUNKS=1 MAX_MICRO_CHUNKS_PER_FILE=200 make -C \$CONTEXT_ENGINE_PATH index-here COLLECTION=\$CONTEXT_COLLECTION"
```

---

## Windows (PowerShell)

Add to your PowerShell profile (`$PROFILE`):

```powershell
# Context-Engine Quick Commands
$env:CONTEXT_ENGINE_PATH = "C:\Users\YourName\Context-Engine"
$env:CONTEXT_COLLECTION = "all-repos"

function index-here {
    make -C $env:CONTEXT_ENGINE_PATH index-here COLLECTION=$env:CONTEXT_COLLECTION
}

function index-here-as {
    param([string]$name)
    if (-not $name) {
        Write-Host "Usage: index-here-as <repo-name>"
        return
    }
    make -C $env:CONTEXT_ENGINE_PATH index-here REPO_NAME=$name COLLECTION=$env:CONTEXT_COLLECTION
}

function index-path {
    param([string]$path, [string]$name)
    if (-not $path) {
        Write-Host "Usage: index-path <path> [repo-name]"
        return
    }
    $repoName = if ($name) { $name } else { Split-Path -Leaf $path }
    make -C $env:CONTEXT_ENGINE_PATH index-path REPO_PATH=$path REPO_NAME=$repoName COLLECTION=$env:CONTEXT_COLLECTION
}
```

---

## Troubleshooting

### Command not found after adding to config

Make sure you reloaded your shell:
```bash
source ~/.zshrc  # or ~/.bashrc
```

Or open a new terminal window.

### Ollama embedding timeouts

If you get `TimeoutError: timed out` or `URLError` during indexing:

1. **Adjust concurrent workers** (default is 4 parallel requests, giving ~2.6x speedup):
   ```bash
   # If Ollama is overloaded or timing out, reduce workers:
   export OLLAMA_EMBED_WORKERS=2   # More conservative (still 2.5x faster)
   
   # If you want maximum speed and your system can handle it:
   export OLLAMA_EMBED_WORKERS=8   # Fastest (2.8x speedup)
   
   source ~/.zshrc
   ```
   
   **💡 Pro tip:** Run `python3 $CONTEXT_ENGINE_PATH/scripts/benchmark_ollama_embeddings.py` to find your system's optimal worker count!

2. **Increase the timeout** if individual requests are slow (default is 120 seconds):
   ```bash
   export OLLAMA_EMBED_TIMEOUT=300  # 5 minutes per request
   source ~/.zshrc
   ```

3. **Check Ollama is running and responsive**:
   ```bash
   curl http://localhost:11434/api/tags
   ollama list
   ```

4. **Verify model is pulled**:
   ```bash
   ollama pull nomic-embed-text:latest
   ```

5. **Test from Docker** (to verify networking):
   ```bash
   cd $CONTEXT_ENGINE_PATH
   docker run --rm --add-host=host.docker.internal:host-gateway \
     curlimages/curl:latest curl -v http://host.docker.internal:11434/api/tags
   ```

6. **Increase retries** if your connection is flaky:
   ```bash
   export OLLAMA_EMBED_RETRIES=5  # default is 3
   ```

7. **For large repositories**, consider:
   - Reducing `MAX_MICRO_CHUNKS_PER_FILE` (e.g., from 500 to 200)
   - Reducing `OLLAMA_EMBED_WORKERS` (e.g., from 4 to 2)
   - Using FastEmbed instead: `export EMBEDDING_PROVIDER=fastembed`
   - Processing in smaller batches by indexing subdirectories separately

### Performance tuning

**Finding your optimal worker count:**

Run the benchmark tool to test your system:
```bash
cd $CONTEXT_ENGINE_PATH
python3 scripts/benchmark_ollama_embeddings.py
```

This will test 1, 2, 4, 8, and 16 workers and recommend the optimal setting for your hardware.

**Typical results:**
- **1 worker** (sequential): ~56 emb/sec (baseline)
- **2 workers**: ~139 emb/sec (2.5x faster) - Conservative
- **4 workers**: ~147 emb/sec (2.6x faster) - **Recommended default** ⭐
- **8 workers**: ~159 emb/sec (2.8x faster) - Maximum performance
- **16 workers**: ~148 emb/sec (2.6x) - Diminishing returns, overhead increases

### "make: command not found"

Install make:
```bash
# macOS
brew install make

# Ubuntu/Debian
sudo apt install make
```

### Context-Engine path is wrong

Update the path in your config:
```bash
export CONTEXT_ENGINE_PATH="/correct/path/to/Context-Engine"
source ~/.zshrc
```

Verify:
```bash
index-status
```

---

## Summary

After setup, you can:

```bash
# Navigate and index in one go
cd ~/project-1 && index-here
cd ~/project-2 && index-here
cd ~/project-3 && index-here

# Check everything
index-status

# All 3 repos are now searchable! 🎉
```

This makes indexing as simple as possible - just `cd` and `index-here`!

