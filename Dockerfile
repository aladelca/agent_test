FROM python:3.9-slim

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ src/
COPY main.py .

# Set environment variables for Python unbuffered output
ENV PYTHONUNBUFFERED=1

# The following environment variables will be provided by ECS Task Definition:
# OPENAI_API_KEY
# TELEGRAM_BOT_TOKEN
# AWS_REGION
# AWS_ACCESS_KEY_ID
# AWS_SECRET_ACCESS_KEY
# S3_BUCKET_NAME

# Run the bot
CMD ["python", "main.py"] 