from langchain_core.tools import tool
import asyncio

@tool
async def get_weather(city: str) -> str:
    """Get the current weather for a city. Use this when the user asks about weather."""
    await asyncio.sleep(1.5)
    fake_data = {
        "paris": "18°C, partly cloudy",
        "tunis": "29°C, sunny",
        "new york": "22°C, light rain",
    }
    return fake_data.get(city.lower(), f"No data found for {city}")

@tool
async def calculate(expression: str) -> str:
    """Evaluate a basic math expression, e.g. '12 * (4 + 1)'. Use this for any arithmetic."""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"
TOOLS = [get_weather, calculate]
