FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY crawler/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY scraper.py .
COPY crawler/ ./crawler/
COPY backend/formula_engine.py ./backend/

# Create __init__.py for backend module
RUN mkdir -p /app/backend && touch /app/backend/__init__.py

# Create logs directory
RUN mkdir -p /app/logs

# Run crawler
CMD ["python", "crawler/main.py"]
