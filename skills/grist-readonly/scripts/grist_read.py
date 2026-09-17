#!/usr/bin/env python3
"""Read one administrator-configured Grist document using GET requests only."""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request


IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
DOC_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
SORT_RE = re.compile(r"^-?[A-Za-z_][A-Za-z0-9_]*(,-?[A-Za-z_][A-Za-z0-9_]*)*$")
MAX_RECORDS = 500


def identifier(value: str) -> str:
    if not IDENTIFIER_RE.fullmatch(value):
        raise argparse.ArgumentTypeError("Expected a Grist table or column ID.")
    return value


def positive_record_id(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("Record ID must be positive.")
    return parsed


def record_limit(value: str) -> int:
    parsed = int(value)
    if parsed < 1 or parsed > MAX_RECORDS:
        raise argparse.ArgumentTypeError(f"Limit must be between 1 and {MAX_RECORDS}.")
    return parsed


def offset(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("Offset must be zero or greater.")
    return parsed


def filter_object(value: str) -> dict:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"Invalid filter JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("Filter must be a JSON object.")
    for column, accepted_values in parsed.items():
        if not isinstance(column, str) or not IDENTIFIER_RE.fullmatch(column):
            raise argparse.ArgumentTypeError("Filter keys must be Grist column IDs.")
        if not isinstance(accepted_values, list):
            raise argparse.ArgumentTypeError("Each filter value must be an array.")
    return parsed


def sort_expression(value: str) -> str:
    if not SORT_RE.fullmatch(value):
        raise argparse.ArgumentTypeError("Sort must contain comma-separated Grist column IDs.")
    return value


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Read the configured Grist document.")
    commands = root.add_subparsers(dest="operation", required=True)
    commands.add_parser("tables", help="List user tables.")
    columns = commands.add_parser("columns", help="List columns for one table.")
    columns.add_argument("--table", required=True, type=identifier)
    records = commands.add_parser("records", help="Get records from one table.")
    records.add_argument("--table", required=True, type=identifier)
    records.add_argument("--limit", type=record_limit, default=100)
    records.add_argument("--offset", type=offset, default=0)
    records.add_argument("--filter", type=filter_object)
    records.add_argument("--sort", type=sort_expression)
    record = commands.add_parser("record", help="Get one record by numeric ID.")
    record.add_argument("--table", required=True, type=identifier)
    record.add_argument("--id", required=True, type=positive_record_id)
    return root


def load_configuration() -> tuple[str, str, str]:
    base_url = os.environ.get("GRIST_BASE_URL", "").rstrip("/")
    doc_id = os.environ.get("GRIST_DOC_ID", "")
    api_key = os.environ.get("GRIST_API_KEY", "")
    parsed = urllib.parse.urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("GRIST_BASE_URL must be an absolute HTTP(S) URL.")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("GRIST_BASE_URL must not contain credentials, a query, or a fragment.")
    if not DOC_ID_RE.fullmatch(doc_id):
        raise ValueError("GRIST_DOC_ID is missing or invalid.")
    if not api_key:
        raise ValueError("GRIST_API_KEY is not loaded.")
    return base_url, doc_id, api_key


def request_path(args: argparse.Namespace, doc_id: str) -> tuple[str, dict[str, str]]:
    root = f"/api/docs/{doc_id}/tables"
    if args.operation == "tables":
        return root, {}
    table = urllib.parse.quote(args.table, safe="")
    if args.operation == "columns":
        return f"{root}/{table}/columns", {}
    if args.operation == "record":
        return f"{root}/{table}/records", {
            "limit": "1",
            "filter": json.dumps({"id": [args.id]}),
        }
    query = {"limit": str(args.limit), "offset": str(args.offset)}
    if args.filter is not None:
        query["filter"] = json.dumps(args.filter, separators=(",", ":"))
    if args.sort is not None:
        query["sort"] = args.sort
    return f"{root}/{table}/records", query


def main() -> int:
    args = parser().parse_args()
    try:
        base_url, doc_id, api_key = load_configuration()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    path, query = request_path(args, doc_id)
    url = base_url + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        print(f"Grist returned HTTP {exc.code}.", file=sys.stderr)
        return 1
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"Grist request failed: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError:
        print("Grist returned an invalid JSON response.", file=sys.stderr)
        return 1
    if args.operation == "record":
        records = result.get("records", [])
        result = records[0] if records else None
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
