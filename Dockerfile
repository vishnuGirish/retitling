# --- Use official Python image ---
FROM python:3.11-slim

# --- Set environment variables ---
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8501

# --- Set work directory ---
WORKDIR /app

# --- Copy requirements first for caching ---
COPY requirements.txt .

# --- Install system dependencies and Python dependencies ---
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# --- Copy app code ---
COPY . .

# --- Expose Streamlit default port ---
EXPOSE 8501

# --- Command to run the app ---
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
