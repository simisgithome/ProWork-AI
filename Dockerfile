FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ADK web UI – Cloud Run requires 0.0.0.0 and PORT env var
CMD ["sh", "-c", "exec adk web --host 0.0.0.0 --port ${PORT:-8080} ."]
