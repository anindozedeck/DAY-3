"""Fetch and display a city's live weather and save the combined data as JSON.

Run with a city name:
    python day3_exercise.py "Nairobi"

Or run without a city to be prompted:
    python day3_exercise.py

Choose a different JSON output file with:
    python day3_exercise.py "Nairobi" --output nairobi_weather.json

This tool uses the Open-Meteo geocoding and forecast APIs and needs no API key
or third-party Python packages.
"""

import argparse
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


def fetch_json(url):
    """Fetch and decode a JSON API response."""
    try:
        with urlopen(url, timeout=15) as response:
            return json.load(response)
    except HTTPError as error:
        raise RuntimeError(
            f"The weather service returned HTTP {error.code}."
        ) from error
    except (URLError, TimeoutError) as error:
        raise RuntimeError(
            "Could not reach the weather service. Check your internet "
            "connection and try again."
        ) from error
    except json.JSONDecodeError as error:
        raise RuntimeError("The weather service returned invalid data.") from error


def get_weather_for_city(city):
    """Look up a city, then fetch and combine its current weather."""
    geocoding_url = "https://geocoding-api.open-meteo.com/v1/search?" + urlencode(
        {"name": city, "count": 1, "language": "en", "format": "json"}
    )
    locations = fetch_json(geocoding_url)
    results = locations.get("results", [])
    if not results:
        raise ValueError(
            f"Couldn't find '{city}'. Check the spelling and try again."
        )

    location = results[0]
    latitude = location["latitude"]
    longitude = location["longitude"]
    weather_url = "https://api.open-meteo.com/v1/forecast?" + urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,relative_humidity_2m,apparent_temperature,"
                "precipitation,weather_code,wind_speed_10m"
            ),
            "timezone": "auto",
        }
    )
    forecast = fetch_json(weather_url)

    return {
        "location": {
            "name": location["name"],
            "admin1": location.get("admin1"),
            "country": location.get("country"),
            "latitude": latitude,
            "longitude": longitude,
        },
        "current_weather": forecast["current"],
        "units": forecast["current_units"],
    }


def describe_weather_code(code):
    """Return a readable description for an Open-Meteo weather code."""
    descriptions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Freezing fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    return descriptions.get(code, f"Weather code {code}")


def display_weather(data):
    """Print the combined weather report in a friendly format."""
    location = data["location"]
    current = data["current_weather"]
    units = data["units"]
    place = ", ".join(
        part
        for part in (
            location["name"],
            location.get("admin1"),
            location.get("country"),
        )
        if part
    )
    print(f"\nCurrent weather for {place}")
    print("-" * (20 + len(place)))
    print(
        f"Conditions:  "
        f"{describe_weather_code(current['weather_code'])}"
    )
    print(
        f"Temperature: {current['temperature_2m']}"
        f"{units['temperature_2m']}"
    )
    print(
        f"Feels like:  {current['apparent_temperature']}"
        f"{units['apparent_temperature']}"
    )
    print(
        f"Humidity:    {current['relative_humidity_2m']}"
        f"{units['relative_humidity_2m']}"
    )
    print(
        f"Wind:        {current['wind_speed_10m']}"
        f"{units['wind_speed_10m']}"
    )
    print(
        f"Precipitation: {current['precipitation']}"
        f"{units['precipitation']}"
    )
    print(f"As of:       {current['time']}")


def main():
    parser = argparse.ArgumentParser(
        description="Look up a city's current weather and save it as JSON."
    )
    parser.add_argument(
        "city",
        nargs="?",
        help="city to look up (if omitted, you will be prompted)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="weather_report.json",
        help="JSON output filename (default: weather_report.json)",
    )
    args = parser.parse_args()

    city = args.city
    if city is None:
        try:
            city = input("Which city would you like the weather for? ").strip()
        except EOFError:
            print("No city was provided.", file=sys.stderr)
            return 1
    if not city:
        print("Please enter a city name.", file=sys.stderr)
        return 1

    try:
        data = get_weather_for_city(city)
    except (RuntimeError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    except (KeyError, IndexError, TypeError) as error:
        print(
            "The weather service returned data in an unexpected format.",
            file=sys.stderr,
        )
        return 1

    try:
        output_path = Path(args.output)
        with output_path.open("w", encoding="utf-8") as output_file:
            json.dump(data, output_file, indent=2, ensure_ascii=False)
            output_file.write("\n")
    except OSError as error:
        print(f"Couldn't save the JSON file: {error}", file=sys.stderr)
        return 1

    display_weather(data)
    print(f"\nA copy of this report was saved to {output_path}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
