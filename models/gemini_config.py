from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # LLM Provider Selection
    llm_provider = fields.Selection(
        [
            ("google", "Google Gemini"),
            ("openrouter", "OpenRouter (múltiples modelos)"),
        ],
        string="Proveedor de LLM",
        default="google",
    )
    llm_enabled = fields.Boolean(string="Asistente habilitado", default=False)

    # Google Gemini Configuration
    gemini_api_key = fields.Char(string="Gemini API Key")
    gemini_model = fields.Selection(
        [
            ("gemini-2.0-flash-exp", "Gemini 2.0 Flash Experimental (推荐)"),
            ("gemini-2.0-flash-lite", "Gemini 2.0 Flash Lite"),
            ("gemini-1.5-flash", "Gemini 1.5 Flash"),
            ("gemini-1.5-flash-8b", "Gemini 1.5 Flash 8B"),
            ("gemini-2.5-pro", "Gemini 2.5 Pro"),
        ],
        string="Modelo Gemini",
        default="gemini-2.0-flash-exp",
    )

    # OpenRouter Configuration
    openrouter_api_key = fields.Char(string="OpenRouter API Key")
    openrouter_model = fields.Selection(
        [
            ("openai/gpt-4-turbo", "GPT-4 Turbo"),
            ("openai/gpt-4", "GPT-4"),
            ("openai/gpt-3.5-turbo", "GPT-3.5 Turbo (economico)"),
            ("anthropic/claude-3-opus", "Claude 3 Opus"),
            ("anthropic/claude-3-sonnet", "Claude 3 Sonnet"),
            ("anthropic/claude-3-haiku", "Claude 3 Haiku (economico)"),
            ("google/gemini-pro", "Gemini Pro (via OpenRouter)"),
            ("mistralai/mistral-7b-instruct", "Mistral 7B (rapido)"),
        ],
        string="Modelo OpenRouter",
        default="openai/gpt-3.5-turbo",
    )

    # AnythingLLM Configuration
    anythingllm_url = fields.Char(
        string="URL de AnythingLLM",
        help="Base URL de tu instancia AnythingLLM (ej: http://info.knowhub.tech)",
    )
    anythingllm_api_key = fields.Char(
        string="API Key de AnythingLLM",
        help="Token de autenticación para AnythingLLM",
    )
    anythingllm_workspace = fields.Char(
        string="Workspace de AnythingLLM",
        help="Nombre del workspace especializado en Odoo (ej: Odoo17)",
    )
    anythingllm_enabled = fields.Boolean(
        string="Usar AnythingLLM para documentación",
        default=True,
    )

    # Web Search Configuration
    web_search_enabled = fields.Boolean(
        string="Habilitar búsqueda web",
        default=True,
        help="Buscar en internet cuando AnythingLLM no tiene respuesta",
    )

    # Voice Configuration
    vosk_model_path = fields.Char(string="Ruta del modelo Vosk")
    tts_voice = fields.Char(string="Voz TTS", default="es-ES-AlvaroNeural")

    @api.model
    def get_values(self):
        res = super().get_values()
        ICP = self.env["ir.config_parameter"].sudo()
        res.update(
            llm_provider=ICP.get_param("gemini_assistant.llm_provider", "google"),
            llm_enabled=ICP.get_param("gemini_assistant.llm_enabled", "False") == "True",
            gemini_api_key=ICP.get_param("gemini_assistant.gemini_api_key", ""),
            gemini_model=ICP.get_param("gemini_assistant.gemini_model", "gemini-1.5-flash"),
            openrouter_api_key=ICP.get_param("gemini_assistant.openrouter_api_key", ""),
            openrouter_model=ICP.get_param("gemini_assistant.openrouter_model", "openai/gpt-3.5-turbo"),
            anythingllm_url=ICP.get_param("gemini_assistant.anythingllm_url", ""),
            anythingllm_api_key=ICP.get_param("gemini_assistant.anythingllm_api_key", ""),
            anythingllm_workspace=ICP.get_param("gemini_assistant.anythingllm_workspace", ""),
            anythingllm_enabled=ICP.get_param("gemini_assistant.anythingllm_enabled", "True") == "True",
            web_search_enabled=ICP.get_param("gemini_assistant.web_search_enabled", "True") == "True",
            vosk_model_path=ICP.get_param("gemini_assistant.vosk_model_path", ""),
            tts_voice=ICP.get_param("gemini_assistant.tts_voice", "es-ES-AlvaroNeural"),
        )
        return res

    def set_values(self):
        super().set_values()
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("gemini_assistant.llm_provider", self.llm_provider or "google")
        ICP.set_param("gemini_assistant.llm_enabled", str(self.llm_enabled))
        ICP.set_param("gemini_assistant.gemini_api_key", self.gemini_api_key or "")
        ICP.set_param("gemini_assistant.gemini_model", self.gemini_model or "gemini-1.5-flash")
        ICP.set_param("gemini_assistant.openrouter_api_key", self.openrouter_api_key or "")
        ICP.set_param("gemini_assistant.openrouter_model", self.openrouter_model or "openai/gpt-3.5-turbo")
        ICP.set_param("gemini_assistant.anythingllm_url", self.anythingllm_url or "")
        ICP.set_param("gemini_assistant.anythingllm_api_key", self.anythingllm_api_key or "")
        ICP.set_param("gemini_assistant.anythingllm_workspace", self.anythingllm_workspace or "")
        ICP.set_param("gemini_assistant.anythingllm_enabled", str(self.anythingllm_enabled))
        ICP.set_param("gemini_assistant.web_search_enabled", str(self.web_search_enabled))
        ICP.set_param("gemini_assistant.vosk_model_path", self.vosk_model_path or "")
        ICP.set_param(
            "gemini_assistant.tts_voice", self.tts_voice or "es-ES-AlvaroNeural"
        )
