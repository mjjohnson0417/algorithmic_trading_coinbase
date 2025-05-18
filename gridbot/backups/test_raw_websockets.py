# Save as test_raw_websocket.py
import asyncio
import websockets
import logging

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

async def test_ws():
    uri = "wss://stream.binance.us:9443/ws/hbarusdt@kline_15m"
    try:
        async with websockets.connect(uri) as ws:
            logging.info("Connected to WebSocket")
            async for message in ws:
                logging.info(f"Received: {message}")
    except Exception as e:
        logging.error(f"Error: {e}")

asyncio.run(test_ws())