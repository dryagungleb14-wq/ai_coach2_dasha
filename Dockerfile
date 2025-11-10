FROM python:3.11-slim

WORKDIR /app

# Копируем requirements.txt из backend
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip cache purge && \
    rm -rf /root/.cache/pip

# Копируем всю папку backend одной командой
COPY backend/ .

EXPOSE 8000

CMD ["sh", "-c", "uvi["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8000"]

