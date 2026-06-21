"""
Minimal example: push a message to Poke FROM the Pi.

This is the opposite direction from server.py -- here the Pi initiates
contact with Poke, rather than waiting to be called.

API key: set POKE_API_KEY in a .env file next to this script (copy
.env.example to .env and fill it in). It's loaded as an environment
variable below -- never hardcode the key directly in this file.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()  # reads .env in this directory

POKE_API_KEY = os.environ["POKE_API_KEY"]
POKE_INBOUND_URL = "https://poke.com/api/v1/inbound/api-message"


def push_to_poke(message: str) -> None:
    response = requests.post(
        POKE_INBOUND_URL,
        headers={
            "Authorization": f"Bearer {POKE_API_KEY}",
            "Content-Type": "application/json",
        },
        json={"message": message},
        timeout=10,
    )
    response.raise_for_status()


if __name__ == "__main__":
    push_to_poke("Test message from the Raspberry Pi.")