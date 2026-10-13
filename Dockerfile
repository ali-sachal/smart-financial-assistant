FROM python:3.11-slim

# Install system dependencies for both Python and Node.js
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    libnss3 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    libxshmfence1 \
    libgtk-3-0 \
    libglib2.0-0 \
    libgobject-2.0-0 \
    fonts-liberation \
    ca-certificates \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (LTS version)
# RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
#     && apt-get install -y nodejs \
#     && npm install -g npm \
#     && npm install -g remotion

# Set working directory for Python app
WORKDIR /code

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install "uvicorn[standard]" gunicorn uvicorn-worker playwright \
    && playwright install chromium

# Copy project files to container
COPY . .

# Return to main working directory
WORKDIR /code

# Expose port 8000
EXPOSE 8000

# CMD to run the FastAPI app using Gunicorn with Uvicorn worker
CMD ["gunicorn", "-k", "uvicorn_worker.UvicornWorker", "-b", "0.0.0.0:8000", "--workers", "1", "--timeout", "300", "--graceful-timeout", "300", "--keep-alive", "75", "app.main:app"]