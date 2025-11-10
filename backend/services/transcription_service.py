import whisper
import os

_model = None

def load_model():
    global _model
    if _model is None:
        _model = whisper.load_model("base")
    return _model

def transcribe_audio(audio_path: str) -> str:
    model = load_model()
    result = model.transcribe(audio_path, language="ru")
    return result["text"]


