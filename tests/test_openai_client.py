"""Unit tests for OpenAI client module."""

from unittest.mock import MagicMock, patch

import pytest

from app import openai_client


@pytest.fixture(autouse=True)
def reset_openai_client():
    """Reset cached client between tests to avoid cross-test pollution."""
    yield
    openai_client._client = None


def test_get_client_raises_when_api_key_missing():
    """get_client raises ValueError when OPENAI_API_KEY is not set."""
    with patch.dict("os.environ", {}, clear=True):
        # Clear any cached client
        openai_client._client = None
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            openai_client.get_client()


def test_get_client_returns_client_when_api_key_set():
    """get_client returns OpenAI client when API key is configured."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
        openai_client._client = None
        with patch("app.openai_client.OpenAI") as mock_openai:
            client = openai_client.get_client()
            mock_openai.assert_called_once_with(api_key="sk-test")
            assert client is mock_openai.return_value


def test_get_client_caches_client():
    """get_client reuses the same client instance."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
        openai_client._client = None
        with patch("app.openai_client.OpenAI") as mock_openai:
            client1 = openai_client.get_client()
            client2 = openai_client.get_client()
            mock_openai.assert_called_once()
            assert client1 is client2


def test_call_model_returns_response_text():
    """call_model returns the message content from the API response."""
    mock_choice = MagicMock()
    mock_choice.message.content = "Hello, world!"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch.object(openai_client, "get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = openai_client.call_model("Test prompt")

    assert result == "Hello, world!"
    mock_client.chat.completions.create.assert_called_once()
    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "stepfun/step-3.5-flash:free"
    assert call_kwargs["messages"][1]["content"] == "Test prompt"


def test_call_model_returns_empty_string_when_content_none():
    """call_model returns empty string when response content is None."""
    mock_choice = MagicMock()
    mock_choice.message.content = None
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch.object(openai_client, "get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = openai_client.call_model("Test")

    assert result == ""


def test_get_embedding_returns_vector():
    """get_embedding returns embedding vector from API."""
    mock_embedding = [0.1, -0.2, 0.3]
    mock_data = MagicMock()
    mock_data.embedding = mock_embedding
    mock_response = MagicMock()
    mock_response.data = [mock_data]

    with patch.object(openai_client, "get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = openai_client.get_embedding("Some text")

    assert result == mock_embedding
    mock_client.embeddings.create.assert_called_once_with(
        model="thenlper/gte-base",
        input="Some text",
    )


def test_call_model_with_api_key_uses_provided_key():
    """call_model with api_key uses provided key instead of get_client."""
    mock_choice = MagicMock()
    mock_choice.message.content = "Response"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with (
        patch("app.openai_client.OpenAI") as mock_openai_cls,
        patch.object(openai_client, "get_client") as mock_get_client,
    ):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        result = openai_client.call_model("Test", api_key="sk-user-key")

    assert result == "Response"
    mock_get_client.assert_not_called()
    mock_openai_cls.assert_called_once_with(api_key="sk-user-key")


def test_get_embedding_with_api_key_uses_provided_key():
    """get_embedding with api_key uses provided key instead of get_client."""
    mock_embedding = [0.1, 0.2]
    mock_data = MagicMock()
    mock_data.embedding = mock_embedding
    mock_response = MagicMock()
    mock_response.data = [mock_data]

    with (
        patch("app.openai_client.OpenAI") as mock_openai_cls,
        patch.object(openai_client, "get_client") as mock_get_client,
    ):
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        result = openai_client.get_embedding("Text", api_key="sk-user-key")

    assert result == mock_embedding
    mock_get_client.assert_not_called()
    mock_openai_cls.assert_called_once_with(api_key="sk-user-key")
