import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

DEFAULT_OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
DEFAULT_OPENROUTER_URL = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
DEFAULT_OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b")


class OpenRouterClientError(Exception):
    pass


class OpenRouterClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", DEFAULT_OPENROUTER_KEY)
        self.api_url = api_url or os.getenv("OPENROUTER_API_URL", DEFAULT_OPENROUTER_URL)
        self.model = model or os.getenv("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL)

    def check_health(self) -> Dict[str, Any]:
        """Check if OpenRouter API environment is set up."""
        api_key = os.getenv("OPENROUTER_API_KEY") or self.api_key
        model = os.getenv("OPENROUTER_MODEL") or self.model
        if not api_key:
            return {"running": False, "models": [], "error": "OPENROUTER_API_KEY is not configured."}
        if not model:
            return {"running": False, "models": [], "error": "OPENROUTER_MODEL is not configured."}
        return {"running": True, "active_model": model, "models": [model]}

    def resolve_model(self) -> str:
        model = os.getenv("OPENROUTER_MODEL") or self.model
        if not model:
            raise OpenRouterClientError("OPENROUTER_MODEL is not configured in the environment.")
        return model

    def generate(self, prompt: str, system: Optional[str] = None, format_json: bool = False, temperature: float = 0.2) -> str:
        """Generate response from OpenRouter API endpoint."""
        api_key = os.getenv("OPENROUTER_API_KEY") or self.api_key
        if not api_key:
            raise OpenRouterClientError("OPENROUTER_API_KEY is missing. Please set OPENROUTER_API_KEY in your environment.")
        
        active_model = self.resolve_model()

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": active_model,
            "messages": messages,
            "temperature": temperature
        }
        if format_json:
            payload["response_format"] = {"type": "json_object"}

        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://localhost:8000",
            "X-Title": "Autonomous Data Scientist",
            "User-Agent": "Mozilla/5.0"
        }

        req = urllib.request.Request(
            self.api_url,
            data=body,
            headers=headers,
            method="POST"
        )

        timeout = int(os.getenv("LLM_TIMEOUT", "3"))
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status in (200, 201):
                    result = json.loads(response.read().decode("utf-8"))
                    choices = result.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        return content
                    return ""
                else:
                    raise OpenRouterClientError(f"OpenRouter API returned HTTP status {response.status}")
        except urllib.error.HTTPError as err:
            err_msg = err.read().decode("utf-8") if err.fp else str(err)
            raise OpenRouterClientError(f"OpenRouter API HTTP error {err.code}: {err_msg}")
        except urllib.error.URLError as err:
            raise OpenRouterClientError(f"OpenRouter API connection error: {str(err)}")
        except Exception as err:
            raise OpenRouterClientError(f"Unexpected error communicating with OpenRouter API: {str(err)}")
