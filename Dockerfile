FROM python:3.11-slim
WORKDIR /app

# Create a non-root user (best practice, consistent with adk output)
RUN adduser --disabled-password --gecos "" myuser

# Install Node.js and npm for MCP servers (requires root)
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

# Switch to the non-root user
USER myuser
ENV PATH="/home/myuser/.local/bin:$PATH"

# Install ADK and any other dependencies
RUN pip install google-adk==1.26.0

# Copy agent directory (adjust permissions for the non-root user)
COPY --chown=myuser:myuser postcards /app/agents/postcards

EXPOSE 8080

# Start the ADK web server
CMD adk web --port=8080 --host=0.0.0.0 --session_service_uri=memory:// --artifact_service_uri=memory:// "/app/agents"