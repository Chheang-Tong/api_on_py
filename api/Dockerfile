# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# Install deps
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . /app

# Env
ENV FLASK_APP=wsgi.py FLASK_RUN_HOST=0.0.0.0 FLASK_ENV=production

EXPOSE 5000
CMD ["python", "-m", "flask", "run"]
