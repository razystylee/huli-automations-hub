"""
Configuration module for Huli Automations Hub - Mission Control

Loads environment variables from .env file and provides base configuration
for the FastAPI application and APScheduler.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


class Config:
    """Base configuration class"""

    # Application
    APP_NAME = "Huli Automations Hub - Mission Control"
    APP_VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # Server
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))

    # Timezone
    TIMEZONE = "America/Sao_Paulo"
    TZ = pytz.timezone(TIMEZONE)

    # Jobs configuration
    JOBS_CONFIG_PATH = os.getenv(
        "JOBS_CONFIG_PATH",
        str(Path(__file__).parent.parent.parent / "backend" / "config" / "jobs_config.json")
    )

    # Logs directory
    LOGS_DIR = os.getenv(
        "LOGS_DIR",
        str(Path(__file__).parent.parent.parent / "logs")
    )

    # Create logs directory if it doesn't exist
    Path(LOGS_DIR).mkdir(parents=True, exist_ok=True)

    # Scheduler
    SCHEDULER_ENABLED = os.getenv("SCHEDULER_ENABLED", "True").lower() == "true"

    # Credentials (from environment)
    HOTMART_CLIENT_ID = os.getenv("HOTMART_CLIENT_ID", "")
    HOTMART_CLIENT_SECRET = os.getenv("HOTMART_CLIENT_SECRET", "")
    HOTMART_BASIC_TOKEN = os.getenv("HOTMART_BASIC_TOKEN", "")
    FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
    FACEBOOK_SHEET_ID = os.getenv("FACEBOOK_SHEET_ID", "")
    GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s - %(message)s"

    # Execution
    DEFAULT_JOB_TIMEOUT = int(os.getenv("DEFAULT_JOB_TIMEOUT", 300))  # 5 minutes


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = "INFO"


def get_config() -> Config:
    """
    Get configuration based on environment.

    Returns:
        Config: Configuration instance
    """
    env = os.getenv("ENVIRONMENT", "development").lower()

    if env == "production":
        return ProductionConfig()

    return DevelopmentConfig()


# Default config instance
config = get_config()
