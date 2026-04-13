FROM python:3.12-slim

WORKDIR /app

# Copy and install dependencies (layer cached by requirements.txt content hash)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "120", "--preload", "app:app"]
