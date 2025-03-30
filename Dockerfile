FROM python:3.10-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt requirements.txt
COPY api/requirements.txt api-requirements.txt

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r api-requirements.txt

# Copy the Chroma database and application code
COPY chroma_db/ /app/chroma_db/
COPY api/ /app/api/

# Set environment variables
ENV PYTHONPATH=/app
ENV DB_PATH=/app/chroma_db
ENV API_KEY=change-me-in-production

# Expose port for API
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run the application
WORKDIR /app/api
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 