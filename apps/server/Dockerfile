FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml ./
COPY aidp ./aidp
RUN pip install --no-cache-dir .
COPY alembic.ini ./
COPY migrations ./migrations
CMD ["sh", "-c", "alembic upgrade head && uvicorn aidp.main:app --host 0.0.0.0 --port 8000"]
