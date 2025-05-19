
#### README for `key_loader.py`
```markdown
# Key Loader

## Overview
The `key_loader.py` module is responsible for loading Coinbase API keys from a JSON file, enabling secure authentication for the grid trading bot.

## Functionality
- **Key Loading**: Reads API key (`name`) and ECDSA private key (`privateKey`) from a specified JSON file.
- **Logging**: Logs key loading success or failure to `logs/key_loader.log` when enabled.
- **Error Handling**: Returns `False` if keys are missing or the file is invalid.

## Dependencies
- Python 3.8+
- Modules: `json`, `logging`, `pathlib`
- External Libraries: None

## Usage
```python
from key_loader import KeyLoader

key_loader = KeyLoader(key_file_path="/path/to/coinbase_keys.json", enable_logging=True)
if key_loader.load_keys():
    print(f"API Key: {key_loader.api_key}, Secret: {key_loader.secret}")
else:
    print("Failed to load keys")