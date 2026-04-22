import logging
import asyncio
import edge_tts

_logger = logging.getLogger(__name__)

VOICE_MAP = {
    "es": "es-ES-AlvaroNeural",
    "en": "en-US-GuyNeural",
    "fr": "fr-FR-DeniseNeural",
    "pt": "pt-BR-AntonioNeural",
    "de": "de-DE-ConradNeural",
    "it": "it-IT-DiegoNeural",
}

DEFAULT_VOICE = "es-ES-AlvaroNeural"


async def _generate_audio_async(text, voice):
    communicate = edge_tts.Communicate(text, voice)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data


def generate_speech(text, voice=None):
    if not voice:
        voice = DEFAULT_VOICE
    try:
        audio_data = asyncio.run(_generate_audio_async(text, voice))
        _logger.info("TTS generated %d bytes of audio", len(audio_data))
        return audio_data
    except Exception as e:
        _logger.error("TTS generation failed: %s", str(e))
        return None


def get_available_voices():
    try:
        voices = asyncio.run(edge_tts.list_voices())
        return [
            {"short_name": v["ShortName"], "locale": v["Locale"], "gender": v["Gender"]}
            for v in voices
        ]
    except Exception as e:
        _logger.error("Failed to list voices: %s", str(e))
        return []


def get_voice_for_lang(lang_code):
    return VOICE_MAP.get(lang_code, DEFAULT_VOICE)
