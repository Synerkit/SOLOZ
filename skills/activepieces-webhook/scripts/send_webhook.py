#!/usr/bin/env python3
"""Send one JSON object to an administrator-configured Activepieces webhook."""

import argparse
import ipaddress
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


MAX_PAYLOAD_BYTES = 65_536


def configured_url() -> str:
    url = os.environ.get("ACTIVEPIECES_WEBHOOK_URL", "")
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("ACTIVEPIECES_WEBHOOK_URL must be an absolute HTTP(S) URL.")
    if parsed.username or parsed.password or parsed.fragment:
        raise ValueError("Webhook URL must not contain credentials or a fragment.")
    if not parsed.path.startswith("/api/v1/webhooks/"):
        raise ValueError("Webhook URL must use an Activepieces /api/v1/webhooks/ path.")
    if parsed.hostname.lower() == "localhost":
        raise ValueError("Webhook URL must not use a loopback host.")
    try:
        if ipaddress.ip_address(parsed.hostname).is_loopback:
            raise ValueError("Webhook URL must not use a loopback host.")
    except ValueError as exc:
        if "loopback" in str(exc):
            raise
    return url


def main() -> int:
    parser = argparse.ArgumentParser(description="Trigger the configured Activepieces webhook.")
    parser.add_argument("--json", required=True, dest="json_payload")
    args = parser.parse_args()
    try:
        payload = json.loads(args.json_payload)
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON: {exc}", file=sys.stderr)
        return 2
    if not isinstance(payload, dict):
        print("Payload must be a JSON object.", file=sys.stderr)
        return 2
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    if len(body) > MAX_PAYLOAD_BYTES:
        print(f"Payload exceeds {MAX_PAYLOAD_BYTES} bytes.", file=sys.stderr)
        return 2
    try:
        webhook_url = configured_url()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    request = urllib.request.Request(
        webhook_url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "hermes-activepieces-webhook/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            print(f"HTTP {response.status}")
            print(response.read().decode("utf-8", errors="replace"))
            return 0
    except urllib.error.HTTPError as exc:
        print(f"HTTP {exc.code}", file=sys.stderr)
        print(exc.read().decode("utf-8", errors="replace"), file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Request failed: {exc.reason}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
