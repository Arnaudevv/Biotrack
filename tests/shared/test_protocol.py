"""Tests for the shared HTTP-like protocol helpers."""

import json
import unittest
from datetime import date, datetime
from decimal import Decimal

from shared.protocol import (
    build_request,
    build_response,
    parse_request,
    parse_response,
    percent_decode,
    percent_encode,
    read_http_message,
)
from tests.helpers import FakeSocket, make_request, make_response


class ProtocolTests(unittest.TestCase):
    def test_request_and_response_round_trip(self):
        request = build_request("post", "/patients", {"code": "P-1", "active": True})
        parsed = parse_request(request)
        self.assertEqual(parsed["method"], "POST")
        self.assertEqual(parsed["path"], "/patients")
        self.assertEqual(parsed["body"]["code"], "P-1")

        response = build_response(200, {"message": "pong"})
        parsed_response = parse_response(response)
        self.assertEqual(parsed_response["status"], 200)
        self.assertEqual(parsed_response["body"]["message"], "pong")

    def test_percent_encoding_round_trip(self):
        value = "Ana María + 1"
        encoded = percent_encode(value)
        self.assertEqual(percent_decode(encoded), value)

    def test_read_http_message_fragmented(self):
        raw = make_request("GET", "/ping")
        for chunk_size in (1, 5, 4096):
            chunks = [raw[i:i + chunk_size] for i in range(0, len(raw), chunk_size)]
            sock = FakeSocket(chunks)
            self.assertEqual(read_http_message(sock), raw)

    def test_parse_response_handles_json_and_decimal(self):
        sample = {"date": date(2024, 1, 2), "timestamp": datetime(2024, 1, 2, 3, 4, 5), "amount": Decimal("12.3400")}
        response = build_response(200, sample)
        parsed = parse_response(response)
        self.assertEqual(parsed["status"], 200)
        self.assertIn("amount", parsed["body"])
        self.assertEqual(parsed["body"]["amount"], "12.3400")

    def test_invalid_messages_raise_errors(self):
        with self.assertRaises(ValueError):
            parse_request(b"BAD")
        with self.assertRaises(ValueError):
            parse_request(b"GET /ping HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Length: 5\r\n\r\n")


if __name__ == "__main__":
    unittest.main()
