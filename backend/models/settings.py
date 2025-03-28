import os
import logging

logger = logging.getLogger("visualize-it")


class Settings:
    """
    Settings class for application configuration.
    Loads configuration from environment variables with sensible defaults.
    """

    def __init__(self):
        self.DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "deepseek-coder-v2")
        self.OLLAMA_API_TIMEOUT = int(os.environ.get("OLLAMA_API_TIMEOUT", "60"))
        # Always default to localhost for local development
        self.OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
        # Remove the http:// prefix for the Ollama client
        # Make sure we don't have any trailing slashes or protocol prefixes
        self.OLLAMA_HOST = self.OLLAMA_API_URL.replace("http://", "").replace("https://", "").rstrip("/")
        logger.info(f"Ollama host set to: {self.OLLAMA_HOST}")

        # Logging settings
        self.LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
        self.SERVER_LOG_FILE = os.environ.get("SERVER_LOG_FILE", "backend.log")
        self.CLIENT_LOG_FILE = os.environ.get("CLIENT_LOG_FILE", "client.log")
        # API settings
        self.MAX_VISUALIZATIONS = int(os.environ.get("MAX_VISUALIZATIONS", "8"))
        logger.info(
            f"Settings initialized: DEFAULT_MODEL={self.DEFAULT_MODEL}, "
            f"OLLAMA_API_TIMEOUT={self.OLLAMA_API_TIMEOUT}, "
            f"OLLAMA_API_URL={self.OLLAMA_API_URL}, "
            f"OLLAMA_HOST={self.OLLAMA_HOST}"
        )


# Create a singleton instance
settings = Settings()
