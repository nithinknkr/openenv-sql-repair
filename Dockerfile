FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies first (better layer caching)
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy all project files
COPY . .

# Verify SQLite is available (it's in Python stdlib — this should always pass)
RUN python -c "import sqlite3; print('SQLite version:', sqlite3.sqlite_version)"

# Expose HuggingFace Spaces default port
EXPOSE 7860

# Start FastAPI server
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
