# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.12-alpine

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install runtime dependencies
# libsodium and libffi are often needed by asyncssh/cryptography at runtime
RUN apk add --no-cache libsodium libffi

COPY requirements.txt .

# Install build dependencies, install pip packages, then remove build dependencies
# cryptography often needs rust/cargo to build on alpine if no wheel is available
RUN apk add --no-cache --virtual .build-deps \
    openssl-dev python3-dev gcc libc-dev cargo rust && \
    python -m pip install -r requirements.txt && \
    apk del .build-deps

WORKDIR /app
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["python", "-m", "unlock"]
