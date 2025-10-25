"""
Ollama embedding adapter for Context-Engine.

Provides embeddings via Ollama instead of fastembed for faster local performance,
especially on Apple Silicon or systems with Ollama already running.

Usage:
    Set environment variables:
    - EMBEDDING_PROVIDER=ollama
    - OLLAMA_EMBED_URL=http://host.docker.internal:11434  (default)
    - OLLAMA_EMBED_MODEL=nomic-embed-text:137m-v1.5-fp16 (or your model)
"""

from __future__ import annotations
import os
import json
from typing import List, Any
from urllib import request


class OllamaEmbedding:
    """Ollama embedding adapter compatible with fastembed interface."""
    
    def __init__(self, model_name: str = "n", **kwargs):
        self.model_name = model_name
        self.base_url = os.environ.get("OLLAMA_EMBED_URL", "http://host.docker.internal:11434")
        self._dim = None
        
        # Test connection
        try:
            self._get_embedding("test")
        except Exception as e:
            raise RuntimeError(
                f"Failed to connect to Ollama at {self.base_url}. "
                f"Make sure Ollama is running and model '{model_name}' is pulled. "
                f"Error: {e}"
            )
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text."""
        payload = {
            "model": self.model_name,
            "prompt": text
        }
        
        req = request.Request(
            f"{self.base_url.rstrip('/')}/api/embeddings",
            method="POST"
        )
        req.add_header("Content-Type", "application/json")
        data = json.dumps(payload).encode("utf-8")
        
        timeout = float(os.environ.get("OLLAMA_EMBED_TIMEOUT", "60"))
        
        with request.urlopen(req, data=data, timeout=timeout) as resp:
            body = resp.read()
        
        result = json.loads(body.decode("utf-8"))
        return result["embedding"]
    
    def embed(self, texts: List[str]) -> Any:
        """
        Embed a batch of texts.
        
        Returns a generator that yields numpy-like arrays (lists of floats),
        matching fastembed's interface.
        """
        for text in texts:
            embedding = self._get_embedding(text)
            
            # Cache dimension on first call
            if self._dim is None:
                self._dim = len(embedding)
            
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

