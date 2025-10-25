"""
Ollama embedding adapter for Context-Engine.

Provides embeddings via Ollama instead of fastembed for faster local performance,
especially on Apple Silicon or systems with Ollama already running.

Performance (based on benchmark with nomic-embed-text:137m-v1.5-fp16):
    - Sequential (1 worker): ~56 emb/sec
    - 2 workers: ~139 emb/sec (2.5x faster)
    - 4 workers: ~147 emb/sec (2.6x faster) ⭐ Recommended default
    - 8 workers: ~159 emb/sec (2.8x faster)
    
    Run `python3 scripts/benchmark_ollama_embeddings.py` to find optimal settings for your system.

Usage:
    Set environment variables:
    - EMBEDDING_PROVIDER=ollama
    - OLLAMA_EMBED_URL=http://host.docker.internal:11434  (default)
    - OLLAMA_EMBED_MODEL=nomic-embed-text:137m-v1.5-fp16 (or your model)
    - OLLAMA_EMBED_TIMEOUT=120  (per-request timeout, default 120s)
    - OLLAMA_EMBED_RETRIES=3    (retry failed requests, default 3)
    - OLLAMA_EMBED_WORKERS=4    (concurrent requests, default 4 - conservative but 2.6x faster)
"""

from __future__ import annotations
import os
import json
import time
from typing import List, Any
from urllib import request
from urllib.error import URLError, HTTPError
from concurrent.futures import ThreadPoolExecutor, as_completed


class OllamaEmbedding:
    """Ollama embedding adapter compatible with fastembed interface.
    
    Uses concurrent requests to speed up batch embedding processing.
    """
    
    def __init__(self, model_name: str = "n", **kwargs):
        self.model_name = model_name
        self.base_url = os.environ.get("OLLAMA_EMBED_URL", "http://host.docker.internal:11434")
        self.timeout = float(os.environ.get("OLLAMA_EMBED_TIMEOUT", "120"))
        self.max_retries = int(os.environ.get("OLLAMA_EMBED_RETRIES", "3"))
        self.max_workers = int(os.environ.get("OLLAMA_EMBED_WORKERS", "4"))
        self._dim = None
        self._embed_count = 0
        self._last_report_time = time.time()
        
        # Test connection with retries
        print(f"Connecting to Ollama at {self.base_url} with model '{model_name}' (workers={self.max_workers})...")
        try:
            self._get_embedding("test connection", is_test=True)
            print(f"✓ Ollama embedding connection successful")
        except Exception as e:
            raise RuntimeError(
                f"Failed to connect to Ollama at {self.base_url}. "
                f"Make sure Ollama is running and model '{model_name}' is pulled. "
                f"Run: ollama pull {model_name}\n"
                f"Error: {e}"
            )
    
    def _get_embedding(self, text: str, is_test: bool = False) -> List[float]:
        """Get embedding for a single text with retry logic."""
        payload = {
            "model": self.model_name,
            "prompt": text
        }
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                req = request.Request(
                    f"{self.base_url.rstrip('/')}/api/embeddings",
                    method="POST"
                )
                req.add_header("Content-Type", "application/json")
                data = json.dumps(payload).encode("utf-8")
                
                with request.urlopen(req, data=data, timeout=self.timeout) as resp:
                    body = resp.read()
                
                result = json.loads(body.decode("utf-8"))
                
                # Track progress every 50 embeddings
                if not is_test:
                    self._embed_count += 1
                    if self._embed_count % 50 == 0:
                        elapsed = time.time() - self._last_report_time
                        rate = 50 / elapsed if elapsed > 0 else 0
                        print(f"[ollama-embed] Processed {self._embed_count} embeddings ({rate:.1f}/sec)")
                        self._last_report_time = time.time()
                
                return result["embedding"]
                
            except (URLError, HTTPError, TimeoutError, OSError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    print(f"[ollama-embed] Retry {attempt + 1}/{self.max_retries} after error: {e}")
                    print(f"[ollama-embed] Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    # Final attempt failed
                    error_msg = (
                        f"Failed to get embedding after {self.max_retries} attempts. "
                        f"Last error: {e}\n"
                        f"Suggestions:\n"
                        f"  1. Check Ollama is running: curl {self.base_url}/api/tags\n"
                        f"  2. Verify model is pulled: ollama list | grep {self.model_name}\n"
                        f"  3. Increase timeout: export OLLAMA_EMBED_TIMEOUT=300\n"
                        f"  4. Check Docker networking: docker run --rm --add-host=host.docker.internal:host-gateway curlimages/curl:latest curl {self.base_url}/api/tags"
                    )
                    raise RuntimeError(error_msg) from last_error
    
    def embed(self, texts: List[str]) -> Any:
        """
        Embed a batch of texts using concurrent requests.
        
        Returns a generator that yields numpy-like arrays (lists of floats),
        matching fastembed's interface.
        
        Note: Results are yielded in the same order as input texts, even though
        requests are processed concurrently.
        """
        if not texts:
            return
        
        # For small batches or single items, process sequentially
        if len(texts) <= 2:
            for text in texts:
                embedding = self._get_embedding(text)
                if self._dim is None:
                    self._dim = len(embedding)
                yield embedding
            return
        
        # For larger batches, use concurrent requests
        batch_start = time.time()
        embeddings = [None] * len(texts)  # Pre-allocate to maintain order
        errors = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks with their indices
            future_to_idx = {
                executor.submit(self._get_embedding, text): idx
                for idx, text in enumerate(texts)
            }
            
            # Collect results as they complete
            completed_count = 0
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    embedding = future.result()
                    embeddings[idx] = embedding
                    completed_count += 1
                    
                    # Cache dimension on first successful embedding
                    if self._dim is None:
                        self._dim = len(embedding)
                    
                    # Progress reporting
                    self._embed_count += 1
                    if self._embed_count % 50 == 0:
                        elapsed = time.time() - self._last_report_time
                        rate = 50 / elapsed if elapsed > 0 else 0
                        print(f"[ollama-embed] Processed {self._embed_count} embeddings ({rate:.1f}/sec)")
                        self._last_report_time = time.time()
                        
                except Exception as e:
                    errors.append((idx, str(e)))
                    embeddings[idx] = None
        
        # Report batch completion
        batch_elapsed = time.time() - batch_start
        batch_rate = len(texts) / batch_elapsed if batch_elapsed > 0 else 0
        if len(texts) >= 10:  # Only report for larger batches
            print(f"[ollama-embed] Batch of {len(texts)} completed in {batch_elapsed:.1f}s ({batch_rate:.1f}/sec)")
        
        # Check for errors
        if errors:
            error_msg = f"Failed to embed {len(errors)}/{len(texts)} texts:\n"
            for idx, err in errors[:3]:  # Show first 3 errors
                error_msg += f"  Text {idx}: {err}\n"
            if len(errors) > 3:
                error_msg += f"  ... and {len(errors) - 3} more errors\n"
            raise RuntimeError(error_msg)
        
        # Yield results in original order
        for embedding in embeddings:
            yield embedding
    
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        if self._dim is None:
            # Probe with a test embedding
            test_emb = self._get_embedding("dimension probe")
            self._dim = len(test_emb)
        return self._dim


def get_embedding_model(model_name: str, provider: str = "fastembed"):
    """
    Factory function to get the appropriate embedding model.
    
    Args:
        model_name: Model name/identifier
        provider: "fastembed" or "ollama"
    
    Returns:
        Embedding model instance with .embed() method
    """
    provider = provider.lower().strip()
    
    if provider == "ollama":
        # Use Ollama
        ollama_model = os.environ.get("OLLAMA_EMBED_MODEL", model_name)
        print(f"Using Ollama embeddings: {ollama_model}")
        return OllamaEmbedding(model_name=ollama_model)
    
    elif provider == "fastembed" or not provider:
        # Use fastembed (default)
        from fastembed import TextEmbedding
        print(f"Using fastembed: {model_name}")
        return TextEmbedding(model_name=model_name)
    
    else:
        raise ValueError(
            f"Unknown embedding provider: {provider}. "
            f"Use 'fastembed' or 'ollama'"
        )

