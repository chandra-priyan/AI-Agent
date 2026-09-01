import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


class OllamaClientError(Exception):
    pass


class OllamaClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", OLLAMA_BASE_URL)
        # Verify the model is read from OLLAMA_MODEL environment variable dynamically
        self.model = model or os.getenv("OLLAMA_MODEL")
        
        env_timeout = os.getenv("OLLAMA_TIMEOUT_SECONDS")
        if env_timeout is not None:
            try:
                self.timeout = float(env_timeout)
            except ValueError:
                self.timeout = 60.0
        else:
            self.timeout = timeout if timeout is not None else 60.0

    def resolve_model(self) -> str:
        model = os.getenv("OLLAMA_MODEL") or self.model
        if not model:
            raise OllamaClientError("OLLAMA_MODEL environment variable is not configured.")
        return model

    def resolve_timeout(self) -> float:
        env_timeout = os.getenv("OLLAMA_TIMEOUT_SECONDS")
        if env_timeout is not None:
            try:
                return float(env_timeout)
            except ValueError:
                return 60.0
        return self.timeout

    def check_health(self) -> Dict[str, Any]:
        """Check if Ollama service is reachable and the required model is installed."""
        try:
            model = self.resolve_model()
        except OllamaClientError as err:
            return {"running": False, "models": [], "error": str(err)}

        base_url = os.getenv("OLLAMA_BASE_URL") or self.base_url
        url = f"{base_url.rstrip('/')}/api/tags"
        req = urllib.request.Request(url, method="GET")
        
        # A shorter timeout for health checking (at most 2.0 seconds) to avoid freezing
        timeout = min(2.0, self.resolve_timeout())
        
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status in (200, 201):
                    result = json.loads(response.read().decode("utf-8"))
                    models_list = result.get("models", [])
                    available_model_names = [m.get("name") for m in models_list if m.get("name")]
                    
                    found = False
                    for available_name in available_model_names:
                        if available_name == model:
                            found = True
                            break
                        # Handle cases where model name exists with/without ':latest' suffix
                        if ":" in available_name and ":" not in model:
                            if available_name.split(":")[0] == model:
                                found = True
                                break
                        if ":" not in available_name and ":" in model:
                            if model.split(":")[0] == available_name:
                                found = True
                                break
                                
                    if found:
                        return {"running": True, "active_model": model, "models": [model]}
                    else:
                        return {
                            "running": False,
                            "models": available_model_names,
                            "error": f"Model '{model}' is not available in local Ollama installation (available: {', '.join(available_model_names)})."
                        }
                else:
                    return {
                        "running": False,
                        "models": [],
                        "error": f"Ollama HTTP error during tags check: {response.status}"
                    }
        except urllib.error.URLError as err:
            return {
                "running": False,
                "models": [],
                "error": f"Ollama service unavailable: {str(err)}"
            }
        except Exception as err:
            return {
                "running": False,
                "models": [],
                "error": f"Unexpected error during Ollama health check: {str(err)}"
            }

    def generate(self, prompt: str, system: Optional[str] = None, format_json: bool = False, temperature: float = 0.2) -> str:
        """Generate response from Ollama API endpoint."""
        model = self.resolve_model()
        base_url = os.getenv("OLLAMA_BASE_URL") or self.base_url

        # Verify reachability and model presence before attempting generation
        health = self.check_health()
        if not health["running"]:
            raise OllamaClientError(health["error"] or f"Ollama model '{model}' is unavailable or service is unreachable.")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        if format_json:
            payload["format"] = "json"
            
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
        
        url = f"{base_url.rstrip('/')}/api/chat"
        req = urllib.request.Request(
            url,
            data=body,
            headers=headers,
            method="POST"
        )
        
        timeout = self.resolve_timeout()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status in (200, 201):
                    result = json.loads(response.read().decode("utf-8"))
                    message = result.get("message", {})
                    content = message.get("content", "")
                    if format_json:
                        json.loads(content)  # Validate json response structure
                    return content
                else:
                    raise OllamaClientError(f"Ollama API returned HTTP status {response.status}")
        except urllib.error.HTTPError as err:
            err_msg = err.read().decode("utf-8") if err.fp else str(err)
            raise OllamaClientError(f"Ollama API HTTP error {err.code}: {err_msg}")
        except urllib.error.URLError as err:
            raise OllamaClientError(f"Ollama connection error (refused/timeout): {str(err)}")
        except json.JSONDecodeError as err:
            raise OllamaClientError(f"Ollama response malformed (invalid JSON): {str(err)}")
        except Exception as err:
            raise OllamaClientError(f"Ollama generation failure: {str(err)}")
