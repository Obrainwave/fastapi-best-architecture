FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN python -m pip install --upgrade pip

WORKDIR /app

COPY requirements/dev.txt .

RUN python -m pip install --no-cache-dir -r dev.txt

COPY . .

RUN chmod +x /app/migrations/docker-entrypoint.sh

ENTRYPOINT ["/app/migrations/docker-entrypoint.sh"]

EXPOSE 8880

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
