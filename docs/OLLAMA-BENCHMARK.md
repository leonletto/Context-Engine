# Ollama Embedding Performance Benchmark

This script helps you find the optimal concurrency settings for Ollama embeddings on your system.

## What It Does

Tests Ollama embedding performance with different numbers of concurrent requests:
- **Sequential** (1 worker) - Baseline performance
- **2, 4, 8, 16 workers** - Various concurrency levels
- **Multiple batch sizes** - Tests with 10, 30, and 64 samples

## Quick Start

### 1. Make sure Ollama is running

```bash
ollama list
ollama pull nomic-embed-text:latest
```

### 2. Run the benchmark

```bash
cd /Users/Shared/OpenSource/Context-Engine
python3 scripts/benchmark_ollama_embeddings.py
```

### 3. Apply the recommended settings

The script will output something like:

```
💡 RECOMMENDED CONFIGURATION:
export OLLAMA_EMBED_WORKERS=4
```

Add this to your `~/.zshrc` or `~/.bashrc`:

```bash
echo "export OLLAMA_EMBED_WORKERS=4" >> ~/.zshrc
source ~/.zshrc
```

## Example Output

```
🚀 Ollama Embedding Performance Benchmark
======================================================================
URL: http://localhost:11434
Model: nomic-embed-text:latest
Sample size: 64 texts
Worker counts to test: [1, 2, 4, 8, 16]
======================================================================

🔄 Testing SEQUENTIAL (1 worker)...
✅ Workers: 1
   Total time: 45.23s
   Throughput: 1.41 embeddings/sec
   Avg time per text: 0.707s

🔄 Testing CONCURRENT (4 workers)...
✅ Workers: 4
   Total time: 12.34s
   Throughput: 5.19 embeddings/sec
   Avg time per text: 0.193s

📊 BENCHMARK SUMMARY
======================================================================
Workers    Total Time   Throughput         Speedup    Errors  
----------------------------------------------------------------------
1          45.23s       1.41 emb/s         1.00x      0
2          23.45s       2.73 emb/s         1.93x      0
4          12.34s       5.19 emb/s         3.67x      0
8          14.56s       4.40 emb/s         3.11x      0
16         18.23s       3.51 emb/s         2.48x      0

🏆 OPTIMAL CONFIGURATION: 4 workers
   Throughput: 5.19 embeddings/sec
   Speedup vs sequential: 3.67x
```

## Environment Variables

You can customize the benchmark:

```bash
# Test a different model
export OLLAMA_EMBED_MODEL=mxbai-embed-large:latest
python3 scripts/benchmark_ollama_embeddings.py

# Test against a remote Ollama instance
export OLLAMA_EMBED_URL=http://remote-server:11434
python3 scripts/benchmark_ollama_embeddings.py
```

## Interpreting Results

### Good Signs ✅
- **Throughput increases** with more workers (up to a point)
- **No errors** at any concurrency level
- **Speedup of 3-4x** with 4-8 workers

### Warning Signs ⚠️
- **Errors appear** at higher concurrency → Ollama is overloaded
- **Throughput decreases** beyond certain worker count → Hitting resource limits
- **Very slow** (< 1 emb/sec) → Check CPU/RAM usage, or model size

### Typical Results

| System | Model | Optimal Workers | Throughput |
|--------|-------|----------------|------------|
| MacBook Air M2 | nomic-embed-text | 4-8 | 5-8 emb/sec |
| MacBook Pro M1 Max | nomic-embed-text | 8 | 10-15 emb/sec |
| Linux Server (16 core) | nomic-embed-text | 8-16 | 15-25 emb/sec |

## Troubleshooting

### "Connection failed"
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

### "Model not found"
```bash
# Pull the model first
ollama pull nomic-embed-text:latest
```

### Benchmark hangs or times out
```bash
# Reduce test size by editing the script
# Change: sample_sizes = [10]  # Instead of [10, 30, 64]
```

### Very low throughput
- Check CPU usage during test
- Try a smaller/faster model
- Close other applications
- Check if Ollama is using GPU (if available)

## What's Next?

After finding your optimal configuration:

1. **Update your shell config** with the recommended `OLLAMA_EMBED_WORKERS`
2. **Update Context-Engine** functions to use the new setting
3. **Re-run indexing** to see performance improvements

## Advanced Usage

### Test specific worker counts only

Edit the script and change:
```python
worker_configs = [4, 8]  # Only test 4 and 8 workers
```

### Test with different sample sizes

Edit the script and change:
```python
sample_sizes = [100, 200]  # Test with larger batches
```

### Save results to file

```bash
python3 scripts/benchmark_ollama_embeddings.py > benchmark_results.txt 2>&1
```

---

**Pro Tip:** Run this benchmark periodically after Ollama updates or system changes to ensure optimal performance! 🚀

