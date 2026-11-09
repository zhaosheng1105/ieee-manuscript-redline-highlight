#!/usr/bin/env python3
"""Offline tests: HTTPConnection is always mocked; no socket is opened."""

from contextlib import redirect_stderr, redirect_stdout
import http.client
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import avrs_http


class AvrsHttpTests(unittest.TestCase):
    def setUp(self):
        self.envelope = {
            "TargetObjectId": "ego",
            "RequestType": "GetFrictionModifiers",
            "bVerboseResponse": False,
            "RequestBody": {"Tires": "All"},
        }
        self.response = Mock(status=200)
        self.response.read.return_value = b"FL: 1\nFR: 1\nRL: 1\nRR: 1"
        self.connection = Mock()
        self.connection.getresponse.return_value = self.response
        self.factory_patch = patch.object(avrs_http.http.client, "HTTPConnection", return_value=self.connection)
        self.factory = self.factory_patch.start()
        self.addCleanup(self.factory_patch.stop)

    def invoke(self, args=None, text=None):
        output, errors = io.StringIO(), io.StringIO()
        if text is None:
            text = json.dumps(self.envelope, ensure_ascii=False)
        with patch("sys.stdin", io.StringIO(text)), redirect_stdout(output), redirect_stderr(errors):
            try:
                code = avrs_http.main(["--stdin", *(args or [])])
            except SystemExit as error:
                code = error.code
        return code, output.getvalue(), errors.getvalue()

    def test_dry_run_does_not_create_connection_or_response_file(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "response.txt"
            code, output, errors = self.invoke(["--dry-run", "--response-file", str(destination)])
            self.assertEqual(code, 0)
            preview = json.loads(output)
            self.assertEqual(preview["body"], self.envelope)
            self.assertEqual((preview["method"], preview["path"]), ("POST", "/post"))
            self.assertFalse(destination.exists())
            self.assertEqual(errors, "")
            self.factory.assert_not_called()

    def test_exact_request_envelope_and_integer_target(self):
        self.envelope["TargetObjectId"] = 7
        self.envelope["RequestBody"] = {"文字": "轮胎"}
        code, output, errors = self.invoke(["--host", "sim.example", "--port", "30314", "--timeout", "2.5"])
        self.assertEqual(code, 0)
        self.factory.assert_called_once_with("sim.example", 30314, timeout=2.5)
        call = self.connection.request.call_args
        self.assertEqual(call[0], ("POST", "/post"))
        self.assertEqual(call[1]["headers"], {"Content-Type": "application/json"})
        payload = call[1]["body"]
        self.assertIsInstance(payload, bytes)
        self.assertEqual(json.loads(payload), self.envelope)
        self.assertIn("轮胎".encode("utf-8"), payload)
        self.assertEqual(output, self.response.read.return_value.decode())
        self.assertIn("API-level success must be checked", errors)
        self.response.read.assert_called_once_with(avrs_http.MAX_RESPONSE_BYTES + 1)
        self.connection.close.assert_called_once_with()

    def test_utf8_response_is_preserved_in_stdout_and_file(self):
        raw = '{  "结果": "成功", "escaped": "a\\nb" }\n'.encode("utf-8")
        self.response.read.return_value = raw
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "response.json"
            code, output, _ = self.invoke(["--response-file", str(destination)])
            self.assertEqual(code, 0)
            self.assertEqual(output.encode("utf-8"), raw)
            self.assertEqual(destination.read_bytes(), raw)

    def test_http_error_preserves_response_and_closes(self):
        self.response.status = 503
        self.response.read.return_value = "暂不可用\n".encode("utf-8")
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "failure.txt"
            code, output, errors = self.invoke(["--response-file", str(destination)])
            self.assertEqual(code, 1)
            self.assertEqual(output, "暂不可用\n")
            self.assertEqual(destination.read_bytes(), self.response.read.return_value)
            self.assertIn("HTTP 503", errors)
            self.connection.close.assert_called_once_with()

    def test_timeout_is_not_retried_and_connection_is_closed(self):
        self.connection.request.side_effect = TimeoutError("timed out")
        code, output, errors = self.invoke()
        self.assertEqual(code, 1)
        self.assertEqual(output, "")
        self.assertIn("TimeoutError", errors)
        self.assertIn("No automatic retry", errors)
        self.assertIn("may already have executed", errors)
        self.assertIn("state is unknown", errors)
        self.factory.assert_called_once()
        self.connection.request.assert_called_once()
        self.connection.getresponse.assert_not_called()
        self.connection.close.assert_called_once_with()

    def test_connection_creation_error_has_no_retry(self):
        self.factory.side_effect = OSError("connection failed")
        code, _, errors = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn("connection failed", errors)
        self.assertIn("query the relevant state", errors)
        self.factory.assert_called_once()
        self.connection.close.assert_not_called()

    def test_incomplete_response_is_failure_and_closes(self):
        self.response.read.side_effect = http.client.IncompleteRead(b"partial", 8)
        code, output, errors = self.invoke()
        self.assertEqual(code, 1)
        self.assertEqual(output, "")
        self.assertIn("IncompleteRead", errors)
        self.connection.close.assert_called_once_with()

    def test_invalid_json_is_rejected_before_network(self):
        samples = [
            "{",
            "[]",
            '{"TargetObjectId":"ego","TargetObjectId":7}',
        ]
        base = json.dumps(self.envelope)
        samples.extend(base.replace('"All"', value) for value in ("NaN", "Infinity", "-Infinity", "1e999"))
        samples.append(base.replace('{"Tires": "All"}', '{"Tires":"All","Tires":"FL"}'))
        for source in samples:
            with self.subTest(source=source):
                code, output, errors = self.invoke(text=source)
                self.assertEqual(code, 2)
                self.assertEqual(output, "")
                self.assertIn("no connection opened", errors)
        self.factory.assert_not_called()

    def test_invalid_envelope_fields_are_rejected_before_network(self):
        changes = [
            ("TargetObjectId", True), ("TargetObjectId", 1.5), ("TargetObjectId", None),
            ("RequestType", "  "), ("RequestType", 4),
            ("bVerboseResponse", "false"), ("bVerboseResponse", 0),
            ("RequestBody", []), ("RequestBody", None),
        ]
        for key, value in changes:
            with self.subTest(key=key, value=value):
                source = dict(self.envelope)
                source[key] = value
                self.assertEqual(self.invoke(text=json.dumps(source))[0], 2)
        for source in ({**self.envelope, "Unexpected": 1}, {k: v for k, v in self.envelope.items() if k != "RequestBody"}):
            self.assertEqual(self.invoke(text=json.dumps(source))[0], 2)
        self.factory.assert_not_called()

    def test_invalid_cli_parameters_are_rejected_before_network(self):
        cases = [
            ["--port", "0"], ["--port", "65536"], ["--port", "3.5"],
            ["--timeout", "0"], ["--timeout", "-1"], ["--timeout", "nan"],
            ["--timeout", "inf"], ["--timeout", "bad"],
            ["--host", ""], ["--host", "http://localhost"],
        ]
        for args in cases:
            with self.subTest(args=args):
                self.assertEqual(self.invoke(args)[0], 2)
        self.factory.assert_not_called()

    def test_oversized_response_is_not_saved_or_printed(self):
        self.response.read.return_value = b"x" * (avrs_http.MAX_RESPONSE_BYTES + 1)
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "response.txt"
            code, output, errors = self.invoke(["--response-file", str(destination)])
            self.assertEqual(code, 1)
            self.assertEqual(output, "")
            self.assertFalse(destination.exists())
            self.assertIn("exceeds", errors)
        self.connection.close.assert_called_once_with()

    def test_exact_limit_is_not_rejected(self):
        self.response.read.return_value = b"x" * avrs_http.MAX_RESPONSE_BYTES
        code, output, _ = self.invoke()
        self.assertEqual(code, 0)
        self.assertEqual(len(output), avrs_http.MAX_RESPONSE_BYTES)

    def test_non_utf8_response_is_preserved_to_file_but_fails(self):
        self.response.read.return_value = b"\xff"
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "response.bin"
            code, output, errors = self.invoke(["--response-file", str(destination)])
            self.assertEqual(code, 1)
            self.assertEqual(output, "")
            self.assertEqual(destination.read_bytes(), b"\xff")
            self.assertIn("UnicodeDecodeError", errors)
        self.connection.close.assert_called_once_with()

    def test_string_request_body_is_accepted(self):
        self.envelope["RequestBody"] = ""
        self.assertEqual(self.invoke()[0], 0)

    def test_request_file_and_stdin_alias(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "request.json"
            source.write_text(json.dumps(self.envelope), encoding="utf-8")
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(avrs_http.main(["--request-file", str(source), "--dry-run"]), 0)
                with patch("sys.stdin", io.StringIO(json.dumps(self.envelope))):
                    self.assertEqual(avrs_http.main(["-stdin", "--dry-run"]), 0)
        self.factory.assert_not_called()

    def test_dash_request_file_reads_stdin_and_sends_native_envelope(self):
        output, errors = io.StringIO(), io.StringIO()
        with patch("sys.stdin", io.StringIO(json.dumps(self.envelope))), redirect_stdout(output), redirect_stderr(errors):
            code = avrs_http.main(["--request-file", "-"])
        self.assertEqual(code, 0)
        self.factory.assert_called_once_with("127.0.0.1", 30313, timeout=10.0)
        self.assertEqual(json.loads(self.connection.request.call_args[1]["body"]), self.envelope)
        self.assertEqual(output.getvalue(), self.response.read.return_value.decode("utf-8"))
        self.connection.close.assert_called_once_with()

    def test_missing_or_bad_request_file_opens_no_connection(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "request.json"
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(avrs_http.main(["--request-file", str(source)]), 2)
                source.write_bytes(b"\xff")
                self.assertEqual(avrs_http.main(["--request-file", str(source)]), 2)
        self.factory.assert_not_called()

    def test_source_is_required_and_mutually_exclusive(self):
        for args in ([], ["--stdin", "--request-file", "request.json"]):
            with self.subTest(args=args), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                avrs_http.main(args)
            self.assertEqual(error.exception.code, 2)
        self.factory.assert_not_called()

    def test_response_file_write_failure_closes_connection(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "missing" / "response.txt"
            code, _, errors = self.invoke(["--response-file", str(destination)])
            self.assertEqual(code, 1)
            self.assertIn("FileNotFoundError", errors)
        self.connection.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
