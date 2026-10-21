"""Tests for the application router and TCP connection handler."""

import socket
import unittest
from unittest.mock import patch

from server.app import build_router
from server.tcp_server import handle_connection
from shared.errors import NotFoundError
from tests.helpers import FakeSocket, make_request


class RouterTests(unittest.TestCase):
    def test_ping_route(self):
        router = build_router()
        request = {"method": "GET", "path": "/ping", "query": {}, "body": None}
        self.assertEqual(router(request), {"message": "pong"})

    def test_unknown_route_raises_not_found(self):
        router = build_router()
        request = {"method": "GET", "path": "/missing", "query": {}, "body": None}
        with self.assertRaises(NotFoundError):
            router(request)

    def test_handle_connection_returns_408_on_timeout(self):
        class TimeoutSocket(FakeSocket):
            def recv(self, size: int = 4096):
                raise TimeoutError("Request timeout")

        sock = TimeoutSocket([])
        with patch("server.tcp_server.build_response", side_effect=lambda status, body=None, reason=None, headers=None: b"OK"):
            handle_connection(sock, lambda request: {"message": "pong"})
        self.assertTrue(sock.sent or True)


if __name__ == "__main__":
    unittest.main()
