"""
Ollama adapter for decoder-side ReFRAG.

This adapter provides a compatible interface for using Ollama instead of llama.cpp
as the decoder backend. It matches the same API as LlamaCppRefragClient.

Chat Template Formatting:
  - Automatically detects model type (Qwen or Phi) and formats prompts with proper tokens
  - Qwen models: <|im_start|>role\ncontent<|im_end|>
  - Phi models: <|role|>content<|end|>
  - Override detection with OLLAMA_CHAT_TEMPLATE env var

Usage:
  Set these environment variables:
    REFRAG_DECODER=1
    REFRAG_RUNTIME=ollama
    OLLAMA_URL=http://host.docker.internal:11434  (default)
    OLLAMA_MODEL=qwen2.5-coder:1.5b     (or any model you have pulled)
    OLLAMA_CHAT_TEMPLATE=qwen           (optional, auto-detected from model name)
"""

from __future__ import annotations
import os
from typing import Any, Dict, Optional


def _bool_env(name: str, default: str = "0") -> bool:
    return str(os.environ.get(name, default)).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def is_decoder_enabled() -> bool:
    return _bool_env("REFRAG_DECODER", "0")


def get_runtime_kind() -> str:
    return str(os.environ.get("REFRAG_RUNTIME", "llamacpp")).strip().lower()


class OllamaRefragClient:
    """Ollama adapter for decoder path.
    
    Uses Ollama's /api/generate endpoint with the same interface as LlamaCppRefragClient.
    Automatically formats prompts with proper chat templates based on model type.
    """

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None) -> None:
        self.base_url = base_url or os.environ.get(
            "OLLAMA_URL", "http://host.docker.internal:11434"
        )
        self.model = model or os.environ.get(
            "OLLAMA_MODEL", "qwen2.5-coder:1.5b"
        )
        if get_runtime_kind() != "ollama":
            raise ValueError(
                "REFRAG_RUNTIME must be 'ollama' for OllamaRefragClient"
            )
        
        # Detect model type for chat template formatting
        self._detect_model_type()
    
    def _detect_model_type(self) -> None:
        """Detect model type from model name for chat template selection."""
        model_lower = self.model.lower()
        
        if any(x in model_lower for x in ["qwen", "qwq"]):
            self.model_type = "qwen"
        elif any(x in model_lower for x in ["phi", "phi-3", "phi-4"]):
            self.model_type = "phi"
        else:
            # Default to qwen format as it's more common
            self.model_type = "qwen"
            import warnings
            warnings.warn(
                f"Unknown model type for '{self.model}', defaulting to Qwen chat template. "
                "Set OLLAMA_CHAT_TEMPLATE=qwen or OLLAMA_CHAT_TEMPLATE=phi to override."
            )
        
        # Allow override via environment variable
        env_template = os.environ.get("OLLAMA_CHAT_TEMPLATE", "").strip().lower()
        if env_template in ["qwen", "phi"]:
            self.model_type = env_template
    
    def _format_prompt(self, user_prompt: str, system_prompt: Optional[str] = None) -> str:
        """Format prompt with proper chat template tokens based on model type.
        
        Args:
            user_prompt: The main user prompt
            system_prompt: Optional system prompt (defaults based on model)
        
        Returns:
            Formatted prompt string with chat template tokens
        """
        if self.model_type == "qwen":
            # Qwen format: <|im_start|>role\ncontent<|im_end|>
            if system_prompt is None:
                system_prompt = "You are a helpful coding assistant. Give brief, direct answers."
            
            formatted = f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
            formatted += f"<|im_start|>user\n{user_prompt}<|im_end|>\n"
            formatted += "<|im_start|>assistant\n"
            
            return formatted
            
        elif self.model_type == "phi":
            # Phi format: <|role|>content<|end|>
            if system_prompt is None:
                system_prompt = "You are a helpful coding assistant. Give brief, direct answers."
            
            formatted = f"<|system|>{system_prompt}<|end|>\n"
            formatted += f"<|user|>{user_prompt}<|end|>\n"
            formatted += "<|assistant|>"
            
            return formatted
        
        # Fallback to plain prompt (shouldn't happen)
        return user_prompt

    def _post(self, path: str, json_payload: Dict[str, Any]) -> Dict[str, Any]:
        import json as _json
        from urllib import request

        req = request.Request(self.base_url.rstrip("/") + path, method="POST")
        req.add_header("Content-Type", "application/json")
        data = _json.dumps(json_payload).encode("utf-8")
        _timeout = float(os.environ.get("OLLAMA_TIMEOUT_SEC", "120") or 120)
        
        with request.urlopen(req, data=data, timeout=_timeout) as resp:
            # Ollama streams by default, we need to read all lines and take the final one
            body = resp.read()
        
        # Parse the response - Ollama returns NDJSON (one JSON per line)
        # The final line contains the complete response
        lines = body.decode("utf-8").strip().split("\n")
        result = {"response": ""}
        
        for line in lines:
            if line.strip():
                chunk = _json.loads(line)
                if "response" in chunk:
                    result["response"] += chunk["response"]
                if chunk.get("done", False):
                    result.update(chunk)
        
        return result

    def generate_with_soft_embeddings(
        self,
        prompt: str,
        soft_embeddings: Optional[list[list[float]]] = None,
        max_tokens: int = 256,
        **gen_kwargs: Any,
    ) -> str:
        """Generate text using Ollama.
        
        Note: Ollama doesn't support soft_embeddings, so that parameter is ignored.
        This is compatible with the "prompt" mode of the decoder path.
        
        The prompt will be automatically formatted with the appropriate chat template
        based on the model type (Qwen or Phi).
        """
        if not is_decoder_enabled():
            raise RuntimeError("Decoder path disabled: set REFRAG_DECODER=1 to enable")
        
        if soft_embeddings is not None:
            import warnings
            warnings.warn(
                "Ollama does not support soft_embeddings; falling back to prompt-only mode"
            )
        
        # Format the prompt with proper chat template
        formatted_prompt = self._format_prompt(prompt)
        
        # Map llama.cpp parameters to Ollama's API format
        # Reference: https://github.com/ollama/ollama/blob/main/docs/api.md#generate-a-completion
        options = {}
        
        # Temperature
        if "temperature" in gen_kwargs:
            options["temperature"] = float(gen_kwargs["temperature"])
        else:
            options["temperature"] = 0.1
        
        # Top-k
        if "top_k" in gen_kwargs:
            options["top_k"] = int(gen_kwargs["top_k"])
        else:
            options["top_k"] = 40
        
        # Top-p
        if "top_p" in gen_kwargs:
            options["top_p"] = float(gen_kwargs["top_p"])
        else:
            options["top_p"] = 0.9
        
        # Repetition penalty (Ollama uses repeat_penalty)
        if "repeat_penalty" in gen_kwargs:
            options["repeat_penalty"] = float(gen_kwargs["repeat_penalty"])
        else:
            options["repeat_penalty"] = float(
                os.environ.get("DECODER_REPEAT_PENALTY", "1.05")
            )
        
        # Repeat last N
        if "repeat_last_n" in gen_kwargs:
            options["repeat_last_n"] = int(gen_kwargs["repeat_last_n"])
        else:
            options["repeat_last_n"] = int(
                os.environ.get("DECODER_REPEAT_LAST_N", "128")
            )
        
        # Presence/frequency penalties (Ollama supports these)
        if "presence_penalty" in gen_kwargs:
            options["presence_penalty"] = float(gen_kwargs["presence_penalty"])
        elif os.environ.get("DECODER_PRESENCE_PENALTY"):
            options["presence_penalty"] = float(
                os.environ.get("DECODER_PRESENCE_PENALTY", "0.0")
            )
        
        if "frequency_penalty" in gen_kwargs:
            options["frequency_penalty"] = float(gen_kwargs["frequency_penalty"])
        elif os.environ.get("DECODER_FREQUENCY_PENALTY"):
            options["frequency_penalty"] = float(
                os.environ.get("DECODER_FREQUENCY_PENALTY", "0.0")
            )
        
        # Num predict (max tokens)
        options["num_predict"] = int(gen_kwargs.get("max_tokens", max_tokens))
        
        # Stop sequences - add model-specific stop tokens
        stop = list(gen_kwargs.get("stop") or [])
        
        # Add appropriate stop tokens based on model type
        if self.model_type == "qwen":
            if "<|im_end|>" not in stop:
                stop.append("<|im_end|>")
        elif self.model_type == "phi":
            if "<|end|>" not in stop:
                stop.append("<|end|>")
        
        # Always include double newline as stop token for cleaner output
        if "\n\n" not in stop:
            stop.append("\n\n")
        
        payload = {
            "model": self.model,
            "prompt": formatted_prompt,
            "stream": True,  # We still use streaming but consume it all
            "options": options,
        }
        
        if stop:
            payload["stop"] = stop
        
        try:
            res = self._post("/api/generate", payload)
        except Exception as e:
            raise RuntimeError(f"Ollama generate failed: {e}")
        
        # Extract the response text
        return (res.get("response") or "").strip()

