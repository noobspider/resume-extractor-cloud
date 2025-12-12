FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends     tesseract-ocr     poppler-utils     libgl1     build-essential     && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN mkdir -p uploads output

# Default command for web (Render will override for workers)
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "app:app", "--bind", "0.0.0.0:3000"]