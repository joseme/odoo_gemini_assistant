import logging
import base64

from odoo import http, _
from odoo.http import request
from odoo.exceptions import UserError

from ..services.llm_service import LLMService
from ..services.vosk_service import transcribe_audio
from ..services.tts_service import generate_speech, get_voice_for_lang

_logger = logging.getLogger(__name__)


class GeminiAssistantController(http.Controller):
    def _get_config(self):
        ICP = request.env["ir.config_parameter"].sudo()
        return {
            "provider": ICP.get_param("gemini_assistant.llm_provider", "google"),
            "enabled": ICP.get_param("gemini_assistant.llm_enabled", "False") == "True",
            # Google Gemini
            "gemini_api_key": ICP.get_param("gemini_assistant.gemini_api_key", ""),
            "gemini_model": ICP.get_param("gemini_assistant.gemini_model", "gemini-1.5-flash"),
            # OpenRouter
            "openrouter_api_key": ICP.get_param("gemini_assistant.openrouter_api_key", ""),
            "openrouter_model": ICP.get_param("gemini_assistant.openrouter_model", "openai/gpt-3.5-turbo"),
            # AnythingLLM
            "anythingllm_url": ICP.get_param("gemini_assistant.anythingllm_url", ""),
            "anythingllm_api_key": ICP.get_param("gemini_assistant.anythingllm_api_key", ""),
            "anythingllm_workspace": ICP.get_param("gemini_assistant.anythingllm_workspace", ""),
            "anythingllm_enabled": ICP.get_param("gemini_assistant.anythingllm_enabled", "True") == "True",
            # Web Search
            "web_search_enabled": ICP.get_param("gemini_assistant.web_search_enabled", "True") == "True",
            # Voice
            "vosk_model_path": ICP.get_param("gemini_assistant.vosk_model_path", ""),
            "tts_voice": ICP.get_param("gemini_assistant.tts_voice", ""),
        }

    def _get_llm_service(self, config):
        provider = config.get("provider", "google")
        
        # Get API key and model based on provider
        if provider == "google":
            api_key = config.get("gemini_api_key")
            model = config.get("gemini_model")
            if not api_key:
                raise UserError(_("API key de Google Gemini no configurada"))
        elif provider == "openrouter":
            api_key = config.get("openrouter_api_key")
            model = config.get("openrouter_model")
            if not api_key:
                raise UserError(_("API key de OpenRouter no configurada"))
        else:
            raise UserError(_("Proveedor de LLM no soportado: %s") % provider)
        
        # Setup AnythingLLM
        anythingllm_url = None
        anythingllm_key = None
        anythingllm_workspace = None
        
        if config["anythingllm_enabled"] and config["anythingllm_url"]:
            anythingllm_url = config["anythingllm_url"]
            anythingllm_key = config["anythingllm_api_key"]
            anythingllm_workspace = config["anythingllm_workspace"]
        
        return LLMService(
            provider=provider,
            api_key=api_key,
            model_name=model,
            anythingllm_url=anythingllm_url,
            anythingllm_key=anythingllm_key,
            anythingllm_workspace=anythingllm_workspace,
            enable_web_search=config["web_search_enabled"],
        )

    def _get_knowledge_docs(self, query):
        try:
            docs = request.env["knowledge.article"].search(
                [("name", "ilike", query)],
                limit=5,
            )
            return [{"name": d.name, "content": d.content} for d in docs if d.content]
        except Exception:
            return []

    @http.route("/gemini_assistant/config", type="json", auth="user", methods=["POST"])
    def get_config(self):
        config = self._get_config()
        provider = config["provider"]
        
        # Return appropriate model based on provider
        if provider == "google":
            model = config["gemini_model"]
        else:
            model = config["openrouter_model"]
        
        return {
            "enabled": config["enabled"],
            "provider": provider,
            "model": model,
            "tts_voice": config["tts_voice"],
        }

    @http.route("/gemini_assistant/chat", type="json", auth="user", methods=["POST"])
    def chat(self, message, history=None, context=None):
        config = self._get_config()
        if not config["enabled"]:
            return {"error": "El asistente no está habilitado"}

        if context is None:
            context = {}

        knowledge_docs = self._get_knowledge_docs(message)
        context["knowledge_docs"] = knowledge_docs

        try:
            llm = self._get_llm_service(config)
            response_text = llm.chat(
                message=message,
                history=history,
                context=context,
            )
            return {"response": response_text}
        except Exception as e:
            _logger.error("LLM chat error: %s", str(e))
            return {"error": str(e)}

    @http.route("/gemini_assistant/stt", type="json", auth="user", methods=["POST"])
    def speech_to_text(self, audio_data, sample_rate=16000):
        config = self._get_config()
        if not config["enabled"]:
            return {"error": "El asistente no está habilitado"}

        try:
            audio_bytes = base64.b64decode(audio_data)
            model_path = config["vosk_model_path"] or None
            text = transcribe_audio(
                audio_bytes, sample_rate=sample_rate, model_path=model_path
            )
            return {"text": text}
        except Exception as e:
            _logger.error("STT error: %s", str(e))
            return {"error": str(e)}

    @http.route("/gemini_assistant/tts", type="http", auth="user", methods=["POST"])
    def text_to_speech(self, text, lang="es", **kwargs):
        config = self._get_config()
        if not config["enabled"]:
            return request.make_response(b"", status=403)

        voice = config["tts_voice"] or get_voice_for_lang(lang)

        try:
            audio_data = generate_speech(text, voice=voice)
            if not audio_data:
                return request.make_response(b"", status=500)

            headers = [
                ("Content-Type", "audio/mpeg"),
                ("Content-Length", len(audio_data)),
                ("Content-Disposition", f'attachment; filename="speech.mp3"'),
            ]
            return request.make_response(audio_data, headers)
        except Exception as e:
            _logger.error("TTS error: %s", str(e))
            return request.make_response(b"", status=500)
