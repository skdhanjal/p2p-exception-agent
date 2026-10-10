FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY common ./common
COPY servers ./servers

RUN useradd --create-home appuser

USER appuser

CMD ["sh", "-c", "python -m servers.${SERVER:?SERVER must be set}"]
