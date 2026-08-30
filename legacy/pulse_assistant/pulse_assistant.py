#!/usr/bin/env python3
import argparse
import json
import sys
import urllib.parse
import urllib.request


def fetch_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": "MIATSUNO-Lab/pulse-assistant"})
    with urllib.request.urlopen(request, timeout=12) as response:
        return json.load(response)


def geocode(place):
    query = urllib.parse.urlencode({"name": place, "count": 1, "language": "en", "format": "json"})
    data = fetch_json("https://geocoding-api.open-meteo.com/v1/search?" + query)
    results = data.get("results") or []
    if not results:
        raise RuntimeError("No location matched that name")
    return results[0]


def weather(place):
    location = geocode(place)
    query = urllib.parse.urlencode({
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m",
        "timezone": "auto",
    })
    data = fetch_json("https://api.open-meteo.com/v1/forecast?" + query)
    current = data["current"]
    units = data["current_units"]
    label = ", ".join(value for value in [location.get("name"), location.get("admin1"), location.get("country")] if value)
    print(label)
    print("Observed at:", current["time"], "(" + data.get("timezone", "local time") + ")")
    print("Temperature:", current["temperature_2m"], units["temperature_2m"])
    print("Feels like:", current["apparent_temperature"], units["apparent_temperature"])
    print("Humidity:", current["relative_humidity_2m"], units["relative_humidity_2m"])
    print("Wind:", current["wind_speed_10m"], units["wind_speed_10m"])


def define(term):
    encoded = urllib.parse.quote(term.strip())
    data = fetch_json("https://api.dictionaryapi.dev/api/v2/entries/en/" + encoded)
    entry = data[0]
    print(entry.get("word", term))
    for meaning in entry.get("meanings", []):
        part = meaning.get("partOfSpeech", "")
        for item in meaning.get("definitions", [])[:3]:
            text = item.get("definition", "")
            print("-", (part + ": " if part else "") + text)
            example = item.get("example")
            if example:
                print("  Example:", example)


def build_parser():
    parser = argparse.ArgumentParser(description="A small local assistant backed by public web APIs.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    weather_parser = subparsers.add_parser("weather", help="show current weather for a place")
    weather_parser.add_argument("place", help="city, town, or region to look up")
    define_parser = subparsers.add_parser("define", help="look up an English dictionary entry")
    define_parser.add_argument("term", help="English word to define")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "weather":
            weather(args.place)
        else:
            define(args.term)
    except (urllib.error.URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError) as error:
        print("The public service could not provide a result:", error, file=sys.stderr)
        return 1
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

