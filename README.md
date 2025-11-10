# AI Coach - Тулза для прослушки звонков

Онлайн-тулза для анализа звонков менеджеров по продажам.

## Архитектура

- **Фронтенд**: Next.js (TypeScript) на Vercel
- **Бэкенд**: Python FastAPI на Railway
- **База данных**: Supabase PostgreSQL
- **Расшифровка**: Whisper `base` модель
- **Оценка**: Google Gemini API

## Установка

### Бэкенд

```bash
cd backend
pip install -r requirements.txt
```

Создайте файл `backend/.env`:
```
DATABASE_URL=sqlite:///./ai_coach.db
GEMINI_API_KEY=your_gemini_api_key_here
HUGGINGFACE_TOKEN=your_huggingface_token_here
```

Для локальной разработки используется SQLite. Для продакшена настройте PostgreSQL.

Запуск:
```bash
uvicorn main:app --reload
```

### Фронтенд

```bash
cd frontend
npm install
```

Создайте файл `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Запуск:
```bash
npm run dev
```

## Использование

1. Загрузите аудио файлы через интерфейс
2. Укажите метаданные (менеджер, дата, ID звонка)
3. Запустите анализ - система расшифрует аудио и оценит по чек-листу
4. Просмотрите результаты и экспортируйте в CSV

## API Endpoints

- `POST /api/upload` - загрузка файлов
- `POST /api/analyze/{call_id}` - анализ звонка
- `POST /api/analyze/{call_id}/retest` - повторная проверка
- `GET /api/calls` - список звонков
- `GET /api/calls/{call_id}` - детали звонка
- `GET /api/export` - экспорт в CSV


