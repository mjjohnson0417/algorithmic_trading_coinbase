import asyncio
import logging
from binance.websocket.spot.websocket_stream import SpotWebsocketStreamClient
from dotenv import load_dotenv
import os

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

async def main():
    def handle_message(client, msg):
        logging.info(f"Received: {msg}")

    load_dotenv("/home/jason/api/binance/binance_us.env")
    try:
        ws_client = SpotWebsocketStreamClient(
            stream_url="wss://stream.binance.us:9443",
            on_message=handle_message,
            on_error=lambda e: logging.error(f"Error: {e}"),
            on_close=lambda: logging.info("Connection closed")
        )
        logging.info("Starting kline stream for HBARUSDT")
        ws_client.kline(symbol="hbarusdt", interval="15m")
        await asyncio.sleep(30)
        logging.info("Stopping client")
        ws_client.stop()
    except Exception as e:
        logging.error(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(main())