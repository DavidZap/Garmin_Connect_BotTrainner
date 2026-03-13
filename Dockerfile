FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts
COPY docs ./docs
COPY README.md .
COPY .env.example ./.env.example

EXPOSE 8000

CMD ["python", "scripts/run_api.py"]

