# Use official Python slim image for a smaller footprint.
# Slim keeps the image lean — no build tools or extras included.
FROM python:3.12-slim

# Set the working directory inside the container.
WORKDIR /app

# Copy and install dependencies first so Docker can cache this layer.
# If only source code changes, this layer won't be rebuilt.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source and config into the image.
COPY src/ ./src/
COPY config/ ./config/

# Expose the port uvicorn will listen on.
EXPOSE 8000

# Start the FastAPI app via uvicorn.
# Host 0.0.0.0 makes it reachable from outside the container.
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
