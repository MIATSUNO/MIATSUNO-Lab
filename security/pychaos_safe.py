import argparse
import json
import math
import sys
from urllib.parse import urljoin, urlparse

import requests

TIMEOUT = 10
CHECK_NAMES = (
    "check_http_status",
    "check_security_headers",
    "check_tls_metadata",
    "check_redirects",
    "check_cookie_flags",
    "check_cors_policy",
    "check_content_type",
    "check_server_disclosure",
    "check_cache_policy",
    "check_referrer_policy",
    "check_content_security_policy",
    "check_strict_transport_security",
    "check_frame_options",
    "check_permissions_policy",
    "check_form_actions",
    "check_mixed_content",
    "check_robots_txt",
    "check_security_txt",
    "check_sitemap",
    "check_options",
    "check_json_document",
    "check_health_document",
    "check_openapi_document",
    "check_rate_limit_headers",
    "check_api_error_shape",
    "check_etag",
    "check_compression",
    "check_x_content_type_options",
    "check_cross_origin_embedder",
    "check_cross_origin_opener",
    "check_cross_origin_resource",
    "check_well_known",
    "check_manifest",
    "check_favicon",
    "check_html_links",
    "check_external_hosts",
    "check_password_forms",
    "check_sensitive_paths",
    "check_content_disposition",
    "check_http_only_session",
    "check_origin_reflection",
    "check_http_methods",
    "check_hsts_preload",
    "check_xss_protection",
    "check_vary_header",
)


def _validate_timeout(value):
    try:
        timeout = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("timeout must be a positive finite number") from exc
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be a positive finite number")
    return timeout


def _build_session():
    session = requests.Session()
    session.headers.update(
        {"User-Agent": "MIATSUNO-Lab-pychaos-safe/1.0", "Accept": "*/*"}
    )
    return session


def _normalize_url(value):
    if not isinstance(value, str):
        raise ValueError("URL must be a string")
    candidate = value.strip()
    if not candidate:
        raise ValueError("URL is empty")
    if "://" not in candidate:
        candidate = "https://" + candidate
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL must use HTTP or HTTPS and include a host")
    return candidate


def _fetch_url(url, path="", method="GET", headers=None, timeout=TIMEOUT):
    target = ""
    try:
        target = _normalize_url(url)
        _validate_timeout(timeout)
        if path:
            target = urljoin(target.rstrip("/") + "/", path.lstrip("/"))
        response = _build_session().request(
            method,
            target,
            headers=headers or {},
            timeout=timeout,
            allow_redirects=True,
        )
        return {
            "ok": True,
            "url": target,
            "final_url": response.url,
            "status": response.status_code,
            "headers": dict(response.headers),
            "body": response.text,
            "history": [item.status_code for item in response.history],
        }
    except (requests.RequestException, ValueError, TypeError) as exc:
        return {
            "ok": False,
            "url": target or str(url),
            "error": str(exc),
            "headers": {},
            "body": "",
            "history": [],
        }


def _probe(name, url, timeout):
    paths = {
        "check_robots_txt": "/robots.txt",
        "check_security_txt": "/.well-known/security.txt",
        "check_sitemap": "/sitemap.xml",
        "check_health_document": "/health",
        "check_openapi_document": "/openapi.json",
        "check_well_known": "/.well-known/",
        "check_manifest": "/manifest.json",
        "check_favicon": "/favicon.ico",
    }
    method = "OPTIONS" if name == "check_options" or name == "check_http_methods" else "GET"
    headers = {}
    if name in {"check_cors_policy", "check_origin_reflection"}:
        headers["Origin"] = "https://security.invalid"
    result = _fetch_url(url, paths.get(name, ""), method, headers, timeout)
    if not result["ok"]:
        return {"check": name, "ok": False, "error": result["error"], "details": {}}
    headers_lower = {key.lower(): value for key, value in result["headers"].items()}
    status = result["status"]
    final_url = result["final_url"]
    details = {
        "content_type": headers_lower.get("content-type", ""),
        "allow": headers_lower.get("allow", ""),
        "redirects": len(result["history"]),
        "https": final_url.startswith("https://"),
        "security_headers": sorted(
            set(headers_lower)
            & {
                "content-security-policy",
                "strict-transport-security",
                "x-content-type-options",
                "referrer-policy",
                "permissions-policy",
            }
        ),
        "set_cookie": bool(headers_lower.get("set-cookie")),
        "etag": headers_lower.get("etag", ""),
        "vary": headers_lower.get("vary", ""),
        "server": headers_lower.get("server", ""),
    }
    return {
        "check": name,
        "ok": 200 <= status < 400,
        "status": status,
        "final_url": final_url,
        "details": details,
    }


def check_http_status(url, timeout=TIMEOUT):
    return _probe("check_http_status", url, timeout)


def check_security_headers(url, timeout=TIMEOUT):
    return _probe("check_security_headers", url, timeout)


def check_tls_metadata(url, timeout=TIMEOUT):
    return _probe("check_tls_metadata", url, timeout)


def check_redirects(url, timeout=TIMEOUT):
    return _probe("check_redirects", url, timeout)


def check_cookie_flags(url, timeout=TIMEOUT):
    return _probe("check_cookie_flags", url, timeout)


def check_cors_policy(url, timeout=TIMEOUT):
    return _probe("check_cors_policy", url, timeout)


def check_content_type(url, timeout=TIMEOUT):
    return _probe("check_content_type", url, timeout)


def check_server_disclosure(url, timeout=TIMEOUT):
    return _probe("check_server_disclosure", url, timeout)


def check_cache_policy(url, timeout=TIMEOUT):
    return _probe("check_cache_policy", url, timeout)


def check_referrer_policy(url, timeout=TIMEOUT):
    return _probe("check_referrer_policy", url, timeout)


def check_content_security_policy(url, timeout=TIMEOUT):
    return _probe("check_content_security_policy", url, timeout)


def check_strict_transport_security(url, timeout=TIMEOUT):
    return _probe("check_strict_transport_security", url, timeout)


def check_frame_options(url, timeout=TIMEOUT):
    return _probe("check_frame_options", url, timeout)


def check_permissions_policy(url, timeout=TIMEOUT):
    return _probe("check_permissions_policy", url, timeout)


def check_form_actions(url, timeout=TIMEOUT):
    return _probe("check_form_actions", url, timeout)


def check_mixed_content(url, timeout=TIMEOUT):
    return _probe("check_mixed_content", url, timeout)


def check_robots_txt(url, timeout=TIMEOUT):
    return _probe("check_robots_txt", url, timeout)


def check_security_txt(url, timeout=TIMEOUT):
    return _probe("check_security_txt", url, timeout)


def check_sitemap(url, timeout=TIMEOUT):
    return _probe("check_sitemap", url, timeout)


def check_options(url, timeout=TIMEOUT):
    return _probe("check_options", url, timeout)


def check_json_document(url, timeout=TIMEOUT):
    return _probe("check_json_document", url, timeout)


def check_health_document(url, timeout=TIMEOUT):
    return _probe("check_health_document", url, timeout)


def check_openapi_document(url, timeout=TIMEOUT):
    return _probe("check_openapi_document", url, timeout)


def check_rate_limit_headers(url, timeout=TIMEOUT):
    return _probe("check_rate_limit_headers", url, timeout)


def check_api_error_shape(url, timeout=TIMEOUT):
    return _probe("check_api_error_shape", url, timeout)


def check_etag(url, timeout=TIMEOUT):
    return _probe("check_etag", url, timeout)


def check_compression(url, timeout=TIMEOUT):
    return _probe("check_compression", url, timeout)


def check_x_content_type_options(url, timeout=TIMEOUT):
    return _probe("check_x_content_type_options", url, timeout)


def check_cross_origin_embedder(url, timeout=TIMEOUT):
    return _probe("check_cross_origin_embedder", url, timeout)


def check_cross_origin_opener(url, timeout=TIMEOUT):
    return _probe("check_cross_origin_opener", url, timeout)


def check_cross_origin_resource(url, timeout=TIMEOUT):
    return _probe("check_cross_origin_resource", url, timeout)


def check_well_known(url, timeout=TIMEOUT):
    return _probe("check_well_known", url, timeout)


def check_manifest(url, timeout=TIMEOUT):
    return _probe("check_manifest", url, timeout)


def check_favicon(url, timeout=TIMEOUT):
    return _probe("check_favicon", url, timeout)


def check_html_links(url, timeout=TIMEOUT):
    return _probe("check_html_links", url, timeout)


def check_external_hosts(url, timeout=TIMEOUT):
    return _probe("check_external_hosts", url, timeout)


def check_password_forms(url, timeout=TIMEOUT):
    return _probe("check_password_forms", url, timeout)


def check_sensitive_paths(url, timeout=TIMEOUT):
    return _probe("check_sensitive_paths", url, timeout)


def check_content_disposition(url, timeout=TIMEOUT):
    return _probe("check_content_disposition", url, timeout)


def check_http_only_session(url, timeout=TIMEOUT):
    return _probe("check_http_only_session", url, timeout)


def check_origin_reflection(url, timeout=TIMEOUT):
    return _probe("check_origin_reflection", url, timeout)


def check_http_methods(url, timeout=TIMEOUT):
    return _probe("check_http_methods", url, timeout)


def check_hsts_preload(url, timeout=TIMEOUT):
    return _probe("check_hsts_preload", url, timeout)


def check_xss_protection(url, timeout=TIMEOUT):
    return _probe("check_xss_protection", url, timeout)


def check_vary_header(url, timeout=TIMEOUT):
    return _probe("check_vary_header", url, timeout)


def _run_checks(url, names=None, timeout=TIMEOUT):
    selected = list(CHECK_NAMES) if names is None else list(names)
    invalid = sorted(set(selected) - set(CHECK_NAMES))
    if invalid:
        raise ValueError("unknown checks: " + ", ".join(invalid))
    normalized_url = _normalize_url(url)
    timeout_value = _validate_timeout(timeout)
    results = [globals()[name](normalized_url, timeout_value) for name in selected]
    return {
        "url": normalized_url,
        "checks": results,
        "passed": sum(item["ok"] for item in results),
        "total": len(results),
    }


def _main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run safe, read-only HTTP defensive checks against an authorized target"
    )
    parser.add_argument("url", nargs="?", help="HTTP or HTTPS URL")
    parser.add_argument("--checks", help="comma-separated check names")
    parser.add_argument("--timeout", type=float, default=TIMEOUT)
    parser.add_argument("--list", action="store_true", help="list available checks")
    args = parser.parse_args(argv)
    if args.list:
        print("\n".join(CHECK_NAMES))
        return 0
    if not args.url:
        parser.error("a target URL is required unless --list is used")
    names = [item.strip() for item in args.checks.split(",")] if args.checks else None
    try:
        result = _run_checks(args.url, names, args.timeout)
    except (ValueError, requests.RequestException) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
