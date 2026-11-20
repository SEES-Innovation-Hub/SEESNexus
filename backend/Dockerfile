FROM python:3.12-slim

# Logs straight to stdout (Heroku and docker logs read it); no .pyc files.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as an unprivileged user, not root.
RUN useradd --create-home --uid 10001 app && chown -R app /app
USER app

EXPOSE 8000

# Heroku sets PORT and expects the app to listen on it; locally it defaults to
# 8000. WEB_CONCURRENCY worker processes (default 2). The shell expands the
# variables, then `exec` hands over to uvicorn so it receives Heroku's SIGTERM
# directly and shuts down cleanly instead of being killed after 30 seconds.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-2}"]
