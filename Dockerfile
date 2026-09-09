FROM python:3.11-slim

WORKDIR /app

# Install system utilities and build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Ensure data directories exist
RUN mkdir -p data/uploads data/processed outputs

# Expose ports: 8000 for FastAPI API, 8501 for Streamlit UI
EXPOSE 8000 8501

# Default command: launch Streamlit UI
CMD ["streamlit", "run", "app/ui.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
