#!/usr/bin/env python3
"""
Ollama Embedding Performance Benchmark

Tests embedding performance with different concurrency levels to find the optimal
configuration for your system.

Usage:
    python3 scripts/benchmark_ollama_embeddings.py

Environment Variables:
    OLLAMA_EMBED_URL - Ollama API URL (default: http://localhost:11434)
    OLLAMA_EMBED_MODEL - Model to test (default: nomic-embed-text:latest)
"""

import os
import sys
import time
import json
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib import request
from urllib.error import URLError, HTTPError


class OllamaEmbeddingBenchmark:
    """Benchmark Ollama embedding performance with various concurrency levels."""
    
    def __init__(self, base_url: str, model_name: str):
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.timeout = 60  # Use shorter timeout for benchmarking
        
    def get_embedding(self, text: str) -> tuple[List[float], float]:
        """Get a single embedding and return (embedding, elapsed_time)."""
        start_time = time.time()
        
        payload = {
            "model": self.model_name,
            "prompt": text
        }
        
        req = request.Request(
            f"{self.base_url}/api/embeddings",
            method="POST"
        )
        req.add_header("Content-Type", "application/json")
        data = json.dumps(payload).encode("utf-8")
        
        try:
            with request.urlopen(req, data=data, timeout=self.timeout) as resp:
                body = resp.read()
            
            result = json.loads(body.decode("utf-8"))
            elapsed = time.time() - start_time
            return result["embedding"], elapsed
            
        except (URLError, HTTPError, TimeoutError) as e:
            raise RuntimeError(f"Embedding failed: {e}")
    
    def benchmark_sequential(self, texts: List[str]) -> Dict[str, Any]:
        """Benchmark sequential processing (no concurrency)."""
        print(f"\n🔄 Testing SEQUENTIAL (1 worker)...")
        
        start_time = time.time()
        embeddings = []
        individual_times = []
        errors = 0
        
        for i, text in enumerate(texts):
            try:
                emb, elapsed = self.get_embedding(text)
                embeddings.append(emb)
                individual_times.append(elapsed)
                print(f"  [{i+1}/{len(texts)}] {elapsed:.2f}s", end='\r')
            except Exception as e:
                errors += 1
                print(f"  [{i+1}/{len(texts)}] ERROR: {e}")
        
        total_time = time.time() - start_time
        
        return {
            "workers": 1,
            "total_texts": len(texts),
            "successful": len(embeddings),
            "errors": errors,
            "total_time": total_time,
            "avg_time_per_text": total_time / len(texts) if texts else 0,
            "throughput": len(embeddings) / total_time if total_time > 0 else 0,
            "min_time": min(individual_times) if individual_times else 0,
            "max_time": max(individual_times) if individual_times else 0,
            "avg_individual_time": sum(individual_times) / len(individual_times) if individual_times else 0
        }
    
    def benchmark_concurrent(self, texts: List[str], workers: int) -> Dict[str, Any]:
        """Benchmark concurrent processing with specified number of workers."""
        print(f"\n🔄 Testing CONCURRENT ({workers} workers)...")
        
        start_time = time.time()
        embeddings = []
        individual_times = []
        errors = 0
        completed = 0
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_idx = {
                executor.submit(self.get_embedding, text): idx
                for idx, text in enumerate(texts)
            }
            
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    emb, elapsed = future.result()
                    embeddings.append(emb)
                    individual_times.append(elapsed)
                    completed += 1
                    print(f"  [{completed}/{len(texts)}] completed", end='\r')
                except Exception as e:
                    errors += 1
                    completed += 1
                    print(f"  [{completed}/{len(texts)}] ERROR: {e}")
        
        total_time = time.time() - start_time
        
        return {
            "workers": workers,
            "total_texts": len(texts),
            "successful": len(embeddings),
            "errors": errors,
            "total_time": total_time,
            "avg_time_per_text": total_time / len(texts) if texts else 0,
            "throughput": len(embeddings) / total_time if total_time > 0 else 0,
            "min_time": min(individual_times) if individual_times else 0,
            "max_time": max(individual_times) if individual_times else 0,
            "avg_individual_time": sum(individual_times) / len(individual_times) if individual_times else 0
        }
    
    def run_full_benchmark(self, sample_texts: List[str], worker_counts: List[int]) -> List[Dict[str, Any]]:
        """Run benchmark with multiple worker configurations."""
        results = []
        
        print("=" * 70)
        print("🚀 Ollama Embedding Performance Benchmark")
        print("=" * 70)
        print(f"URL: {self.base_url}")
        print(f"Model: {self.model_name}")
        print(f"Sample size: {len(sample_texts)} texts")
        print(f"Worker counts to test: {worker_counts}")
        print("=" * 70)
        
        # Test sequential first
        result = self.benchmark_sequential(sample_texts)
        results.append(result)
        self._print_result(result)
        
        # Test each concurrency level
        for workers in worker_counts:
            if workers == 1:
                continue  # Already tested sequential
            
            result = self.benchmark_concurrent(sample_texts, workers)
            results.append(result)
            self._print_result(result)
            
            # Brief pause between tests
            time.sleep(1)
        
        return results
    
    def _print_result(self, result: Dict[str, Any]):
        """Print a single benchmark result."""
        print(f"\n✅ Workers: {result['workers']}")
        print(f"   Total time: {result['total_time']:.2f}s")
        print(f"   Throughput: {result['throughput']:.2f} embeddings/sec")
        print(f"   Avg time per text: {result['avg_time_per_text']:.3f}s")
        print(f"   Individual request times: min={result['min_time']:.3f}s, "
              f"max={result['max_time']:.3f}s, avg={result['avg_individual_time']:.3f}s")
        if result['errors'] > 0:
            print(f"   ⚠️  Errors: {result['errors']}/{result['total_texts']}")
    
    def print_summary(self, results: List[Dict[str, Any]]):
        """Print comparison summary."""
        print("\n" + "=" * 70)
        print("📊 BENCHMARK SUMMARY")
        print("=" * 70)
        print(f"{'Workers':<10} {'Total Time':<12} {'Throughput':<18} {'Speedup':<10} {'Errors':<8}")
        print("-" * 70)
        
        baseline_time = results[0]['total_time'] if results else 1
        
        for result in results:
            speedup = baseline_time / result['total_time'] if result['total_time'] > 0 else 0
            print(f"{result['workers']:<10} "
                  f"{result['total_time']:.2f}s{' ':<6} "
                  f"{result['throughput']:.2f} emb/s{' ':<7} "
                  f"{speedup:.2f}x{' ':<6} "
                  f"{result['errors']}")
        
        # Find optimal configuration
        best = max(results, key=lambda r: r['throughput'] if r['errors'] == 0 else 0)
        print("\n" + "=" * 70)
        print(f"🏆 OPTIMAL CONFIGURATION: {best['workers']} workers")
        print(f"   Throughput: {best['throughput']:.2f} embeddings/sec")
        print(f"   Speedup vs sequential: {baseline_time / best['total_time']:.2f}x")
        print("=" * 70)
        print(f"\n💡 Recommendation: export OLLAMA_EMBED_WORKERS={best['workers']}")
        print("=" * 70)


def generate_sample_texts(count: int) -> List[str]:
    """Generate sample code snippets for testing."""
    templates = [
        "def calculate_sum(a, b):\n    return a + b",
        "class UserManager:\n    def __init__(self):\n        self.users = []",
        "async function fetchData(url) {\n    const response = await fetch(url);\n    return response.json();\n}",
        "public class HelloWorld {\n    public static void main(String[] args) {\n        System.out.println(\"Hello\");\n    }\n}",
        "function fibonacci(n) {\n    if (n <= 1) return n;\n    return fibonacci(n-1) + fibonacci(n-2);\n}",
        "SELECT users.name, orders.total\nFROM users\nJOIN orders ON users.id = orders.user_id\nWHERE orders.status = 'completed';",
        "import React from 'react';\nexport const Button = ({ label, onClick }) => (\n    <button onClick={onClick}>{label}</button>\n);",
        "interface User {\n    id: number;\n    name: string;\n    email: string;\n}\n\nfunction getUser(id: number): User | null {\n    return null;\n}",
    ]
    
    texts = []
    for i in range(count):
        # Vary the text by adding context
        template = templates[i % len(templates)]
        texts.append(f"// File: example_{i}.py\n// Function at line {i * 10}\n{template}")
    
    return texts


def test_connection(base_url: str, model_name: str) -> tuple[bool, str]:
    """Test connection to Ollama. Returns (success, actual_model_name)."""
    print(f"🔍 Testing connection to {base_url}...")
    print(f"🔍 Looking for model: {model_name}")
    
    try:
        # Test /api/tags endpoint
        req = request.Request(f"{base_url.rstrip('/')}/api/tags")
        with request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            models = [m.get('name', '') for m in data.get('models', [])]
            
            print(f"✅ Connected to Ollama")
            print(f"   Available models: {', '.join(models) if models else 'none'}")
            
            # Check for exact match or prefix match (e.g., "nomic-embed-text" matches "nomic-embed-text:latest")
            model_found = False
            matched_model = None
            
            # First try exact match
            if model_name in models:
                model_found = True
                matched_model = model_name
            else:
                # Try prefix match (model name without tag)
                base_name = model_name.split(':')[0]
                for available_model in models:
                    if available_model.startswith(base_name):
                        model_found = True
                        matched_model = available_model
                        break
            
            if not model_found:
                print(f"⚠️  Warning: Model '{model_name}' not found in available models")
                print(f"   Available models:")
                for m in models:
                    print(f"     - {m}")
                print(f"\n   Run: ollama pull {model_name}")
                return False, model_name
            
            if matched_model != model_name:
                print(f"ℹ️  Note: Using available model '{matched_model}' (requested: '{model_name}')")
            else:
                print(f"✅ Model '{model_name}' is available")
            
            return True, matched_model
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"\nTroubleshooting:")
        print(f"  1. Check Ollama is running: ollama list")
        print(f"  2. Pull model: ollama pull {model_name}")
        print(f"  3. Verify URL: {base_url}")
        return False, model_name


def main():
    # Configuration
    base_url = os.environ.get("OLLAMA_EMBED_URL", "http://localhost:11434")
    model_name = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")
    
    # Test connection first and get the actual model name to use
    success, actual_model = test_connection(base_url, model_name)
    if not success:
        sys.exit(1)
    
    # Use the actual model name that was found
    model_name = actual_model
    
    # Generate test data
    print("\n📝 Generating test samples...")
    sample_sizes = [10, 30, 64]  # Test with different batch sizes
    worker_configs = [1, 2, 4, 8, 16]  # Different concurrency levels
    
    benchmark = OllamaEmbeddingBenchmark(base_url, model_name)
    
    all_results = {}
    
    for sample_size in sample_sizes:
        print(f"\n{'='*70}")
        print(f"📦 Testing with {sample_size} samples")
        print(f"{'='*70}")
        
        texts = generate_sample_texts(sample_size)
        results = benchmark.run_full_benchmark(texts, worker_configs)
        all_results[sample_size] = results
        benchmark.print_summary(results)
    
    # Final recommendations
    print("\n" + "=" * 70)
    print("🎯 FINAL RECOMMENDATIONS")
    print("=" * 70)
    
    for sample_size, results in all_results.items():
        best = max(results, key=lambda r: r['throughput'] if r['errors'] == 0 else 0)
        print(f"\nFor batch size ~{sample_size}:")
        print(f"  Optimal workers: {best['workers']}")
        print(f"  Throughput: {best['throughput']:.2f} embeddings/sec")
    
    # Overall recommendation based on typical batch size (64)
    typical_results = all_results.get(64, all_results.get(max(all_results.keys())))
    best_overall = max(typical_results, key=lambda r: r['throughput'] if r['errors'] == 0 else 0)
    
    print("\n" + "=" * 70)
    print("💡 RECOMMENDED CONFIGURATION:")
    print("=" * 70)
    print(f"export OLLAMA_EMBED_WORKERS={best_overall['workers']}")
    print(f"\nAdd this to your ~/.zshrc or ~/.bashrc and reload with: source ~/.zshrc")
    print("=" * 70)


if __name__ == "__main__":
    main()

