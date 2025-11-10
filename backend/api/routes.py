from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
import sys
import uuid
import csv
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Call, Evaluation, SessionLocal, init_db
from services.transcription_service import transcribe_audio
from services.evaluation_service import evaluate_transcription

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    manager: Optional[str] = Form(None),
    call_date: Optional[str] = Form(None),
    call_identifier: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    uploaded_calls = []
    
    for file in files:
        if not file.content_type.startswith("audio/"):
            continue
        
        file_id = str(uuid.uuid4())
        filename = f"{file_id}_{file.filename}"
        file_path = f"uploads/{filename}"
        
        os.makedirs("uploads", exist_ok=True)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        call_date_obj = None
        if call_date:
            try:
                call_date_obj = datetime.fromisoformat(call_date.replace("Z", "+00:00"))
            except:
                pass
        
        call = Call(
            filename=file.filename,
            audio_url=file_path,
            manager=manager,
            call_date=call_date_obj,
            call_identifier=call_identifier
        )
        
        db.add(call)
        db.commit()
        db.refresh(call)
        
        uploaded_calls.append({
            "id": call.id,
            "filename": call.filename,
            "manager": call.manager,
            "call_date": call.call_date.isoformat() if call.call_date else None,
            "call_identifier": call.call_identifier
        })
    
    return {"calls": uploaded_calls}

@router.post("/analyze/{call_id}")
async def analyze_call(call_id: int, db: Session = Depends(get_db)):
    try:
        call = db.query(Call).filter(Call.id == call_id).first()
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        if not call.audio_url:
            raise HTTPException(status_code=400, detail="Audio file not found")
        
        audio_path = call.audio_url
        if not os.path.isabs(audio_path):
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            audio_path = os.path.join(backend_dir, audio_path)
        
        if not os.path.exists(audio_path):
            raise HTTPException(status_code=400, detail=f"Audio file not found at {audio_path}")
        
        transcription = transcribe_audio(audio_path)
        call.transcription = transcription
        db.commit()
        
        evaluation_result = evaluate_transcription(transcription)
        
        evaluation = Evaluation(
            call_id=call_id,
            scores=evaluation_result["scores"],
            итоговая_оценка=evaluation_result["итоговая_оценка"],
            нарушения=evaluation_result["нарушения"],
            комментарии=evaluation_result["комментарии"],
            is_retest=False
        )
        
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)
        
        return {
            "call_id": call_id,
            "transcription": transcription,
            "evaluation": {
                "id": evaluation.id,
                "scores": evaluation.scores,
                "итоговая_оценка": evaluation.итоговая_оценка,
                "нарушения": evaluation.нарушения,
                "комментарии": evaluation.комментарии
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error during analysis: {str(e)}")

@router.post("/analyze/{call_id}/retest")
async def retest_call(call_id: int, db: Session = Depends(get_db)):
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    if not call.transcription:
        raise HTTPException(status_code=400, detail="Transcription not found")
    
    evaluation_result = evaluate_transcription(call.transcription)
    
    evaluation = Evaluation(
        call_id=call_id,
        scores=evaluation_result["scores"],
        итоговая_оценка=evaluation_result["итоговая_оценка"],
        нарушения=evaluation_result["нарушения"],
        комментарии=evaluation_result["комментарии"],
        is_retest=True
    )
    
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    
    return {
        "call_id": call_id,
        "evaluation": {
            "id": evaluation.id,
            "scores": evaluation.scores,
            "итоговая_оценка": evaluation.итоговая_оценка,
            "нарушения": evaluation.нарушения,
            "комментарии": evaluation.комментарии,
            "is_retest": True
        }
    }

@router.get("/calls")
async def get_calls(
    manager: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Call)
    
    if manager:
        query = query.filter(Call.manager == manager)
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            query = query.filter(Call.call_date >= start_dt)
        except:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            query = query.filter(Call.call_date <= end_dt)
        except:
            pass
    
    calls = query.order_by(Call.created_at.desc()).all()
    
    result = []
    for call in calls:
        latest_evaluation = db.query(Evaluation).filter(
            Evaluation.call_id == call.id
        ).order_by(Evaluation.created_at.desc()).first()
        
        result.append({
            "id": call.id,
            "filename": call.filename,
            "manager": call.manager,
            "call_date": call.call_date.isoformat() if call.call_date else None,
            "call_identifier": call.call_identifier,
            "created_at": call.created_at.isoformat(),
            "evaluation": {
                "итоговая_оценка": latest_evaluation.итоговая_оценка if latest_evaluation else None,
                "нарушения": latest_evaluation.нарушения if latest_evaluation else False
            } if latest_evaluation else None
        })
    
    return {"calls": result}

@router.get("/calls/{call_id}")
async def get_call(call_id: int, db: Session = Depends(get_db)):
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    evaluations = db.query(Evaluation).filter(
        Evaluation.call_id == call_id
    ).order_by(Evaluation.created_at.desc()).all()
    
    return {
        "id": call.id,
        "filename": call.filename,
        "manager": call.manager,
        "call_date": call.call_date.isoformat() if call.call_date else None,
        "call_identifier": call.call_identifier,
        "transcription": call.transcription,
        "duration": call.duration,
        "created_at": call.created_at.isoformat(),
        "evaluations": [
            {
                "id": ev.id,
                "scores": ev.scores,
                "итоговая_оценка": ev.итоговая_оценка,
                "нарушения": ev.нарушения,
                "комментарии": ev.комментарии,
                "is_retest": ev.is_retest,
                "created_at": ev.created_at.isoformat()
            }
            for ev in evaluations
        ]
    }

@router.get("/export")
async def export_calls(
    manager: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Call)
    
    if manager:
        query = query.filter(Call.manager == manager)
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            query = query.filter(Call.call_date >= start_dt)
        except:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            query = query.filter(Call.call_date <= end_dt)
        except:
            pass
    
    calls = query.order_by(Call.created_at.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "Номер", "Дата звонка", "Дата оценки", "Месяц оценки", "Длительность звонка", "Менеджер",
        "Установление контакта", "", "Диагностика", "", "Продажа", "", "Презентация", "",
        "Работа с возражениями", "", "Завершение", "", "", "", "Итоговая оценка"
    ])
    
    writer.writerow([
        "", "", "", "", "", "",
        "1.1 Приветствие", "1.2 Наличие техники",
        "2.1 Выявление цели, боли", "2.2 Критерии обучения",
        "3.1 Запись на пробное", "3.2 Повторная связь",
        "4.1 Презентация формата", "4.2 Презентация до пробного",
        "5.1 Выявление возражений", "5.2 Отработка возражений",
        "6. Контрольные точки", "7. Корректность сделки", "8. Грамотность", "9. Нарушения",
        ""
    ])
    
    for idx, call in enumerate(calls, 1):
        latest_evaluation = db.query(Evaluation).filter(
            Evaluation.call_id == call.id
        ).order_by(Evaluation.created_at.desc()).first()
        
        if not latest_evaluation:
            continue
        
        scores = latest_evaluation.scores or {}
        evaluation_date = latest_evaluation.created_at
        month = evaluation_date.strftime("%Y-%m") if evaluation_date else ""
        
        violation_text = "FALSE"
        if latest_evaluation.нарушения:
            violation_text = "TRUE"
        elif scores.get("9", {}).get("violation", False):
            violation_text = "TRUE"
        
        row = [
            idx,
            call.call_date.strftime("%Y-%m-%d") if call.call_date else "",
            evaluation_date.strftime("%Y-%m-%d %H:%M:%S") if evaluation_date else "",
            month,
            call.duration or "",
            call.manager or "",
            scores.get("1.1", {}).get("score", ""),
            scores.get("1.2", {}).get("score", ""),
            scores.get("2.1", {}).get("score", ""),
            scores.get("2.2", {}).get("score", ""),
            scores.get("3.1", {}).get("score", ""),
            scores.get("3.2", {}).get("score", ""),
            scores.get("4.1", {}).get("score", ""),
            scores.get("4.2", {}).get("score", ""),
            scores.get("5.1", {}).get("score", ""),
            scores.get("5.2", {}).get("score", ""),
            scores.get("6", {}).get("score", ""),
            scores.get("7", {}).get("score", ""),
            scores.get("8", {}).get("score", ""),
            violation_text,
            latest_evaluation.итоговая_оценка or ""
        ]
        
        writer.writerow(row)
    
    output.seek(0)
    return FileResponse(
        path=None,
        media_type="text/csv",
        filename=f"calls_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        content=output.getvalue().encode("utf-8-sig")
    )

