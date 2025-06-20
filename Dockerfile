# Use a lightweight Python base image
FROM python:3.12-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Copy pyproject.toml and uv.lock for dependency installation
COPY pyproject.toml uv.lock ./

# Install uv and project dependencies
RUN pip install uv && uv sync

# Copy the rest of the application code
COPY . .

# Expose the port the application runs on
EXPOSE 8080

# Set the PORT environment variable
ENV PORT=8080

# Command to run the application
CMD ["uv", "run", "python", "main.py"]