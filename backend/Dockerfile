FROM python:3.11-slim

WORKDIR /app

# Копируем requirements.txt (build context уже в backend/)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip cache purge && \
    rm -rf /root/.cache/pip

# Копируем все файлы из текущей директории (backend/) в /app
COPY . .

EXPOSE 8000

# Используем переменную PORT из окружения (Railway установит её автоматически)
# Railway всегда устанавливает PORT, поэтому используем его напрямую
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
