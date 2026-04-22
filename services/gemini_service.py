import logging
import google.generativeai as genai

from odoo import _, api, models
from .anything_llm_service import AnythingLLMService
from .web_search_service import WebSearchService

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


def _build_system_prompt(
    module=None, 
    model_name=None, 
    res_id=None, 
    view_type=None, 
    knowledge_docs=None,
    anythingllm_context=None,
    web_search_context=None,
):
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


class GeminiService:
    def __init__(
        self, 
        api_key, 
        model_name="gemini-1.5-flash",
        anythingllm_url=None,
        anythingllm_key=None,
        anythingllm_workspace=None,
        enable_web_search=True,
    ):
        self.api_key = api_key
        self.model_name = model_name
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        
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

    def _get_web_search_context(self, message, confidence_threshold=0.3):
        """Get web search results if AnythingLLM didn't provide good results."""
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

    def chat(self, message, history=None, context=None):
        if context is None:
            context = {}

        # Get context from AnythingLLM
        anythingllm_context = self._get_anythingllm_context(message)
        
        # Get web search context if AnythingLLM didn't provide much
        web_search_context = None
        if not anythingllm_context or len(anythingllm_context) < 100:
            web_search_context = self._get_web_search_context(message)

        system_prompt = _build_system_prompt(
            module=context.get("module"),
            model_name=context.get("model"),
            res_id=context.get("res_id"),
            view_type=context.get("view_type"),
            knowledge_docs=context.get("knowledge_docs"),
            anythingllm_context=anythingllm_context,
            web_search_context=web_search_context,
        )

        genai_model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt,
        )

        chat_history = []
        if history:
            for msg in history[-10:]:
                role = "model" if msg.get("role") == "assistant" else "user"
                chat_history.append(
                    {
                        "role": role,
                        "parts": [msg.get("content", "")],
                    }
                )

        chat = genai_model.start_chat(history=chat_history)
        response = chat.send_message(message)

        return response.text
