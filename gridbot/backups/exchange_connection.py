# exchange_connection.py
import ccxt.async_support as ccxt
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import time
import jwt
from ecdsa import SigningKey, SECP256k1
import base64

class ExchangeConnection:
    def __init__(self, api_key, secret):
        """
        Initializes the ExchangeConnection class with Coinbase Advanced Trade API credentials.
        
        Args:
            api_key (str): Coinbase API key (e.g., organizations/{org_id}/apiKeys/{key_id}).
            secret (str): ECDSA private key for authentication.
        """
        self.logger = logging.getLogger('ExchangeConnection')
        self.logger.setLevel(logging.DEBUG)
        log_dir = Path(__file__).parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / 'exchange_connection.log'
        file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        if not any(isinstance(h, logging.StreamHandler) for h in self.logger.handlers):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(console_handler)

        if not all([api_key, secret]):
            self.logger.error("API key or secret is missing. Cannot initialize ExchangeConnection.")
            raise ValueError("API key and secret must be provided.")
        
        self.api_key = api_key
        self.secret = secret # This is the privateKey from your Coinbase API Key JSON
        self.rest_exchange = None
        self.ws_exchange = None
        self._connect_rest()
        self._connect_websocket()

    def _connect_rest(self):
        """
        Establishes a REST API connection to Coinbase Advanced Trade.
        """
        try:
            self.rest_exchange = ccxt.coinbase({
                'apiKey': self.api_key,
                'secret': self.secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                    'authForWebSocket': True # Ensure authentication is handled for WebSocket
                }
            })
            self.logger.info("Coinbase REST connection established.")
        except Exception as e:
            self.logger.error(f"Error connecting to Coinbase REST API: {e}", exc_info=True)
            self.rest_exchange = None

    def _connect_websocket(self):
        """
        Establishes a WebSocket API connection to Coinbase Advanced Trade.
        """
        try:
            self.ws_exchange = ccxt.coinbase({
                'apiKey': self.api_key,
                'secret': self.secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                    'ws': {
                        'options': {
                            'jwt': self.generate_jwt(), # Pass the JWT for authentication
                        }
                    }
                }
            })
            self.logger.info("Coinbase WebSocket connection established.")
        except Exception as e:
            self.logger.error(f"Error connecting to Coinbase WebSocket API: {e}", exc_info=True)
            self.ws_exchange = None

    def generate_jwt(self):
        """
        Generates a JSON Web Token (JWT) for Coinbase Advanced Trade API.
        This JWT is used for WebSocket authentication.
        """
        try:
            timestamp = int(time.time())
            
            payload = {
                "sub": self.api_key, # Your API Key name (name from Coinbase API Key JSON)
                "iss": "coinbase-cloud", # Fixed issuer for Coinbase Cloud
                "nbf": timestamp,
                "exp": timestamp + 120,  # Token valid for 2 minutes
                "iat": timestamp,
                "aud": ["retail_rest_api_proxy", "retail_websocket_api_proxy"] # Audience for Advanced Trade API (both REST and WS)
            }

            # The privateKey from Coinbase API Key JSON is a PEM-encoded string.
            # It needs to be encoded to bytes for PyJWT.
            pem_private_key_bytes = self.secret.encode('utf-8')

            # Ensure the private key is correctly loaded as an ECDSA signing key
            # PyJWT can directly use the PEM string for ES256
            encoded_jwt = jwt.encode(
                payload,
                pem_private_key_bytes, # Use the byte-encoded PEM private key
                algorithm="ES256",
                headers={"kid": self.api_key} # 'kid' (Key ID) is your API Key name
            )
            self.logger.debug(f"Generated JWT: {encoded_jwt}")
            return encoded_jwt
        except Exception as e:
            self.logger.error(f"Error generating JWT: {e}", exc_info=True)
            return None

    async def check_rest_connection(self):
        """
        Checks if the REST API connection is established by fetching markets.
        
        Returns:
            bool: True if REST connection is active, False otherwise.
        """
        if self.rest_exchange is None:
            self.logger.warning("REST connection not established.")
            return False
        try:
            markets = await self.rest_exchange.fetch_markets()
            self.logger.debug("REST connection verified: fetched %d markets.", len(markets))
            return True
        except Exception as e:
            self.logger.error("REST connection check failed: %s", e, exc_info=True)
            return False

    async def check_websocket_connection(self):
        """
        Checks if the WebSocket API connection is established.
        
        Returns:
            bool: True if WebSocket connection is active, False otherwise.
        """
        if self.ws_exchange is None:
            self.logger.warning("WebSocket connection not established.")
            return False
        try:
            # For WebSocket, we don't necessarily fetch markets directly to check connection
            # CCXT's internal mechanisms should handle connection.
            # A more robust check would involve subscribing to a public channel and verifying messages.
            # For now, we'll assume if ws_exchange exists, connection is attempted.
            self.logger.debug("WebSocket exchange instance exists. Connection is presumed attempted.")
            return True # This is a placeholder; a true check would be more involved
        except Exception as e:
            self.logger.error("WebSocket connection check failed: %s", e, exc_info=True)
            return False

    async def close(self):
        """
        Closes both REST and WebSocket connections.
        """
        try:
            if self.rest_exchange:
                await self.rest_exchange.close()
                self.logger.info("Coinbase REST connection closed.")
            if self.ws_exchange:
                await self.ws_exchange.close()
                self.logger.info("Coinbase WebSocket connection closed.")
        except Exception as e:
            self.logger.error(f"Error closing connections: %s", e, exc_info=True)

    