FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt \
    && groupadd --gid 10001 taxtrace \
    && useradd --uid 10001 --gid 10001 --no-create-home taxtrace \
    && mkdir -p /app/data/checkpoints /app/data/raw /app/runs \
    && chown -R 10001:10001 /app/data /app/runs
COPY taxtrace/*.py taxtrace/*.sql ./taxtrace/
COPY taxtrace/static/ ./taxtrace/static/
USER 10001:10001
EXPOSE 8015
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8015/health/live', timeout=3)"
CMD ["python", "-m", "uvicorn", "taxtrace.web:app", "--host", "0.0.0.0", "--port", "8015", "--workers", "1", "--no-proxy-headers", "--no-access-log"]
