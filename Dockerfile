# syntax=docker/dockerfile:1

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

RUN addgroup --system appgroup \
    && adduser \
        --system \
        --ingroup appgroup \
        --home /home/appuser \
        appuser

COPY requirements.txt requirements-devops.txt ./

RUN python -m pip install --upgrade pip \
    && pip install \
        --no-cache-dir \
        -r requirements.txt \
        -r requirements-devops.txt

COPY --chown=appuser:appgroup . .

RUN if [ -d "/app/scripts" ]; then \
        find /app/scripts \
            -type f \
            -name "*.sh" \
            -exec sed -i 's/\r$//' {} \; \
            -exec chmod +x {} \; ; \
    fi

USER appuser

EXPOSE 8000

CMD ["sh", "-c", "exec gunicorn \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${GUNICORN_WORKERS:-1} \
    --threads ${GUNICORN_THREADS:-8} \
    --timeout ${GUNICORN_TIMEOUT:-120} \
    --access-logfile - \
    --error-logfile - \
    app.index:app"]