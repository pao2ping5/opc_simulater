"""Static file serving for the OPC Simulator web server.

Serves the React SPA bundle from ``DIST_DIR`` with proper MIME types and
SPA fallback to ``index.html`` for unknown routes.  Path-traversal safe
via ``Path.relative_to``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from app_config import DIST_DIR
from helpers import MIME_TYPES


def serve_static(handler, path: str) -> None:
    """Serve a static file from ``DIST_DIR`` or fall back to SPA index.

    Writes the response directly to ``handler.wfile``.  Caller is responsible
    for CORS / auth checks before calling this.
    """
    if path == "/":
        path = "/index.html"
    content = read_dist(path)
    if content is not None:
        ext = Path(path).suffix
        mime = MIME_TYPES.get(ext, "application/octet-stream")
        handler.send_response(200)
        handler.send_header("Content-Type", mime)
        handler._cors()
        handler.end_headers()
        handler.wfile.write(content)
        return
    # SPA fallback
    content = read_dist("index.html")
    if content is not None:
        handler.send_response(200)
        handler.send_header("Content-Type", "text/html; charset=utf-8")
        handler._cors()
        handler.end_headers()
        handler.wfile.write(content)
        return
    handler.send_error(404, "Not found")


def read_dist(relative_path: str) -> Optional[bytes]:
    """Read a file from ``DIST_DIR`` with path-traversal guard.

    Returns ``None`` if the path escapes ``DIST_DIR`` or doesn't exist.
    Uses ``Path.relative_to`` (not ``str.startswith``) for case-insensitive
    filesystem safety.
    """
    safe = Path(relative_path).as_posix().lstrip("/")
    fp = (DIST_DIR / safe).resolve()
    try:
        fp.relative_to(DIST_DIR.resolve())
    except ValueError:
        return None
    if fp.exists() and fp.is_file():
        return fp.read_bytes()
    return None
