"""Fetch and record civil solar events from Open-Meteo."""

import argparse
import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path


API_URL = "https://api.open-meteo.com/v1/forecast"


class SolarError(Exception):
    """A recoverable solar data error."""


def validate_date(value):
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD") from exc


def validate_coordinate(value, name, lower, upper):
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{name} must be numeric") from exc
    if not lower <= number <= upper:
        raise argparse.ArgumentTypeError(f"{name} must be between {lower} and {upper}")
    return number


def fetch(latitude, longitude, day, timeout):
    params = urllib.parse.urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "sunrise,sunset,daylight_duration",
            "timezone": "auto",
            "start_date": day.isoformat(),
            "end_date": day.isoformat(),
        }
    )
    url = f"{API_URL}?{params}"
    request = urllib.request.Request(url, headers={"User-Agent": "solar-ledger/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        raise SolarError(f"Open-Meteo returned HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, socket.timeout, json.JSONDecodeError) as exc:
        raise SolarError(f"could not retrieve solar data: {exc}") from exc
    daily = payload.get("daily") if isinstance(payload, dict) else None
    if not isinstance(daily, dict) or not all(key in daily for key in ("sunrise", "sunset", "daylight_duration")):
        raise SolarError("Open-Meteo response did not contain the requested daily fields")
    try:
        sunrise = daily["sunrise"][0]
        sunset = daily["sunset"][0]
        daylight_seconds = float(daily["daylight_duration"][0])
    except (IndexError, KeyError, TypeError, ValueError) as exc:
        raise SolarError("Open-Meteo returned incomplete solar data") from exc
    return {
        "source": "Open-Meteo",
        "source_url": url,
        "latitude": latitude,
        "longitude": longitude,
        "date": day.isoformat(),
        "timezone": payload.get("timezone"),
        "sunrise": sunrise,
        "sunset": sunset,
        "daylight_seconds": daylight_seconds,
        "daylight_hours": round(daylight_seconds / 3600, 3),
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def save_record(path, record):
    destination = Path(path).expanduser()
    try:
        if destination.exists():
            with destination.open(encoding="utf-8") as stream:
                ledger = json.load(stream)
            if not isinstance(ledger, list):
                raise SolarError(f"ledger must contain a JSON list: {destination}")
        else:
            ledger = []
        ledger.append(record)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8") as stream:
            json.dump(ledger, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except (OSError, json.JSONDecodeError) as exc:
        raise SolarError(f"could not update ledger {destination}: {exc}") from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description="Record real sunrise, sunset, and daylight data for a coordinate.")
    parser.add_argument("--latitude", required=True, type=lambda value: validate_coordinate(value, "latitude", -90, 90))
    parser.add_argument("--longitude", required=True, type=lambda value: validate_coordinate(value, "longitude", -180, 180))
    parser.add_argument("--date", type=validate_date, default=datetime.now(timezone.utc).date(), help="Date in YYYY-MM-DD; defaults to today in UTC.")
    parser.add_argument("--timeout", type=float, default=12.0, help="HTTP timeout in seconds.")
    parser.add_argument("--save", type=Path, help="Append the result to a local JSON ledger.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)
    try:
        result = fetch(args.latitude, args.longitude, args.date, args.timeout)
        if args.save:
            save_record(args.save, result)
    except SolarError as exc:
        parser.exit(1, f"solar-ledger: {exc}\n")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"{result['date']} at {result['latitude']}, {result['longitude']} ({result['timezone']})")
        print(f"sunrise: {result['sunrise']}")
        print(f"sunset: {result['sunset']}")
        print(f"daylight: {result['daylight_hours']:.3f} hours")
        if args.save:
            print(f"saved to {args.save.expanduser()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

