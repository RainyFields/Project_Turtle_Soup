from unittest.mock import patch

from agents.model_providers.gemini_provider import GeminiProvider
from agents.provider_factory import get_provider


def test_get_provider_gemini_routing():
    with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
        with patch.object(GeminiProvider, "__init__", lambda self, api_key=None: None):
            with patch.object(GeminiProvider, "generate", return_value='{"id":"x"}') as gen:
                provider = get_provider("gemini")
                out = provider.generate(
                    system="sys",
                    user="user",
                    model="gemini-2.0-flash",
                )
    assert out == '{"id":"x"}'
    gen.assert_called_once()
