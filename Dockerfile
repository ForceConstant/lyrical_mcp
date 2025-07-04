# Generated by https://smithery.ai. See: https://smithery.ai/docs/config#dockerfile
# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# Copy source
COPY . /app

# Install Python dependencies and the MCP server
RUN pip install --no-cache-dir .

RUN python -c "import nltk; nltk.download('cmudict'); nltk.download('punkt'); nltk.download('punkt_tab')"

# Use the console script entrypoint
CMD ["lyrical-mcp"]