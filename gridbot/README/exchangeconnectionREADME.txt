
#### README for `exchange_connection.py`
```markdown
# Exchange Connection

## Overview
The `exchange_connection.py` module manages connections to the Coinbase Advanced Trade API, supporting both REST and WebSocket interfaces, and generates JWTs for authentication.

## Functionality
- **Connection Setup**: Initializes REST and WebSocket connections using `ccxt.async_support`.
- **JWT Generation**: Creates JSON Web Tokens for WebSocket authentication using ECDSA private keys.
- **Connection Verification**: Checks REST and WebSocket connection status.
- **Cleanup**: Closes connections gracefully.

## Dependencies
- Python 3.8+
- Modules: `asyncio`, `logging`, `pathlib`, `time`, `jwt`, `ecdsa`, `base64`
- External Libraries: `ccxt.async_support`, `pyjwt`, `ecdsa`

## Usage
```python
from exchange_connection import ExchangeConnection

exchange = ExchangeConnection(api_key="your_api_key", secret="your_private_key")
if await exchange.check_rest_connection():
    print("REST connection active")
jwt = exchange.generate_jwt()
await exchange.close()