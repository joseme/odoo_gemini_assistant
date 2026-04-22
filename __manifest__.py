{
    "name": "Gemini AI Assistant",
    "version": "19.0.1.0.0",
    "category": "Productivity",
    "summary": "Asistente IA con Gemini 1.5 Flash, Vosk STT y edge-tts",
    "description": """
        Asistente de IA integrado en Odoo 17 que proporciona:
        - Chat flotante con Gemini 1.5 Flash
        - Reconocimiento de voz con Vosk (STT)
        - Respuesta hablada con edge-tts (voces de Microsoft Edge)
        - Contexto del módulo y registro actual
        - Integración con Odoo Knowledge
    """,
    "author": "Custom",
    "depends": ["web"],
    "data": [
        "security/ir.model.access.csv",
        "views/gemini_config_views.xml",
        "views/assets.xml",
    ],
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
