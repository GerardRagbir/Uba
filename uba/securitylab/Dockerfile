# The recipe for the security lab image.
#
# Note: this is deliberately a SEPARATE image from the real backend. It shares
# no code, no database and no secrets with the rest of the system. That
# isolation is intentional - a vulnerable service must not be able to reach
# anything valuable.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Run as a non-root user even here: good habit, and if a student does find
# remote code execution, it lands them in an unprivileged account.
RUN useradd --create-home --uid 1000 lab
USER lab

EXPOSE 8100

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8100/healthz')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]
