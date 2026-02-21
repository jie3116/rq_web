FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN addgroup --system app && adduser --system --ingroup app app && chown -R app:app /app

USER app

EXPOSE 8000

CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-", "--timeout", "60", "run:app"]
