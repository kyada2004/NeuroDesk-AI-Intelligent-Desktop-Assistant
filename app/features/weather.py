import re
import requests
import time
from app.core.api_config import OPENWEATHER_API_KEY

# In-memory cache for weather data
weather_cache = {}
CACHE_TTL = 600  # 10 minutes

def get_current_location_city():
    """Get user's current city from IP API."""
    try:
        response = requests.get("http://ip-api.com/json", timeout=5)
        response.raise_for_status()
        data = response.json()
        city = data.get("city", "")
        country = data.get("country", "")
        return city, country
    except requests.RequestException:
        return "", ""


def fetch_weather(city: str, country: str = ""):
    """
    Fetch weather by city (and optional country).
    Uses OpenWeather API and a cache.
    """
    if not city:
        return "❌ City not provided."

    location = f"{city},{country}".lower() if country else city.lower()
    current_time = time.time()

    # Check cache first
    if location in weather_cache:
        cached_data, timestamp = weather_cache[location]
        if current_time - timestamp < CACHE_TTL:
            print(f"Returning cached weather for {location}")
            return cached_data

    url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={OPENWEATHER_API_KEY}&units=metric"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("cod") == 200:
            desc = data["weather"][0]["description"].capitalize()
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            wind = data["wind"]["speed"]

            city_name = data["name"]
            country_code = data["sys"]["country"]

            result = (
                f"🌤️ Weather in {city_name}, {country_code}:\n"
                f"- Condition: {desc}\n"
                f"- Temperature: {temp}°C (feels like {feels_like}°C)\n"
                f"- Humidity: {humidity}%\n"
                f"- Wind: {wind} m/s"
            )
            # Store in cache
            weather_cache[location] = (result, current_time)
            return result
        else:
            return f"❌ City '{location}' not found."
    except requests.RequestException as e:
        return f"⚠️ Weather error: {e}"


def handle_weather_query(query: str):
    """Process user query and return weather info."""
    q = query.lower().strip()

    # Case 1: "today weather" without city → use current location
    if re.search(r"\btoday weather\b", q) and "in" not in q:
        city, country = get_current_location_city()
        if not city:
            return "⚠️ Could not detect your current location."
        return fetch_weather(city, country)

    # Case 2: "weather in <city>" or "what's the weather in <city>"
    match = re.search(r"(?:weather\s+in|in)\s+([a-zA-Z\s]+)(?:,\s*([a-zA-Z\s]+))?", query, re.IGNORECASE)
    if match:
        city = match.group(1).strip()
        country = match.group(2).strip() if match.group(2) else ""
        return fetch_weather(city, country)

    # Case 3: "<city> weather" or "<city> today weather"
    match_city_first = re.search(r"([a-zA-Z\s]+)\s+(?:today\s+)?weather", query, re.IGNORECASE)
    if match_city_first:
        city = match_city_first.group(1).strip()
        return fetch_weather(city)

    return "⚠️ Please specify a valid weather query (e.g., 'today weather in London')."