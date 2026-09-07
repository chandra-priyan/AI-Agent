import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


class GroqClientError(Exception):
    pass


class GroqClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", GROQ_API_KEY)
        self.api_url = api_url or os.getenv("GROQ_API_URL", GROQ_API_URL)
        self.model = model or os.getenv("GROQ_MODEL", GROQ_MODEL)

    def check_health(self) -> Dict[str, Any]:
        """Check if Groq API key is present and configured."""
        api_key = os.getenv("GROQ_API_KEY") or self.api_key
        model = os.getenv("GROQ_MODEL") or self.model or "llama-3.3-70b-versatile"
        if not api_key:
            return {"running": False, "models": [], "error": "GROQ_API_KEY is not configured."}
        return {"running": True, "active_model": model, "models": [model]}

    def resolve_model(self) -> str:
        model = os.getenv("GROQ_MODEL") or self.model or "llama-3.3-70b-versatile"
        return model

    def generate(self, prompt: str, system: Optional[str] = None, format_json: bool = False, temperature: float = 0.2) -> str:
        """Generate response from Groq API endpoint with model fallback handling."""
        api_key = os.getenv("GROQ_API_KEY") or self.api_key
        api_url = os.getenv("GROQ_API_URL") or self.api_url
        if not api_key:
            raise GroqClientError("GROQ_API_KEY is missing. Please set GROQ_API_KEY in your environment.")

        primary_model = self.resolve_model()
        candidate_models = [primary_model, "llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "llama3-70b-8192", "llama-3.1-8b-instant", "llama3-8b-8192"]
        # Deduplicate while preserving candidate order
        models_to_try = []
        for m in candidate_models:
            if m and m not in models_to_try:
                models_to_try.append(m)

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        timeout = int(os.getenv("LLM_TIMEOUT", "45"))
        last_error = None

        for model in models_to_try:
            payload: Dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": temperature
            }
            if format_json:
                payload["response_format"] = {"type": "json_object"}

            body = json.dumps(payload).encode("utf-8")
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "Mozilla/5.0"
            }

            req = urllib.request.Request(
                api_url,
                data=body,
                headers=headers,
                method="POST"
            )

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
                        raise GroqClientError(f"Groq API returned HTTP status {response.status}")
            except urllib.error.HTTPError as err:
                err_msg = err.read().decode("utf-8") if err.fp else str(err)
                last_error = f"HTTP error {err.code}: {err_msg}"
                if err.code == 404 or "model_not_found" in err_msg.lower():
                    continue # Try next candidate model on 404
                raise GroqClientError(f"Groq API {last_error}")
            except urllib.error.URLError as err:
                last_error = f"Connection error: {str(err)}"
                raise GroqClientError(f"Groq API {last_error}")
            except Exception as err:
                last_error = f"Unexpected error: {str(err)}"
                raise GroqClientError(f"Groq API {last_error}")

        raise GroqClientError(f"Groq API models failed: {last_error}")
