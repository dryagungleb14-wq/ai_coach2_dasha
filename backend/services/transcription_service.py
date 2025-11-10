import whisper
import os
import logging
import subprocess
import tempfile
from dotenv import load_dotenv
from config import WHISPER_MODEL, ENABLE_DIARIZATION

load_dotenv()

logger = logging.getLogger(__name__)

_model = None

def load_model():
    global _model
    if _model is None:
        model_name = WHISPER_MODEL
        logger.info(f"Загрузка модели Whisper '{model_name}'...")
        _model = whisper.load_model(model_name)
        logger.info(f"Модель Whisper '{model_name}' загружена успешно")
    return _model

def compress_audio(audio_path: str) -> str:
    logger.info(f"Сжатие и конвертация аудио файла: {audio_path}")
    
    temp_dir = tempfile.gettempdir()
    output_path = os.path.join(temp_dir, f"compressed_{os.path.basename(audio_path)}.wav")
    
    try:
        cmd = [
            "ffmpeg",
            "-i", audio_path,
            "-ar", "16000",
            "-ac", "1",
            "-sample_fmt", "s16",
            "-y",
            output_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            logger.warning(f"Ошибка при сжатии аудио: {result.stderr}")
            logger.info("Используется оригинальный файл")
            return audio_path
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            original_size = os.path.getsize(audio_path)
            compressed_size = os.path.getsize(output_path)
            logger.info(f"Аудио сжато: {original_size} -> {compressed_size} байт ({compressed_size/original_size*100:.1f}%)")
            return output_path
        else:
            logger.warning("Сжатый файл не создан, используется оригинальный")
            return audio_path
            
    except subprocess.TimeoutExpired:
        logger.warning("Таймаут при сжатии аудио, используется оригинальный файл")
        return audio_path
    except Exception as e:
        logger.warning(f"Ошибка при сжатии аудио: {e}, используется оригинальный файл")
        return audio_path

def transcribe_audio(audio_path: str, enable_diarization: bool = None) -> str:
    if enable_diarization is None:
        enable_diarization = ENABLE_DIARIZATION
    
    logger.info(f"Начало транскрипции файла: {audio_path}")
    
    model = load_model()
    logger.info("Выполнение транскрипции Whisper...")
    
    compressed_path = compress_audio(audio_path)
    
    try:
        result = model.transcribe(
            compressed_path,
            language="ru",
            verbose=False,
            task="transcribe"
        )
        logger.info("Транскрипция Whisper завершена успешно")
    except Exception as e:
        logger.error(f"Ошибка при выполнении транскрипции Whisper: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
    
    if not enable_diarization:
        logger.info("Диарризация отключена, используется простая транскрипция")
        if "segments" in result and len(result["segments"]) > 0:
            transcription_parts = []
            for segment in result["segments"]:
                text = segment.get("text", "").strip()
                if text:
                    transcription_parts.append(text)
            return "\n".join(transcription_parts)
        return result["text"]
    
    hf_token = os.environ.get("HUGGINGFACE_TOKEN")
    
    if not hf_token or hf_token == "your_token_here":
        logger.warning("HUGGINGFACE_TOKEN не установлен, используется обычная транскрипция без диарризации")
        if "segments" in result and len(result["segments"]) > 0:
            transcription_parts = []
            for segment in result["segments"]:
                text = segment.get("text", "").strip()
                if text:
                    transcription_parts.append(text)
            return "\n".join(transcription_parts)
        return result["text"]
    
    try:
        from pyannote.audio import Pipeline
        import torch
        
        logger.info("Загрузка модели диарризации...")
        try:
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                token=hf_token
            )
        except TypeError:
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=hf_token
            )
        
        if torch.cuda.is_available():
            pipeline.to(torch.device("cuda"))
            logger.info("Используется CUDA для диарризации")
        else:
            logger.info("Используется CPU для диарризации")
        
        logger.info("Выполнение диарризации...")
        diarization = pipeline(compressed_path, min_speakers=2, max_speakers=2)
        
        segments = result.get("segments", [])
        logger.info(f"Найдено {len(segments)} сегментов транскрипции")
        
        diarization_turns = list(diarization.itertracks(yield_label=True))
        logger.info(f"Найдено {len(diarization_turns)} сегментов диарризации")
        
        if len(diarization_turns) == 0:
            logger.warning("Диарризация не нашла сегментов, используется обычная транскрипция")
            transcription_parts = []
            for segment in segments:
                text = segment.get("text", "").strip()
                if text:
                    transcription_parts.append(text)
            return "\n".join(transcription_parts)
        
        transcription_parts = []
        current_speaker = None
        
        for segment in segments:
            text = segment.get("text", "").strip()
            if not text:
                continue
            
            start_time = segment.get("start", 0)
            end_time = segment.get("end", 0)
            mid_time = (start_time + end_time) / 2
            
            speaker = None
            for turn, _, speaker_id in diarization_turns:
                if turn.start <= mid_time <= turn.end:
                    speaker = speaker_id
                    break
            
            if speaker is None:
                for turn, _, speaker_id in diarization_turns:
                    if turn.start <= start_time <= turn.end or turn.start <= end_time <= turn.end:
                        speaker = speaker_id
                        break
            
            if speaker is not None:
                if speaker != current_speaker:
                    if current_speaker is not None:
                        transcription_parts.append("")
                    speaker_label = "Менеджер" if "SPEAKER_00" in speaker or speaker.endswith("0") else "Клиент"
                    transcription_parts.append(f"{speaker_label}:")
                    current_speaker = speaker
                transcription_parts.append(text)
            else:
                if current_speaker is not None:
                    transcription_parts.append("")
                    current_speaker = None
                transcription_parts.append(text)
        
        logger.info(f"Диарризация завершена успешно, создано {len(transcription_parts)} частей транскрипции")
        return "\n".join(transcription_parts) if transcription_parts else result.get("text", "")
        
    except ImportError as e:
        logger.error(f"Библиотека pyannote.audio не установлена: {e}")
        if "segments" in result and len(result["segments"]) > 0:
            transcription_parts = []
            for segment in result["segments"]:
                text = segment.get("text", "").strip()
                if text:
                    transcription_parts.append(text)
            return "\n".join(transcription_parts)
        return result["text"]
    except Exception as e:
        logger.error(f"Ошибка при диарризации: {e}")
        import traceback
        logger.error(traceback.format_exc())
        logger.info("Используется обычная транскрипция без диарризации")
        if "segments" in result and len(result["segments"]) > 0:
            transcription_parts = []
            for segment in result["segments"]:
                text = segment.get("text", "").strip()
                if text:
                    transcription_parts.append(text)
            return "\n".join(transcription_parts)
        return result["text"]


