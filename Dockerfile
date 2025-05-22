FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      gcc \
      libssl-dev \
      libjpeg-dev \
      zlib1g-dev \
      git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --default-timeout=100 \
                --retries=10 \
                --no-cache-dir \
                -r requirements.txt

# Copy project
COPY . .

# Prepare media & static, collect static files
RUN mkdir -p /app/media && \
    python manage.py collectstatic --noinput

EXPOSE 8000

# Launch Daphne
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "live_broadcast.asgi:application"]
