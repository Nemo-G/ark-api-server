FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies using uv
RUN uv sync --frozen

# Copy application code
COPY . .

# Set environment variables with defaults
ENV HTTP_FORWARD_GRPC_HOST=0.0.0.0
ENV HTTP_FORWARD_GRPC_PORT=62000

# Expose port
EXPOSE 80

# Default command using uv run
CMD ["uv", "run", "uvicorn", "openai_api_server:app", "--host", "0.0.0.0", "--port", "80", "--workers", "8"] 