# svcdesk image, based on Dockerfile.example. Every dependency is installed at build time (no network at run
# time, API.md section 9); the service listens on 8080 and keeps its SQLite file on the /data named volume.
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src/ /app/src/
# The practice fixture, for the own-tests suite (src/tests) that runs from this same image.
COPY fixtures/ /app/fixtures/

RUN mkdir -p /data
ENV SVCDESK_DB=/data/svcdesk.db \
    PYTHONUNBUFFERED=1

EXPOSE 8080
CMD ["uvicorn", "svcdesk.main:app", "--app-dir", "/app/src", "--host", "0.0.0.0", "--port", "8080"]
