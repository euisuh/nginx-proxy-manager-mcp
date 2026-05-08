FROM python:3.12-slim

WORKDIR /app

RUN groupadd -r npmcp && useradd -r -g npmcp npmcp

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

USER npmcp

CMD ["python", "server.py"]
