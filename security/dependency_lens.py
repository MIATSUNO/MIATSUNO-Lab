import argparse
import json
import re
import sys
from pathlib import Path

import requests

TIMEOUT = 10
PACKAGE_PATTERN = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:(==|~=|>=|<=|!=|>|<)\s*([^;\s]+))?")


def parse_requirement(line):
    text = line.strip()
    if not text or text.startswith("#") or text.startswith("-"):
        return None
    match = PACKAGE_PATTERN.match(text)
    if not match:
        return None
    return {"name": match.group(1), "operator": match.group(2), "version": match.group(3)}


def read_requirements(path):
    requirements = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        item = parse_requirement(line)
        if item:
            requirements.append(item)
    return requirements


def package_metadata(name, timeout=TIMEOUT):
    endpoint = "https://pypi.org/pypi/" + requests.utils.quote(name, safe="") + "/json"
    try:
        response = requests.get(endpoint, timeout=timeout, headers={"User-Agent": "MIATSUNO-Lab-dependency-lens/1.0"})
        response.raise_for_status()
        payload = response.json()
        info = payload.get("info", {})
        return {"name": name, "ok": True, "latest": info.get("version"), "summary": info.get("summary"), "url": info.get("project_url") or info.get("home_page")}
    except (requests.RequestException, ValueError) as exc:
        return {"name": name, "ok": False, "error": str(exc)}


def vulnerability_metadata(requirements, timeout=TIMEOUT):
    queries = []
    for item in requirements:
        query = {"package": {"name": item["name"], "ecosystem": "PyPI"}}
        if item.get("version"):
            query["version"] = item["version"]
        queries.append(query)
    if not queries:
        return {"ok": True, "vulnerabilities": []}
    try:
        response = requests.post(
            "https://api.osv.dev/v1/querybatch",
            json={"queries": queries},
            timeout=timeout,
            headers={"User-Agent": "MIATSUNO-Lab-dependency-lens/1.0", "Accept": "application/json"},
        )
        response.raise_for_status()
        payload = response.json()
        findings = []
        for item, result in zip(requirements, payload.get("results", [])):
            for vulnerability in result.get("vulns", []):
                findings.append({"package": item["name"], "id": vulnerability.get("id"), "summary": vulnerability.get("summary"), "modified": vulnerability.get("modified")})
        return {"ok": True, "vulnerabilities": findings}
    except (requests.RequestException, ValueError) as exc:
        return {"ok": False, "error": str(exc), "vulnerabilities": []}


def analyze_requirements(path, include_vulnerabilities=False, timeout=TIMEOUT):
    requirements = read_requirements(path)
    metadata = [package_metadata(item["name"], timeout) for item in requirements]
    result = {"path": str(path), "requirements": requirements, "metadata": metadata}
    if include_vulnerabilities:
        result["osv"] = vulnerability_metadata(requirements, timeout)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Compare pinned Python requirements with PyPI and OSV metadata")
    parser.add_argument("path", help="requirements file")
    parser.add_argument("--osv", action="store_true", help="query the public OSV vulnerability database")
    parser.add_argument("--timeout", type=float, default=TIMEOUT)
    args = parser.parse_args(argv)
    try:
        result = analyze_requirements(args.path, args.osv, args.timeout)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if all(item.get("ok", False) for item in result["metadata"]) else 1


if __name__ == "__main__":
    sys.exit(main())

