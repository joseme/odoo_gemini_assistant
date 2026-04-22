import logging
import requests
import json

_logger = logging.getLogger(__name__)

# Modelos disponibles en OpenRouter
OPENROUTER_MODELS = {
    "openai/gpt-4-turbo": "GPT-4 Turbo",
    "openai/gpt-4": "GPT-4",
    "openai/gpt-3.5-turbo": "GPT-3.5 Turbo",
    "anthropic/claude-3-opus": "Claude 3 Opus",
    "anthropic/claude-3-sonnet": "Claude 3 Sonnet",
    "anthropic/claude-3-haiku": "Claude 3 Haiku",
    "google/gemini-pro": "Gemini Pro",
    "mistralai/mistral-7b-instruct": "Mistral 7B",
    "meta-llama/llama-2-70b-chat": "Llama 2 70B",
}


class OpenRouterService:
    """Service to use OpenRouter as LLM provider."""

    def __init__(
        self,
        api_key,
        model_name="openai/gpt-3.5-turbo",
        app_name="OdooGeminiAssistant",
    ):
        """
        Initialize OpenRouter service.
        
        Args:
            api_key: OpenRouter API key
            model_name: Model ID from OpenRouter (e.g., 'openai/gpt-4-turbo')
            app_name: Name of your app for OpenRouter headers
        """
        self.api_key = api_key
        self.model_name = model_name
        self.app_name = app_name
        self.base_url = "https://openrouter.io/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://odoo.example.com",
            "X-Title": app_name,
            "Content-Type": "application/json",
        }

    def chat(self, message, history=None, system_prompt=None, temperature=0.7):
        """
        Send a message to OpenRouter and get a response.
        
        Args:
            message: User message
            history: Chat history (list of dicts with 'role' and 'content')
            system_prompt: System prompt to use
            temperature: Temperature parameter (0-1)
            
        Returns:
            str: Model response text
        """
        if system_prompt is None:
            system_prompt = "You are a helpful assistant."

        # Build messages array
        messages = []
        
        # Add system prompt as first message if supported
        messages.append({
            "role": "user",
            "content": system_prompt + "\n\n" + message,
        })

        # Add chat history
        if history:
            for msg in history[-10:]:  # Last 10 messages
                role = msg.get("role", "user")
                # Ensure role is either 'user' or 'assistant'
                if role == "model":
                    role = "assistant"
                messages.append({
                    "role": role,
                    "content": msg.get("content", ""),
                })

        # Make API request
        try:
            url = f"{self.base_url}/chat/completions"
            
            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 2000,
            }

            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=60,
            )

            if response.status_code == 200:
                data = response.json()
                
                # Extract response text
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                else:
                    error_msg = f"Unexpected OpenRouter response: {data}"
                    _logger.error(error_msg)
                    raise Exception(error_msg)
            else:
                error_msg = f"OpenRouter API error: {response.status_code} - {response.text}"
                _logger.error(error_msg)
                raise Exception(error_msg)

        except requests.exceptions.Timeout:
            error_msg = "OpenRouter request timeout"
            _logger.error(error_msg)
            raise Exception(error_msg)
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to OpenRouter"
            _logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"OpenRouter error: {str(e)}"
            _logger.error(error_msg)
            raise Exception(error_msg)

    @staticmethod
    def get_available_models():
        """Get list of available models on OpenRouter."""
        return OPENROUTER_MODELS
