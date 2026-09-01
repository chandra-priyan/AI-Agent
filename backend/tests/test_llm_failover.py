import pytest
from unittest.mock import MagicMock
from app.llm.service import LLMService


@pytest.fixture
def mock_clients():
    from app.llm.service import LLMService
    LLMService._disabled_providers = set()
    LLMService._all_providers_disabled = False

    ollama = MagicMock()
    ollama.resolve_model.return_value = "qwen2.5-coder:3b-instruct-q4_K_M"
    ollama.check_health.return_value = {"running": True, "active_model": "qwen2.5-coder:3b-instruct-q4_K_M"}

    groq = MagicMock()
    groq.api_key = "valid_test_key"
    groq.check_health.return_value = {"running": True, "active_model": "gpt-mock"}

    gemini = MagicMock()
    gemini.api_key = "valid_test_key"
    gemini.check_health.return_value = {"running": True, "active_model": "gemini-mock"}

    openrouter = MagicMock()
    openrouter.api_key = "valid_test_key"
    openrouter.check_health.return_value = {"running": True, "active_model": "openrouter-mock"}

    return ollama, groq, gemini, openrouter


def test_ollama_success(mock_clients):
    ollama, groq, gemini, openrouter = mock_clients
    ollama.generate.return_value = "Ollama output"

    service = LLMService(
        ollama_client=ollama,
        groq_client=groq,
        gemini_client=gemini,
        openrouter_client=openrouter
    )
    res = service._generate_with_failover("test prompt")

    assert res == "Ollama output"
    assert service.last_provider_used == "ollama"
    assert service.last_fallback_used is False
    assert service.last_fallback_reason is None

    ollama.generate.assert_called_once()
    groq.generate.assert_not_called()
    gemini.generate.assert_not_called()
    openrouter.generate.assert_not_called()


def test_ollama_fail_groq_success(mock_clients):
    ollama, groq, gemini, openrouter = mock_clients
    ollama.generate.side_effect = Exception("Ollama connection refused")
    groq.generate.return_value = "Groq output"

    service = LLMService(
        ollama_client=ollama,
        groq_client=groq,
        gemini_client=gemini,
        openrouter_client=openrouter
    )
    res = service._generate_with_failover("test prompt")

    assert res == "Groq output"
    assert service.last_provider_used == "groq"
    assert service.last_fallback_used is True

    ollama.generate.assert_called_once()
    groq.generate.assert_called_once()
    gemini.generate.assert_not_called()
    openrouter.generate.assert_not_called()


def test_ollama_and_groq_fail_gemini_success(mock_clients):
    ollama, groq, gemini, openrouter = mock_clients
    ollama.generate.side_effect = Exception("Ollama error")
    groq.generate.side_effect = Exception("Groq error")
    gemini.generate.return_value = "Gemini output"

    service = LLMService(
        ollama_client=ollama,
        groq_client=groq,
        gemini_client=gemini,
        openrouter_client=openrouter
    )
    res = service._generate_with_failover("test prompt")

    assert res == "Gemini output"
    assert service.last_provider_used == "gemini"
    assert service.last_fallback_used is True

    ollama.generate.assert_called_once()
    groq.generate.assert_called_once()
    gemini.generate.assert_called_once()
    openrouter.generate.assert_not_called()


def test_ollama_groq_and_gemini_fail_openrouter_success(mock_clients):
    ollama, groq, gemini, openrouter = mock_clients
    ollama.generate.side_effect = Exception("Ollama error")
    groq.generate.side_effect = Exception("Groq error")
    gemini.generate.side_effect = Exception("Gemini error")
    openrouter.generate.return_value = "OpenRouter output"

    service = LLMService(
        ollama_client=ollama,
        groq_client=groq,
        gemini_client=gemini,
        openrouter_client=openrouter
    )
    res = service._generate_with_failover("test prompt")

    assert res == "OpenRouter output"
    assert service.last_provider_used == "openrouter"
    assert service.last_fallback_used is True

    ollama.generate.assert_called_once()
    groq.generate.assert_called_once()
    gemini.generate.assert_called_once()
    openrouter.generate.assert_called_once()


def test_all_providers_failed(mock_clients):
    ollama, groq, gemini, openrouter = mock_clients
    ollama.generate.side_effect = Exception("Ollama error")
    groq.generate.side_effect = Exception("Groq error")
    gemini.generate.side_effect = Exception("Gemini error")
    openrouter.generate.side_effect = Exception("OpenRouter error")

    service = LLMService(
        ollama_client=ollama,
        groq_client=groq,
        gemini_client=gemini,
        openrouter_client=openrouter
    )
    
    with pytest.raises(Exception) as exc_info:
        service._generate_with_failover("test prompt")

    assert "AI service temporarily unavailable. Please try again later." in str(exc_info.value)
    assert service.last_provider_used == "openrouter"
    assert service.last_fallback_used is True
    assert "Ollama failed: Ollama error" in service.last_fallback_reason
    assert "Groq failed: Groq error" in service.last_fallback_reason
    assert "Gemini failed: Gemini error" in service.last_fallback_reason
    assert "OpenRouter failed: OpenRouter error" in service.last_fallback_reason


def test_json_malformed_trigger_failover(mock_clients):
    ollama, groq, gemini, openrouter = mock_clients
    ollama.generate.return_value = "This is not json"
    groq.generate.return_value = '{"answer": "valid json"}'

    service = LLMService(
        ollama_client=ollama,
        groq_client=groq,
        gemini_client=gemini,
        openrouter_client=openrouter
    )
    res = service._generate_with_failover("test prompt", format_json=True)

    assert res == '{"answer": "valid json"}'
    assert service.last_provider_used == "groq"
    assert service.last_fallback_used is True
    
    ollama.generate.assert_called_once()
    groq.generate.assert_called_once()
