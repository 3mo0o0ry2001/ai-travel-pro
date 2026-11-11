FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.lock ./
RUN python -m pip install --no-cache-dir -r requirements.lock \
    && groupadd --gid 10001 waypoint \
    && useradd --uid 10001 --gid waypoint --no-create-home waypoint \
    && mkdir /app/data && chown waypoint:waypoint /app/data
COPY --chown=waypoint:waypoint *.py ./
COPY --chown=waypoint:waypoint static ./static
COPY --chown=waypoint:waypoint scripts ./scripts
COPY --chown=waypoint:waypoint logging.json ./
USER waypoint
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD ["python", "scripts/container_health.py"]
CMD ["python", "-m", "uvicorn", "app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log", "--log-config", "logging.json", "--proxy-headers", "--forwarded-allow-ips", "*"]
