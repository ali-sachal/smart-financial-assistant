FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY ai ./ai
COPY scripts ./scripts
COPY docs ./docs

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser \
    && mkdir -p /code/logs \
    && chown -R appuser:appgroup /code

USER appuser
EXPOSE 8000

CMD ["gunicorn", "-k", "uvicorn_worker.UvicornWorker", "-b", "0.0.0.0:8000", "--workers", "2", "--timeout", "120", "--access-logfile", "-", "app.main:app"]
