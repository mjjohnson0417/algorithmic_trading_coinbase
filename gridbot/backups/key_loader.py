# key_loader.py
import json
import logging
from pathlib import Path

class KeyLoader:
    def __init__(self, key_file_path: str, enable_logging: bool = True):
        """
        Initialize KeyLoader to load Coinbase API keys.

        Args:
            key_file_path (str): Path to the JSON file containing API keys.
            enable_logging (bool): Enable logging if True.
        """
        self.key_file_path = key_file_path
        self.api_key = None
        self.secret = None
        self.logger = logging.getLogger('KeyLoader')
        if enable_logging:
            log_dir = Path(__file__).parent / 'logs'
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / 'key_loader.log'
            handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.WARNING)

    def load_keys(self) -> bool:
        """
        Load API key and secret from the JSON file.

        Returns:
            bool: True if keys are loaded successfully, False otherwise.
        """
        try:
            with open(self.key_file_path, 'r') as f:
                keys = json.load(f)
            self.api_key = keys.get('name')
            self.secret = keys.get('privateKey')  # ECDSA private key
            if not self.api_key or not self.secret:
                self.logger.error("API key or privateKey missing in %s", self.key_file_path)
                return False
            self.logger.debug("Successfully loaded API key and privateKey")
            return True
        except Exception as e:
            self.logger.error("Failed to load keys from %s: %s", self.key_file_path, e)
            return False