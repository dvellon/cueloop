"""Dependency-free local REST API and static dashboard server."""

from __future__ import annotations

from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .pipeline import CueLoopPipeline


STATIC_ROOT = Path(__file__).with_name("dashboard")
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}


class CueLoopHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], pipeline: CueLoopPipeline) -> None:
        self.pipeline = pipeline
        super().__init__(address, CueLoopHandler)


class CueLoopHandler(BaseHTTPRequestHandler):
    server: CueLoopHTTPServer
    server_version = "CueLoop/0.1"

    def log_message(self, format_string: str, *args: object) -> None:
        # Keep the competition console readable. Service startup is explicit.
        return

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; connect-src 'self'")
        self.send_header("X-Frame-Options", "DENY")
        super().end_headers()

    def _json(self, status: HTTPStatus, payload: object) -> None:
        encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _read_json(self) -> dict[str, object]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("invalid content length") from error
        if not 0 < length <= 4096:
            raise ValueError("JSON body must be 1..4096 bytes")
        if self.headers.get_content_type() != "application/json":
            raise ValueError("Content-Type must be application/json")
        payload = json.loads(self.rfile.read(length))
        if not isinstance(payload, dict):
            raise ValueError("JSON object required")
        return payload

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            self._json(HTTPStatus.OK, self.server.pipeline.snapshot())
            return
        if parsed.path == "/api/events":
            try:
                limit = int(parse_qs(parsed.query).get("limit", ["50"])[0])
            except ValueError:
                self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid limit"})
                return
            self._json(
                HTTPStatus.OK,
                {"events": self.server.pipeline.store.list(limit=limit)},
            )
            return
        if parsed.path == "/api/config":
            self._json(
                HTTPStatus.OK,
                {"classes": self.server.pipeline.engine.policies_snapshot()},
            )
            return
        static = STATIC_FILES.get(parsed.path)
        if static is not None:
            filename, content_type = static
            try:
                content = (STATIC_ROOT / filename).read_bytes()
            except OSError:
                self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "asset missing"})
                return
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
        self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        parsed = urlparse(self.path)
        try:
            payload = self._read_json()
            if parsed.path == "/api/mute":
                seconds = float(payload.get("seconds", 0))
                self.server.pipeline.engine.mute(seconds)
                self._json(
                    HTTPStatus.OK,
                    self.server.pipeline.engine.state_snapshot(),
                )
                return
            if parsed.path == "/api/history/clear":
                if payload.get("confirm") is not True:
                    raise ValueError("confirm must be true")
                self.server.pipeline.clear_history()
                self._json(HTTPStatus.OK, {"cleared": True})
                return
            if parsed.path.startswith("/api/config/"):
                label = parsed.path.removeprefix("/api/config/")
                policy = self.server.pipeline.engine.update_policy(label, payload)
                self._json(
                    HTTPStatus.OK,
                    {"label": label, "policy": asdict(policy)},
                )
                return
            parts = parsed.path.strip("/").split("/")
            if len(parts) == 4 and parts[:2] == ["api", "events"]:
                event_id, action = parts[2], parts[3]
                if action not in ("acknowledge", "dismiss"):
                    raise ValueError("unsupported action")
                stored_action = "acknowledged" if action == "acknowledge" else "dismissed"
                changed = self.server.pipeline.feedback(event_id, stored_action)
                self._json(
                    HTTPStatus.OK if changed else HTTPStatus.NOT_FOUND,
                    {"updated": changed, "action": stored_action},
                )
                return
            self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            self._json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
