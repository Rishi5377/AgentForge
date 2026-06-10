FROM python:3.11-slim

# Install system dependencies, Node.js 20, and Git (required for AgentForge Native Execution)
RUN apt-get update && apt-get install -y curl gnupg git && \
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && \
    chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get update && apt-get install -y nodejs gh && \
    npm install -g pnpm && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces require the container to run as a non-root user (UID 1000)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONPATH=/home/user/app/backend

# Set working directory to the user's home app directory
WORKDIR $HOME/app

# Install Python dependencies (run as user)
COPY --chown=user backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy the entire repo and give ownership to the user
COPY --chown=user . .

# Switch to the backend directory to run the server
WORKDIR $HOME/app/backend

# Expose the default Hugging Face port
EXPOSE 7860

# Run FastAPI via Uvicorn. Use sh -c to evaluate $PORT dynamically (defaulting to 7860)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-7860}"]
