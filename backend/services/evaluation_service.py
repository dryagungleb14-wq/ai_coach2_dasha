import google.generativeai as genai
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.checklist import get_checklist_prompt
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

def evaluate_transcription(transcription: str) -> dict:
    prompt = get_checklist_prompt()
    full_prompt = f"{prompt}\n\nРасшифровка звонка:\n\n{transcription}\n\nОцени звонок по чек-листу и верни JSON."
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(full_prompt)
    
    response_text = response.text.strip()
    
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()
    
    try:
        scores_data = json.loads(response_text)
    except json.JSONDecodeError:
        scores_data = {}
    
    violations = scores_data.get("9", {}).get("violation", False)
    
    total_score = 0
    if not violations:
        for key in ["1.1", "1.2", "2.1", "2.2", "3.1", "3.2", "4.1", "4.2", "5.1", "5.2", "6", "7", "8"]:
            score = scores_data.get(key, {}).get("score", 0)
            total_score += score
    else:
        total_score = 0
    
    comments = {}
    for key, value in scores_data.items():
        if isinstance(value, dict) and "comment" in value:
            comments[key] = value["comment"]
    
    return {
        "scores": scores_data,
        "итоговая_оценка": total_score,
        "нарушения": violations,
        "комментарии": json.dumps(comments, ensure_ascii=False)
    }

