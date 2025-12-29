FROM python:3.11.8-slim-bookworm as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ----------------------------------
FROM python:3.11.8-slim-bookworm as runtime

WORKDIR /app

# Copy only what's needed from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Use environment variables for runtime configuration
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
