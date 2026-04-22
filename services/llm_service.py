"""
Unified LLM Service that supports both Google Gemini and OpenRouter.
Abstracts the differences between providers.
"""

import logging
import google.generativeai as genai
import requests

from .openrouter_service import OpenRouterService

_logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
Eres un asistente experto en Odoo 17. Tu función es ayudar a los usuarios \
a usar el sistema de forma clara, concisa y práctica.

NORMAS:
- Responde siempre en el mismo idioma que el usuario
- Sé directo y práctico, evita rodeos
- Si no sabes algo, dilo honestamente
- Usa formato markdown cuando sea útil (listas, código, negritas)
- Para instrucciones paso a paso, usa listas numeradas
- Si usas información de búsqueda web, menciona la fuente
"""


class LLMService:
    """
    Unified service for different LLM providers.
    Supports: Google Gemini, OpenRouter
    """

    PROVIDER_GOOGLE = "google"
    PROVIDER_OPENROUTER = "openrouter"

    def __init__(
        self,
        provider="google",
        api_key=None,
        model_name=None,
        anythingllm_url=None,
        anythingllm_key=None,
        anythingllm_workspace=None,
        enable_web_search=True,
    ):
        """
        Initialize LLM Service.
        
        Args:
            provider: "google" or "openrouter"
            api_key: API key for the provider
            model_name: Model ID to use
            anythingllm_*: AnythingLLM configuration
            enable_web_search: Enable web search fallback
        """
        self.provider = provider
        self.api_key = api_key
        self.model_name = model_name or self._get_default_model()

        # Import here to avoid circular imports
        from .anything_llm_service import AnythingLLMService
        from .web_search_service import WebSearchService

        # Initialize AnythingLLM service
        self.anythingllm_service = None
        if anythingllm_url and anythingllm_key and anythingllm_workspace:
            self.anythingllm_service = AnythingLLMService(
                base_url=anythingllm_url,
                api_key=anythingllm_key,
                workspace_name=anythingllm_workspace,
            )

        # Initialize web search service
        self.web_search_service = WebSearchService(enabled=enable_web_search)

        # Initialize provider-specific service
        if provider == self.PROVIDER_GOOGLE:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(self.model_name)
        elif provider == self.PROVIDER_OPENROUTER:
            self.openrouter_service = OpenRouterService(
                api_key=api_key,
                model_name=self.model_name,
            )

    def _get_default_model(self):
        """Get default model for provider."""
        if self.provider == self.PROVIDER_GOOGLE:
            return "gemini-1.5-flash"
        elif self.provider == self.PROVIDER_OPENROUTER:
            return "openai/gpt-3.5-turbo"
        return "gemini-1.5-flash"

    def _get_anythingllm_context(self, message):
        """Get context from AnythingLLM if available."""
        if not self.anythingllm_service or not self.anythingllm_service.is_configured():
            return None

        try:
            result = self.anythingllm_service.query_workspace(message, top_k=5)
            if result.get("success"):
                return result.get("context", "")
        except Exception as e:
            _logger.warning(f"Error querying AnythingLLM: {str(e)}")

        return None

    def _get_web_search_context(self, message):
        """Get web search results if AnythingLLM didn't provide enough."""
        if not self.web_search_service.enabled:
            return None

        try:
            results = self.web_search_service.search(message, max_results=3)
            if results.get("success") and results.get("results"):
                return self.web_search_service.format_results_for_context(
                    results.get("results")
                )
        except Exception as e:
            _logger.warning(f"Error searching web: {str(e)}")

        return None

    def _build_system_prompt(
        self,
        module=None,
        model_name=None,
        res_id=None,
        view_type=None,
        knowledge_docs=None,
        anythingllm_context=None,
        web_search_context=None,
    ):
        """Build system prompt with all available context."""
        parts = [SYSTEM_PROMPT]

        context_parts = []
        if module:
            context_parts.append(f"- Módulo activo: {module}")
        if model_name:
            context_parts.append(f"- Modelo: {model_name}")
        if res_id:
            context_parts.append(f"- Registro: #{res_id}")
        if view_type:
            context_parts.append(f"- Tipo de vista: {view_type}")

        if context_parts:
            parts.append("\nContexto actual del usuario:")
            parts.extend(context_parts)

        if anythingllm_context:
            parts.append("\nDocumentación de Odoo relevante (desde AnythingLLM):")
            parts.append(anythingllm_context)

        if web_search_context:
            parts.append("\nResultados de búsqueda web:")
            parts.append(web_search_context)

        if knowledge_docs:
            parts.append("\nDocumentos adicionales de Knowledge:")
            for i, doc in enumerate(knowledge_docs[:5], 1):
                title = doc.get("name", "")
                content = doc.get("content", "")[:500]
                parts.append(f"\n--- Documento {i}: {title} ---")
                parts.append(content)

        return "\n".join(parts)

    def chat(self, message, history=None, context=None):
        """
        Chat with the LLM.
        
        Args:
            message: User message
            history: Chat history
            context: Context dict with module, model, etc.
            
        Returns:
            str: LLM response
        """
        if context is None:
            context = {}

        # Get context from external sources
        anythingllm_context = self._get_anythingllm_context(message)
        web_search_context = None
        if not anythingllm_context or len(anythingllm_context) < 100:
            web_search_context = self._get_web_search_context(message)

        # Build system prompt
        system_prompt = self._build_system_prompt(
            module=context.get("module"),
            model_name=context.get("model"),
            res_id=context.get("res_id"),
            view_type=context.get("view_type"),
            knowledge_docs=context.get("knowledge_docs"),
            anythingllm_context=anythingllm_context,
            web_search_context=web_search_context,
        )

        # Send to appropriate provider
        if self.provider == self.PROVIDER_GOOGLE:
            return self._chat_google(message, history, system_prompt)
        elif self.provider == self.PROVIDER_OPENROUTER:
            return self._chat_openrouter(message, history, system_prompt)

        raise ValueError(f"Unknown provider: {self.provider}")

    def _chat_google(self, message, history, system_prompt):
        """Chat using Google Gemini."""
        genai_model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt,
        )

        chat_history = []
        if history:
            for msg in history[-10:]:
                role = "model" if msg.get("role") == "assistant" else "user"
                chat_history.append({
                    "role": role,
                    "parts": [msg.get("content", "")],
                })

        chat = genai_model.start_chat(history=chat_history)
        response = chat.send_message(message)
        return response.text

    def _chat_openrouter(self, message, history, system_prompt):
        """Chat using OpenRouter."""
        # Format history for OpenRouter
        formatted_history = []
        if history:
            for msg in history[-10:]:
                role = msg.get("role", "user")
                if role == "model":
                    role = "assistant"
                formatted_history.append({
                    "role": role,
                    "content": msg.get("content", ""),
                })

        return self.openrouter_service.chat(
            message=message,
            history=formatted_history,
            system_prompt=system_prompt,
        )
