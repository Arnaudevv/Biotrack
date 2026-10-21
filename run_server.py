"""Entry point for the BioTrack TCP server."""

from server.app import build_router
from server.tcp_server import serve


if __name__ == "__main__":
    serve(build_router())