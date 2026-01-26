# Stage 1: Builder
FROM python:3.12-slim AS builder

# Install build dependencies
RUN pip install --no-cache-dir build==1.3.0

# Set the working directory
WORKDIR /app

# Copy the project files
COPY pyproject.toml .
COPY src/ ./src/
COPY README.md .
COPY LICENSE .

# Build the wheel
RUN python -m build --wheel --outdir /wheels

# Stage 2: Runtime
FROM python:3.12-slim AS runtime

# Install runtime dependencies (curl for downloading OPA)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install OPA
RUN curl -L -o /usr/local/bin/opa https://openpolicyagent.org/downloads/latest/opa_linux_amd64_static && \
    chmod 755 /usr/local/bin/opa

# Create a non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Set the working directory
WORKDIR /home/appuser/app

# Copy policies explicitly to /home/appuser/app/policies
COPY src/coreason_manifest/policies/ ./policies/

# Change ownership of app directory
RUN chown -R appuser:appuser /home/appuser/app

USER appuser

# Add user's local bin to PATH
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Copy the wheel from the builder stage
COPY --from=builder /wheels /wheels

# Install the application wheel
RUN pip install --no-cache-dir /wheels/*.whl

# Expose port
EXPOSE 8000

# Set environment variable for policy path
ENV POLICY_PATH=/home/appuser/app/policies/compliance.rego

# Command to run the server
CMD ["uvicorn", "coreason_manifest.server:app", "--host", "0.0.0.0", "--port", "8000"]
