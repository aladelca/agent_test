FROM python:3.9-slim

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies and langchain-community
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir langchain-community

# Copy application code maintaining the src structure
COPY . .

# Set environment variables for Python unbuffered output
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# The following environment variables will be provided by ECS Task Definition:
# OPENAI_API_KEY
# TELEGRAM_BOT_TOKEN
# AWS_REGION
# AWS_ACCESS_KEY_ID
# AWS_SECRET_ACCESS_KEY
# S3_BUCKET_NAME

# Run the bot
CMD ["python", "run.py"] 