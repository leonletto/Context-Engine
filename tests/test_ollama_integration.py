"""
Test Ollama decoder integration.

Run with:
    REFRAG_DECODER=1 REFRAG_RUNTIME=ollama OLLAMA_URL=http://localhost:11434 OLLAMA_MODEL=qwen2.5-coder:1.5b pytest tests/test_ollama_integration.py -v
"""

import pytest
import os


def test_ollama_runtime_check(monkeypatch):
    """Test that runtime detection works for Ollama."""
    monkeypatch.setenv("REFRAG_DECODER", "1")
    monkeypatch.setenv("REFRAG_RUNTIME", "ollama")
    
    from scripts.refrag_llamacpp import is_decoder_enabled, get_runtime_kind
    
    assert is_decoder_enabled() is True
    assert get_runtime_kind() == "ollama"


def test_ollama_client_init(monkeypatch):
    """Test OllamaRefragClient initialization."""
    monkeypatch.setenv("REFRAG_DECODER", "1")
    monkeypatch.setenv("REFRAG_RUNTIME", "ollama")
    monkeypatch.setenv("OLLAMA_URL", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5-coder:1.5b")
    
    from scripts.refrag_ollama import OllamaRefragClient
    
    client = OllamaRefragClient()
    assert client.base_url == "http://localhost:11434"
    assert client.model == "qwen2.5-coder:1.5b"


def test_ollama_client_init_custom_params(monkeypatch):
    """Test OllamaRefragClient with custom parameters."""
    monkeypatch.setenv("REFRAG_RUNTIME", "ollama")
    
    from scripts.refrag_ollama import OllamaRefragClient
    
    client = OllamaRefragClient(
        base_url="http://custom:8080",
        model="custom-model:latest"
    )
    assert client.base_url == "http://custom:8080"
    assert client.model == "custom-model:latest"


def test_ollama_wrong_runtime_raises(monkeypatch):
    """Test that OllamaRefragClient raises if REFRAG_RUNTIME is not 'ollama'."""
    monkeypatch.setenv("REFRAG_RUNTIME", "llamacpp")
    
    from scripts.refrag_ollama import OllamaRefragClient
    
    with pytest.raises(ValueError, match="REFRAG_RUNTIME must be 'ollama'"):
        OllamaRefragClient()


def test_ollama_disabled_raises(monkeypatch):
    """Test that generate fails when decoder is disabled."""
    monkeypatch.setenv("REFRAG_DECODER", "0")
    monkeypatch.setenv("REFRAG_RUNTIME", "ollama")
    
    from scripts.refrag_ollama import OllamaRefragClient
    
    client = OllamaRefragClient()
    with pytest.raises(RuntimeError, match="Decoder path disabled"):
        client.generate_with_soft_embeddings("test prompt")


@pytest.mark.skipif(
    not os.environ.get("TEST_OLLAMA_LIVE"),
    reason="Set TEST_OLLAMA_LIVE=1 to run live Ollama tests"
)
def test_ollama_live_generation(monkeypatch):
    """
    Live test against actual Ollama instance.
    
    Prerequisites:
    - Ollama running on localhost:11434
    - Model pulled: ollama pull qwen2.5-coder:1.5b
    - Set TEST_OLLAMA_LIVE=1
    """
    monkeypatch.setenv("REFRAG_DECODER", "1")
    monkeypatch.setenv("REFRAG_RUNTIME", "ollama")
    monkeypatch.setenv("OLLAMA_URL", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_MODEL", os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:1.5b"))
    
    from scripts.refrag_ollama import OllamaRefragClient
    
    client = OllamaRefragClient()
    
    # Simple generation test
    result = client.generate_with_soft_embeddings(
        prompt="Say 'Hello World' and nothing else.",
        max_tokens=20,
        temperature=0.1
    )
    
    assert isinstance(result, str)
    assert len(result) > 0
    print(f"Ollama response: {result}")


@pytest.mark.skipif(
    not os.environ.get("TEST_OLLAMA_LIVE"),
    reason="Set TEST_OLLAMA_LIVE=1 to run live Ollama tests"
)
def test_ollama_code_question(monkeypatch):
    """
    Test Ollama with a code-related question.
    
    Prerequisites: Same as test_ollama_live_generation
    """
    monkeypatch.setenv("REFRAG_DECODER", "1")
    monkeypatch.setenv("REFRAG_RUNTIME", "ollama")
    monkeypatch.setenv("OLLAMA_URL", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_MODEL", os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:1.5b"))
    
    from scripts.refrag_ollama import OllamaRefragClient
    
    client = OllamaRefragClient()
    
    prompt = """Using ONLY the cited code, write a concise factual summary.

Question: What does this function do?

Code:
def hybrid_search(query: str, limit: int = 10):
    \"\"\"Perform hybrid search combining dense and lexical.\"\"\"
    dense_results = dense_search(query)
    lexical_results = lexical_search(query)
    return fuse_rrf(dense_results, lexical_results, limit)

Answer:"""
    
    result = client.generate_with_soft_embeddings(
        prompt=prompt,
        max_tokens=100,
        temperature=0.2
    )
    
    assert isinstance(result, str)
    assert len(result) > 10
    print(f"Ollama code analysis: {result}")

