"""
Minimal Poke <-> Raspberry Pi MCP server.

Two example tools:
- get_status()   retrieve example: Poke pulls data from the Pi
- set_led(state) action example:   Poke pushes a command to the Pi

No API key needed in this file -- the connection to Poke is authorized
through the one-time tunnel link, not a key in code (see "Commands to
run" below).

Run:
    python3 server.py
Then tunnel it (separate terminal):
    npx poke@latest tunnel http://localhost:3000/mcp -n "Pi Home Control" --recipe
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("raspberry-pi", port=3000)


@mcp.tool()
def get_status() -> str:
    """Retrieve a simple status string from the Pi."""
    return "Raspberry Pi is online and reachable."


@mcp.tool()
def set_led(state: str) -> str:
    """Turn an example LED on or off.

    Args:
        state: "on" or "off"
    """
    # Replace this with real GPIO code once you're ready, e.g.:
    #   from gpiozero import LED
    #   led = LED(17)
    #   led.on() if state == "on" else led.off()
    return f"LED set to {state} (placeholder -- wire up real GPIO here)"


if __name__ == "__main__":
    mcp.run(transport="streamable-http")