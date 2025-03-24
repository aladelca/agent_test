import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# API Keys and Tokens
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION')
S3_BUCKET = os.getenv('S3_BUCKET_NAME')

# Configuration validation
if not all([OPENAI_API_KEY, TELEGRAM_BOT_TOKEN]):
    logger.error("API keys are not configured. Please set up OPENAI_API_KEY and TELEGRAM_BOT_TOKEN in environment variables.")
    raise ValueError("API keys are not configured")

# Configure OpenAI API key
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# LLM Configuration
LLM_MODEL = "gpt-3.5-turbo"
LLM_TEMPERATURE = 0

# Database configuration
DB_FILE = "course_state.json"  # For migration
