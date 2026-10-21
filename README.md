# BioTrack

BioTrack is a client/server TCP refactor of the original terminal-based biobank management application. The application separates the business and persistence concerns in a server process and keeps the terminal client as a thin consumer of a network API.

## Overview

The project follows a layered design:

- Shared: protocol codec, DTO conversion, serialization helpers, common error types
- Server: persistence, services, controllers, router, TCP listener
- Client: terminal UI, connection wrapper, API client calls

The server is intentionally sequential and blocking: it accepts one client at a time, reads one request, processes it, and sends one response before continuing.

## Architecture

`	ext
+---------------------+
| Client (terminal)   |
| - Rich UI           |
| - API client        |
| - TCP socket        |
+----------+----------+
           |
           | JSON payload over TCP
           v
+---------------------+
| Shared protocol     |
| - request/response  |
| - percent encoding  |
| - JSON conversion   |
+----------+----------+
           |
           v
+---------------------+
| Server              |
| - TCP listener      |
| - router            |
| - services          |
| - controllers       |
| - SQLAlchemy        |
+---------------------+
`

## Key constraints

- Python standard library sockets only
- No web framework, no requests, no urllib, no async networking
- SQLAlchemy is server-side only
- Client does not import server persistence or ORM modules
- Protocol is HTTP-like over raw TCP sockets
- One client at a time

## Project structure

`	ext
.
├── client/
│   ├── api_client.py
│   ├── cli_app.py
│   ├── connection.py
│   ├── settings.py
│   └── __init__.py
├── docs/
│   └── protocol.md
├── server/
│   ├── app.py
│   ├── tcp_server.py
│   ├── router.py
│   ├── settings.py
│   ├── controllers/
│   ├── services/
│   └── persistence/
├── shared/
│   ├── protocol.py
│   ├── dtos.py
│   ├── errors.py
│   └── __init__.py
├── tests/
│   ├── shared/
│   ├── server/
│   └── client/
├── run_server.py
├── run_client.py
├── AGENT_BRIEF_BIOTRACK.md
├── pyproject.toml
├── requirements.txt
├── requirements-client.txt
├── requirements-server.txt
├── requirements-dev.txt
├── .env.example
└── README.md
`

## Running the server

From the project root:

`ash
python run_server.py
`

The server listens on the configured default host/port and handles one request at a time.

## Running the client

`ash
python run_client.py
`

## Running tests

`ash
python -m unittest discover -s tests -t .
`

The tests are designed to run without a real network or a real database; they mock sockets and unit-of-work dependencies as needed.

## Protocol summary

The application protocol is defined in [docs/protocol.md](docs/protocol.md). It uses:

- a request line such as GET /patients HTTP/1.1
- UTF-8 JSON bodies
- Content-Length headers
- server responses with HTTP-like status codes
- percent-encoded query values and path parameters

## Supported resource areas

The server exposes a TCP API for the main BioTrack entities:

- patients
- samples and sample quality control
- staff
- projects and team assignments
- protocols
- containers
- sample types

## Deployment notes

- This project is designed for local development and testing, not for internet-facing deployment.
- There is no authentication layer, no TLS, and no pagination in this version.
- The server is intentionally single-client and blocking to match the brief.

## Validation

The implementation was validated with the project test suite and with targeted import checks to ensure the client remains isolated from persistence and ORM modules.

## Limitations

This version does not implement:

- authentication or authorization
- HTTPS or TLS
- binary protocol file transfer
- pagination
- concurrent multi-client handling
- any external web framework or HTTP library
