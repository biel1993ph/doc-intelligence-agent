FROM python:3.12-slim

# Install git (required by gitpython for repo cloning)
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for data persistence and temp cloning
RUN mkdir -p /app/data /tmp/doc-intelligence-agent

EXPOSE 8000

# Default: run the API server
CMD ["python", "-m", "app.main", "--api"]
