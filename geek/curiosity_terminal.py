"""Explore live Wikimedia encyclopedia data from a terminal."""

import argparse
import html
import json
import re
import socket
import urllib.error
import urllib.parse
import urllib.request


class CuriosityError(Exception):
    """A recoverable encyclopedia request error."""


def request_json(url, timeout):
    request = urllib.request.Request(url, headers={"User-Agent": "curiosity-terminal/1.0 (https://github.com/MIATSUNO/MIATSUNO-Lab)"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        raise CuriosityError(f"Wikimedia returned HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, socket.timeout, json.JSONDecodeError) as exc:
        raise CuriosityError(f"could not retrieve Wikimedia data: {exc}") from exc
    if not isinstance(payload, dict):
        raise CuriosityError("Wikimedia returned an unexpected response")
    return payload


def language_base(language):
    if not re.fullmatch(r"[a-z]{2,12}", language):
        raise CuriosityError("language must contain only lowercase letters")
    return f"https://{language}.wikipedia.org"


def random_article(language, timeout):
    base = language_base(language)
    url = f"{base}/api/rest_v1/page/random/summary"
    payload = request_json(url, timeout)
    required = ("title", "extract", "content_urls")
    if not all(key in payload for key in required):
        raise CuriosityError("Wikimedia random response lacked article fields")
    desktop = payload["content_urls"].get("desktop", {})
    return {
        "kind": "random",
        "language": language,
        "title": payload["title"],
        "description": payload.get("description"),
        "extract": payload["extract"],
        "url": desktop.get("page"),
        "source_url": url,
    }


def strip_markup(value):
    return re.sub(r"<[^>]+>", "", html.unescape(value or ""))


def search_articles(language, query, limit, timeout):
    base = language_base(language)
    params = urllib.parse.urlencode(
        {"action": "query", "list": "search", "srsearch": query, "format": "json", "utf8": 1, "srlimit": limit}
    )
    url = f"{base}/w/api.php?{params}"
    payload = request_json(url, timeout)
    try:
        items = payload["query"]["search"]
    except (KeyError, TypeError) as exc:
        raise CuriosityError("Wikimedia search response lacked results") from exc
    results = []
    for item in items:
        title = item.get("title")
        if not isinstance(title, str):
            continue
        results.append(
            {
                "title": title,
                "page_id": item.get("pageid"),
                "snippet": strip_markup(item.get("snippet")),
                "url": f"{base}/wiki/{urllib.parse.quote(title.replace(' ', '_'))}",
            }
        )
    return {"kind": "search", "language": language, "query": query, "results": results, "source_url": url}


def print_random(result):
    print(result["title"])
    if result.get("description"):
        print(result["description"])
    print(result["extract"])
    if result.get("url"):
        print(result["url"])


def print_search(result):
    print(f"{len(result['results'])} result(s) for {result['query']!r}")
    for number, item in enumerate(result["results"], 1):
        print(f"{number}. {item['title']}")
        if item["snippet"]:
            print(f"   {item['snippet']}")
        print(f"   {item['url']}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read random articles or search results from a live Wikimedia Wikipedia API.")
    parser.add_argument("--language", default="en", help="Wikipedia language subdomain, such as en or pt.")
    parser.add_argument("--timeout", type=float, default=12.0, help="HTTP timeout in seconds.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("random", help="Fetch a random article summary.")
    search = commands.add_parser("search", help="Search encyclopedia titles and snippets.")
    search.add_argument("query", nargs="+")
    search.add_argument("--limit", type=int, default=5)
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    if args.command == "search" and not 1 <= args.limit <= 50:
        parser.error("--limit must be between 1 and 50")
    try:
        if args.command == "random":
            result = random_article(args.language, args.timeout)
        else:
            result = search_articles(args.language, " ".join(args.query), args.limit, args.timeout)
    except CuriosityError as exc:
        parser.exit(1, f"curiosity-terminal: {exc}\n")
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    elif args.command == "random":
        print_random(result)
    else:
        print_search(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

