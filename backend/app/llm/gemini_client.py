import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

DEFAULT_GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


class GeminiClientError(Exception):
    pass


class GeminiClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", DEFAULT_GEMINI_KEY)
        self.model = model or os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)

    def check_health(self) -> Dict[str, Any]:
        """Check if Gemini API key is configured."""
        api_key = os.getenv("GEMINI_API_KEY") or self.api_key
        model = os.getenv("GEMINI_MODEL") or self.model
        if not api_key:
            return {"running": False, "models": [], "error": "GEMINI_API_KEY is not configured."}
        return {"running": True, "active_model": model, "models": [model]}

    def resolve_model(self) -> str:
        model = os.getenv("GEMINI_MODEL") or self.model
        return model

    def generate(self, prompt: str, system: Optional[str] = None, format_json: bool = False, temperature: float = 0.2) -> str:
        """Generate response from Google Gemini API."""
        api_key = os.getenv("GEMINI_API_KEY") or self.api_key
        model = os.getenv("GEMINI_MODEL") or self.model
        if not api_key:
            raise GeminiClientError("GEMINI_API_KEY is missing. Please set GEMINI_API_KEY in your environment.")

        # Gemini API Endpoint URL
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        contents = [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]

        generation_config: Dict[str, Any] = {
            "temperature": temperature
        }
        if format_json:
            generation_config["responseMimeType"] = "application/json"

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": generation_config
        }

        if system:
            payload["systemInstruction"] = {
                "parts": [
                    {"text": system}
                ]
            }

        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        timeout = int(os.getenv("LLM_TIMEOUT", "3"))
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status in (200, 201):
                    result = json.loads(response.read().decode("utf-8"))
                    candidates = result.get("candidates", [])
                    if candidates:
                        content_obj = candidates[0].get("content", {})
                        parts = content_obj.get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                    return ""
                else:
                    raise GeminiClientError(f"Gemini API returned HTTP status {response.status}")
        except urllib.error.HTTPError as err:
            err_msg = err.read().decode("utf-8") if err.fp else str(err)
            raise GeminiClientError(f"Gemini API HTTP error {err.code}: {err_msg}")
        except urllib.error.URLError as err:
            raise GeminiClientError(f"Gemini API connection error: {str(err)}")
        except Exception as err:
            raise GeminiClientError(f"Unexpected error communicating with Gemini API: {str(err)}")
