# The recipe for the backend image.
FROM python:3.13-slim

# Do not write .pyc files, and print logs straight away instead of buffering.
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /srv

# Install dependencies first. Docker caches this layer, so a rebuild after a
# code change does not reinstall everything.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Do not run as root inside the container.
RUN useradd --create-home --uid 1000 uba
USER uba

EXPOSE 8000

# Docker marks the container healthy only when this succeeds.
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
