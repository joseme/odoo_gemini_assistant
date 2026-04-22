import logging
import os
import json
import io
import wave
import struct

from vosk import Model, KaldiRecognizer

_logger = logging.getLogger(__name__)

_vosk_model = None
_vosk_model_path = None


def _load_vosk_model(model_path):
    global _vosk_model, _vosk_model_path
    if _vosk_model is not None and _vosk_model_path == model_path:
        return _vosk_model
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Vosk model not found at: {model_path}")
    _logger.info("Loading Vosk model from %s", model_path)
    _vosk_model = Model(model_path)
    _vosk_model_path = model_path
    _logger.info("Vosk model loaded successfully")
    return _vosk_model


def transcribe_audio(audio_bytes, sample_rate=16000, model_path=None):
    if model_path is None:
        model_path = os.environ.get("VOSK_MODEL_PATH", "vosk-model-small-es-0.22")

    model = _load_vosk_model(model_path)
    rec = KaldiRecognizer(model, sample_rate)

    audio_data = bytes(audio_bytes)
    if rec.AcceptWaveform(audio_data):
        result = json.loads(rec.Result())
    else:
        result = json.loads(rec.PartialResult())

    text = result.get("text", "").strip()
    if not text:
        final = json.loads(rec.FinalResult())
        text = final.get("text", "").strip()

    _logger.info("Vosk transcription: %s", text)
    return text
