# Инструкция по деплою

## Шаг 1: Подготовка репозитория

1. Закоммитьте все изменения:
```bash
git add .
git commit -m "Initial commit"
```

2. Запушьте в GitHub:
```bash
git remote add origin https://github.com/dryagungleb14-wq/ai_coach2_dasha.git
git push -u origin main
```

## Шаг 2: Настройка Supabase

1. Создайте проект на https://supabase.com
2. Перейдите в Settings → Database
3. Скопируйте Connection String (URI format)
4. Сохраните для Railway

## Шаг 3: Деплой бэкенда на Railway

1. Зайдите на https://railway.app
2. New Project → Deploy from GitHub repo
3. Выберите репозиторий `ai_coach2_dasha`
4. Root Directory: `backend`
5. Добавьте переменные окружения:
   - `DATABASE_URL` - строка подключения из Supabase
   - `GEMINI_API_KEY` - ваш ключ Gemini API
   - `PORT` - Railway установит автоматически
6. Railway автоматически определит Python и установит зависимости
7. После деплоя скопируйте URL бэкенда (например: `https://your-app.railway.app`)

## Шаг 4: Деплой фронтенда на Vercel

1. Зайдите на https://vercel.com
2. New Project → Import Git Repository
3. Выберите репозиторий `ai_coach2_dasha`
4. Root Directory: `frontend`
5. Framework Preset: Next.js
6. Добавьте переменную окружения:
   - `NEXT_PUBLIC_API_URL` - URL вашего бэкенда на Railway (например: `https://your-app.railway.app`)
7. Deploy

## Шаг 5: Проверка

После деплоя:
1. Откройте URL фронтенда на Vercel
2. Попробуйте загрузить тестовый аудио файл
3. Проверьте, что анализ работает

## Важные замечания

- Railway бесплатно дает $5 кредитов в месяц
- Supabase бесплатный tier: 500MB базы данных
- Vercel бесплатный для хобби проектов
- Whisper модель `base` (~150MB) скачается автоматически при первом анализе на Railway

