#!/usr/bin/env python3
"""Thin, unofficial standard-library client for a native Autoverse JSON request.

The caller supplies the complete request envelope. This helper does not discover
objects, change avrs configuration, retry requests, or infer API-level success.
"""

import argparse
import http.client
import json
import math
from pathlib import Path
import sys


MAX_RESPONSE_BYTES = 16 * 1024 * 1024
ENVELOPE_KEYS = {"TargetObjectId", "RequestType", "bVerboseResponse", "RequestBody"}


def positive_timeout(value):
    try:
        result = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("timeout must be a finite positive number") from error
    if not math.isfinite(result) or result <= 0:
        raise argparse.ArgumentTypeError("timeout must be a finite positive number")
    return result


def valid_port(value):
    try:
        result = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("port must be an integer between 1 and 65535") from error
    if not 1 <= result <= 65535:
        raise argparse.ArgumentTypeError("port must be an integer between 1 and 65535")
    return result


def valid_host(value):
    if not value or any(char.isspace() for char in value) or "/" in value:
        raise argparse.ArgumentTypeError("host must be a hostname or IP address without a URL scheme")
    return value


def reject_constant(value):
    raise ValueError("non-finite JSON number is not allowed: " + value)


def finite_float(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("non-finite JSON number is not allowed: " + value)
    return result


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def load_envelope(source):
    envelope = json.loads(
        source,
        parse_constant=reject_constant,
        parse_float=finite_float,
        object_pairs_hook=unique_object,
    )
    if not isinstance(envelope, dict):
        raise ValueError("request must be a JSON object containing the four native envelope keys")
    if set(envelope) != ENVELOPE_KEYS:
        missing = sorted(ENVELOPE_KEYS - set(envelope))
        extra = sorted(set(envelope) - ENVELOPE_KEYS)
        raise ValueError(f"request envelope keys do not match; missing={missing}, extra={extra}")
    target = envelope["TargetObjectId"]
    if isinstance(target, bool) or not isinstance(target, (str, int)):
        raise ValueError("TargetObjectId must be a string or integer, not a boolean")
    request_type = envelope["RequestType"]
    if not isinstance(request_type, str) or not request_type.strip():
        raise ValueError("RequestType must be a nonempty string")
    if not isinstance(envelope["bVerboseResponse"], bool):
        raise ValueError("bVerboseResponse must be a boolean")
    if not isinstance(envelope["RequestBody"], (dict, str)):
        raise ValueError("RequestBody must be an object or string")
    return envelope


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    source = result.add_mutually_exclusive_group(required=True)
    source.add_argument("--request-file", type=Path, help="UTF-8 JSON file containing the complete native envelope; '-' reads standard input")
    source.add_argument("--stdin", "-stdin", action="store_true", help="read the complete native envelope from standard input")
    result.add_argument("--host", type=valid_host, default="127.0.0.1")
    result.add_argument("--port", type=valid_port, default=30313)
    result.add_argument("--timeout", type=positive_timeout, default=10.0, help="socket timeout in seconds; no automatic retries")
    result.add_argument("--dry-run", action="store_true", help="print a request preview without opening a connection")
    result.add_argument("--response-file", type=Path, help="save the complete raw response bytes, including non-200 responses")
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        from_stdin = args.stdin or args.request_file == Path("-")
        source = sys.stdin.read() if from_stdin else args.request_file.read_text(encoding="utf-8")
        envelope = load_envelope(source)
        payload = json.dumps(envelope, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        print(f"Invalid request; no connection opened: {error}", file=sys.stderr)
        return 2

    if args.dry_run:
        preview = {
            "method": "POST",
            "host": args.host,
            "port": args.port,
            "path": "/post",
            "headers": {"Content-Type": "application/json"},
            "body": envelope,
        }
        print(json.dumps(preview, ensure_ascii=False, allow_nan=False, indent=2))
        return 0

    connection = None
    try:
        connection = http.client.HTTPConnection(args.host, args.port, timeout=args.timeout)
        connection.request("POST", "/post", body=payload, headers={"Content-Type": "application/json"})
        response = connection.getresponse()
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            print(
                f"HTTP {response.status}: response exceeds the {MAX_RESPONSE_BYTES}-byte limit; "
                "truncated data was not printed or saved.",
                file=sys.stderr,
            )
            return 1
        if args.response_file is not None:
            args.response_file.write_bytes(raw)
        text = raw.decode("utf-8")
        sys.stdout.write(text)
        if response.status != 200:
            print(f"HTTP {response.status}: transport request failed; inspect the response.", file=sys.stderr)
            return 1
        print("HTTP 200 received; API-level success must be checked in the response.", file=sys.stderr)
        return 0
    except (OSError, http.client.HTTPException, UnicodeError, ValueError) as error:
        print(
            f"Request/response handling failed ({type(error).__name__}): {error}; "
            "the request may already have executed. Simulator state is unknown; "
            "query the relevant state before deciding whether to retry. No automatic retry performed.",
            file=sys.stderr,
        )
        return 1
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
