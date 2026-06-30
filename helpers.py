"""Helper functions for the OPC Simulator web server.

These are stateless utilities used by the HTTP handler:
- ``ThreadingHTTPServer`` — stdlib ``HTTPServer`` with thread-per-request
- ``MIME_TYPES`` — extension → Content-Type map for static files
- ``_parse_json_body`` — safe JSON request body parsing with size limit
- ``_require_fields`` — required-field validation
- ``_parse_multipart_file`` — stdlib multipart/form-data parser (replaces cgi)
- ``_is_path_allowed`` — file_path allowlist check
- ``_consteq`` — constant-time string comparison for token auth
"""
from __future__ import annotations

import hmac
import json
import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import Any, Dict, Optional, Tuple

from app_config import MAX_REQUEST_BYTES, MODEL_PATH_ALLOWLIST, log

# ---------------------------------------------------------------------------
# Thread-safe HTTPServer
# ---------------------------------------------------------------------------


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle each request in its own thread."""
    daemon_threads = True


# ---------------------------------------------------------------------------
# MIME types
# ---------------------------------------------------------------------------

MIME_TYPES: Dict[str, str] = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


# ---------------------------------------------------------------------------
# Input validation helpers
# ---------------------------------------------------------------------------

def parse_json_body(handler: SimpleHTTPRequestHandler) -> Optional[Dict[str, Any]]:
    """Safely parse JSON request body.  Sends 400 on failure.

    Public name (no leading underscore) so the API handler module can import
    it without looking like a private API.
    """
    try:
        length = int(handler.headers.get("Content-Length", "0"))
    except (ValueError, TypeError):
        handler.send_error(400, "Missing or invalid Content-Length")
        return None
    if length <= 0:
        handler.send_error(400, "Empty body")
        return None
    if length > MAX_REQUEST_BYTES:
        handler.send_error(413, "Request body too large")
        return None
    try:
        body = handler.rfile.read(length)
        return json.loads(body)
    except json.JSONDecodeError:
        handler.send_error(400, "Invalid JSON body")
        return None
    except Exception:
        handler.send_error(400, "Failed to read request body")
        return None


def require_fields(data: Dict[str, Any], *fields: str) -> Optional[str]:
    """Check that all required fields exist.  Returns first missing or None."""
    for f in fields:
        val = data.get(f)
        if val is None or (isinstance(val, str) and val.strip() == ""):
            return f
    return None


def parse_multipart_file(body: bytes, content_type: str) -> Tuple[str, bytes]:
    """Extract the first file part from a multipart/form-data body.

    Returns ``(filename, file_bytes)``.  Raises ``ValueError`` on malformed
    input.  Uses only the stdlib — replaces the deprecated ``cgi`` module.
    """
    if "boundary=" not in content_type:
        raise ValueError("multipart boundary not found in Content-Type")
    boundary = content_type.split("boundary=", 1)[1].strip()
    if boundary.startswith('"') and boundary.endswith('"'):
        boundary = boundary[1:-1]
    delimiter = b"--" + boundary.encode("ascii")

    parts = body.split(delimiter)
    for part in parts:
        if not part or part in (b"--", b"--\r\n", b"\r\n"):
            continue
        part = part.strip(b"\r\n")
        if not part:
            continue
        header_end = part.find(b"\r\n\r\n")
        if header_end == -1:
            continue
        header_bytes = part[:header_end].decode("utf-8", errors="replace")
        data_bytes = part[header_end + 4:]
        if data_bytes.endswith(b"\r\n"):
            data_bytes = data_bytes[:-2]

        filename: Optional[str] = None
        is_file = False
        for line in header_bytes.split("\r\n"):
            lower = line.lower()
            if lower.startswith("content-disposition:"):
                if "filename=" in lower:
                    for token in line.split(";"):
                        token = token.strip()
                        if token.lower().startswith("filename="):
                            filename = token[len("filename="):].strip().strip('"')
                            is_file = True
                            break
        if is_file and filename:
            return filename, data_bytes

    raise ValueError("No file part found in multipart body")


def is_path_allowed(path: Path) -> bool:
    """Return True if ``path`` is inside one of the allowlist roots."""
    try:
        resolved = path.resolve()
    except (OSError, RuntimeError):
        return False
    for root in MODEL_PATH_ALLOWLIST:
        try:
            resolved.relative_to(root.resolve())
            return True
        except ValueError:
            continue
    return False


def consteq(a: str, b: str) -> bool:
    """Constant-time string comparison to prevent timing attacks on tokens."""
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


# ---------------------------------------------------------------------------
# Backwards-compatible aliases (tests / external callers may still use the
# underscore-prefixed names)
# ---------------------------------------------------------------------------

_parse_json_body = parse_json_body
_require_fields = require_fields
_parse_multipart_file = parse_multipart_file
_is_path_allowed = is_path_allowed
_consteq = consteq
