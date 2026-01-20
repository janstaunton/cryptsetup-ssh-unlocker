# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.14-alpine

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install runtime dependencies
RUN apk add --no-cache libsodium libffi

WORKDIR /app

# Install dependencies first (caching)
COPY pyproject.toml uv.lock* ./
RUN uv pip install --system --no-cache-dir -r pyproject.toml || uv pip install --system --no-cache-dir .

# Copy application code
COPY . /app

# Install application
RUN uv pip install --system --no-deps .

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. 
# Ensure the app knows where to find the config.
CMD ["python", "-m", "unlock", "--config", "/app/config/config.ini"]
