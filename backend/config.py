import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ai_coach.db")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "tiny")
ENABLE_DIARIZATION = os.getenv("ENABLE_DIARIZATION", "false").lower() == "true"

