#!/usr/bin/env python3
"""Read one administrator-configured Grist document using GET requests only."""

import argparse
import json
import os
import re
import sys
import unicodedata
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


def non_empty_text(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("Lookup value must not be empty.")
    return value


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
    lookup = commands.add_parser(
        "lookup",
        help="Find minimal record references by a human-readable or stable value.",
    )
    lookup.add_argument("--table", required=True, type=identifier)
    lookup.add_argument("--column", required=True, type=identifier)
    lookup.add_argument("--value", required=True, type=non_empty_text)
    lookup.add_argument("--stable-column", type=identifier)
    lookup.add_argument("--limit", type=record_limit, default=MAX_RECORDS)
    lookup.add_argument(
        "--fallback",
        choices=("none", "contains"),
        default="contains",
        help="Fallback after no normalized exact match (default: contains).",
    )
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


def get_json(base_url: str, path: str, query: dict[str, str], api_key: str) -> dict:
    url = base_url + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def normalized(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).casefold()
    text = "".join(character for character in text if not unicodedata.combining(character))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def minimal_matches(
    records: list[dict], column: str, stable_column: str | None, value: str, mode: str
) -> list[dict]:
    wanted = normalized(value)
    matches = []
    for record in records:
        fields = record.get("fields", {})
        candidate = normalized(fields.get(column))
        is_match = candidate == wanted if mode == "exact" else wanted in candidate
        if not is_match:
            continue
        match = {"id": record.get("id"), "value": fields.get(column)}
        if stable_column:
            match["stable_value"] = fields.get(stable_column)
        matches.append(match)
    return matches


def lookup_records(
    args: argparse.Namespace, base_url: str, doc_id: str, api_key: str
) -> dict:
    table = urllib.parse.quote(args.table, safe="")
    path = f"/api/docs/{doc_id}/tables/{table}/records"
    exact_query = {
        "limit": str(args.limit),
        "filter": json.dumps({args.column: [args.value]}, separators=(",", ":")),
    }
    exact_result = get_json(base_url, path, exact_query, api_key)
    matches = minimal_matches(
        exact_result.get("records", []),
        args.column,
        args.stable_column,
        args.value,
        "exact",
    )
    if matches:
        return {"match_type": "exact", "matches": matches}

    all_result = get_json(base_url, path, {"limit": str(args.limit)}, api_key)
    records = all_result.get("records", [])
    matches = minimal_matches(
        records, args.column, args.stable_column, args.value, "exact"
    )
    if matches:
        return {"match_type": "exact", "matches": matches}
    if args.fallback == "contains":
        matches = minimal_matches(
            records, args.column, args.stable_column, args.value, "contains"
        )
        if matches:
            return {"match_type": "contains", "matches": matches}
    return {"match_type": "none", "matches": []}


def main() -> int:
    args = parser().parse_args()
    try:
        base_url, doc_id, api_key = load_configuration()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    try:
        if args.operation == "lookup":
            result = lookup_records(args, base_url, doc_id, api_key)
        else:
            path, query = request_path(args, doc_id)
            result = get_json(base_url, path, query, api_key)
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
