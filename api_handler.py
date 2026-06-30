"""HTTP request handler for the OPC Simulator.

Single ``APIHandler`` class extends ``SimpleHTTPRequestHandler`` to serve:
- REST API endpoints under ``/api/*`` (delegating to the simulator)
- Static files for the React SPA (everything else)

Lives in its own module so ``web_server.py`` stays a thin entry point.
"""

from __future__ import annotations

import json
import time
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

from common import (
    build_device_model,
    node_meta_to_dict,
    read_model_excel,
)
from app_config import (
    API_TOKEN,
    CORS_ALLOWED_ORIGINS,
    MAX_REQUEST_BYTES,
    PUBLIC_API_PATHS,
    UPLOAD_DIR,
    log,
)
from helpers import (
    MIME_TYPES,
    _consteq,
    _is_path_allowed,
    _parse_json_body,
    _parse_multipart_file,
    _require_fields,
)
from simulator import GenericOPCSimulator
from static import read_dist


class APIHandler(SimpleHTTPRequestHandler):
    """HTTP handler serving React SPA + REST API."""

    simulator: Optional[GenericOPCSimulator] = None

    # -- Auth ------------------------------------------------------------

    def _check_auth(self, path: str) -> bool:
        """Return True if the request is authorized to access ``path``.

        - Static files (non-/api/) are always allowed (the SPA bundle has no
          secrets; the data comes from the API).
        - ``PUBLIC_API_PATHS`` (e.g. /api/health) bypass auth.
        - When ``API_TOKEN`` is empty, all /api/ requests are allowed (rely
          on loopback bind + same-origin).
        - Otherwise the request's ``Authorization: Bearer <token>`` header
          must match.
        """
        if not path.startswith("/api/"):
            return True
        if path in PUBLIC_API_PATHS:
            return True
        if not API_TOKEN:
            return True
        header = self.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return False
        return _consteq(header[len("Bearer ") :].strip(), API_TOKEN)

    def _send_unauthorized(self) -> None:
        self.send_response(401)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("WWW-Authenticate", "Bearer")
        self._cors()
        self.end_headers()
        self.wfile.write(
            json.dumps(
                {"error": "unauthorized", "message": "Missing or invalid token"}
            ).encode("utf-8")
        )

    # -- CORS ------------------------------------------------------------

    def _cors(self) -> None:
        # Origin-aware CORS: only echo Access-Control-Allow-Origin when the
        # request's Origin matches the configured allowlist.  Default config
        # (empty allowlist) sends no CORS headers → same-origin only.
        origin = self.headers.get("Origin", "")
        allowed = "*" if "*" in CORS_ALLOWED_ORIGINS else origin
        if allowed and (allowed == "*" or origin in CORS_ALLOWED_ORIGINS):
            self.send_header("Access-Control-Allow-Origin", allowed)
            self.send_header(
                "Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS"
            )
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            if allowed != "*":
                self.send_header("Vary", "Origin")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors()
        self.end_headers()

    # -- GET -------------------------------------------------------------

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if not self._check_auth(path):
            self._send_unauthorized()
            return
        if path.startswith("/api/"):
            self._api_get(path)
        else:
            self._serve_static(path)

    def _api_get(self, path: str) -> None:
        sim = self.simulator

        # ── health ──────────────────────────────────────────────
        if path == "/api/health":
            self._json({"status": "ok"})
            return

        # ── nodes ───────────────────────────────────────────────
        if path == "/api/nodes":
            if sim is None:
                self.send_error(503, "Simulator not ready")
                return
            self._json(sim.get_full_state())
            return

        # ── values (lightweight poll) ───────────────────────────
        if path == "/api/values":
            if sim is None:
                self.send_error(503, "Simulator not ready")
                return
            self._json(sim.get_nodes_snapshot()["current_vals"])
            return

        # ── strategies ──────────────────────────────────────────
        if path == "/api/strategies":
            if sim is None:
                self.send_error(503, "Simulator not ready")
                return
            self._json(sim.get_strategies())
            return

        # ── model export ────────────────────────────────────────
        if path == "/api/model/export":
            if sim is None or sim.get_model() is None:
                self.send_error(503, "No model loaded")
                return
            model = sim.get_model()
            assert model is not None
            data = {
                "separator": model.separator,
                "groups": {gk: gi.node_ids for gk, gi in model.groups.items()},
                "nodes": {nid: node_meta_to_dict(m) for nid, m in model.nodes.items()},
            }
            self._json(data)
            return

        self.send_error(404, f"Unknown API endpoint: {path}")

    # -- POST ------------------------------------------------------------

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if not self._check_auth(path):
            self._send_unauthorized()
            return
        sim = self.simulator

        if path == "/api/model/upload":
            self._handle_upload()
            return

        if sim is None:
            self.send_error(503, "Simulator not ready")
            return

        body = _parse_json_body(self)
        if body is None:
            return

        # ── set_mode ────────────────────────────────────────────
        if path == "/api/set_mode":
            missing = _require_fields(body, "unique_key", "mode")
            if missing:
                self.send_error(400, f"Missing field: {missing}")
                return
            if body["mode"] not in ("random", "manual"):
                self.send_error(400, "mode must be 'random' or 'manual'")
                return
            if sim.set_mode(body["unique_key"], body["mode"]):
                self._json({"ok": True})
            else:
                self.send_error(404, "Node not found")
            return

        # ── set_value ───────────────────────────────────────────
        if path == "/api/set_value":
            missing = _require_fields(body, "unique_key", "value")
            if missing:
                self.send_error(400, f"Missing field: {missing}")
                return
            try:
                value = float(body["value"])
            except (ValueError, TypeError):
                self.send_error(400, "value must be a number")
                return
            if sim.set_value(body["unique_key"], value):
                self._json({"ok": True})
            else:
                self.send_error(404, "Node not found")
            return

        # ── set_all_mode ────────────────────────────────────────
        if path == "/api/set_all_mode":
            mode = body.get("mode")
            if mode not in ("random", "manual"):
                self.send_error(400, "mode must be 'random' or 'manual'")
                return
            sim.set_all_mode(mode)
            self._json({"ok": True})
            return

        self.send_error(404, f"Unknown API endpoint: {path}")

    # -- PATCH (node meta) -----------------------------------------------

    def do_PATCH(self) -> None:
        path = urlparse(self.path).path
        if not self._check_auth(path):
            self._send_unauthorized()
            return
        sim = self.simulator

        if sim is None:
            self.send_error(503, "Simulator not ready")
            return

        body = _parse_json_body(self)
        if body is None:
            return

        # ── /api/nodes/{node_id}/meta ───────────────────────────
        prefix = "/api/nodes/"
        suffix = "/meta"
        if path.startswith(prefix) and path.endswith(suffix):
            node_id = path[len(prefix) : -len(suffix)]
            if not node_id:
                self.send_error(400, "Missing node_id in URL")
                return
            if sim.update_node_meta(node_id, body):
                self._json({"ok": True, "node_id": node_id})
            else:
                self.send_error(404, f"Node not found: {node_id}")
            return

        # ── /api/nodes/batch ────────────────────────────────────
        if path == "/api/nodes/batch":
            updates = body if isinstance(body, list) else body.get("updates", [])
            if not isinstance(updates, list):
                self.send_error(400, "Expected a JSON array of updates")
                return
            result = sim.batch_update(updates)
            self._json(result)
            return

        self.send_error(404, f"Unknown API endpoint: {path}")

    # -- File upload -----------------------------------------------------

    def _handle_upload(self) -> None:
        """Handle Excel file upload via multipart/form-data or JSON body."""
        content_type = self.headers.get("Content-Type", "")

        if "multipart/form-data" in content_type:
            self._handle_multipart_upload()
            return

        # JSON body with file_path
        body = _parse_json_body(self)
        if body is None:
            return
        file_path = body.get("file_path", "")
        if not file_path:
            self.send_error(400, "Missing 'file_path' in JSON body")
            return
        self._load_model_from_path(file_path)

    def _handle_multipart_upload(self) -> None:
        """Parse multipart/form-data without the deprecated ``cgi`` module.

        Saves the uploaded file with a sanitized basename (no directory
        components) under ``UPLOAD_DIR`` and loads the model from it.
        """
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            self.send_error(400, "Empty upload")
            return
        if content_length > MAX_REQUEST_BYTES:
            self.send_error(413, "Upload too large")
            return

        try:
            body = self.rfile.read(content_length)
        except Exception:
            self.send_error(400, "Failed to read upload body")
            return

        try:
            filename, file_bytes = _parse_multipart_file(
                body, self.headers.get("Content-Type", "")
            )
        except ValueError as exc:
            self.send_error(400, str(exc))
            return

        # Sanitize filename — only basename, no directory traversal
        safe_name = Path(filename).name or "uploaded.xlsx"
        if not safe_name.lower().endswith((".xlsx", ".xlsm")):
            self.send_error(400, "Only .xlsx / .xlsm files are accepted")
            return

        UPLOAD_DIR.mkdir(exist_ok=True)
        dest = UPLOAD_DIR / safe_name
        # Avoid clobbering existing files with colliding names
        if dest.exists():
            stem, suffix = safe_name.rsplit(".", 1)
            dest = UPLOAD_DIR / f"{stem}_{int(time.time())}.{suffix}"
        dest.write_bytes(file_bytes)

        self._load_model_from_path(str(dest))

    def _load_model_from_path(self, file_path: str) -> None:
        """Load model from an Excel file path, validate, and reload."""
        sim = self.simulator
        if sim is None:
            self.send_error(503, "Simulator not ready")
            return

        target = Path(file_path)
        if not _is_path_allowed(target):
            self.send_error(
                403,
                "file_path must be inside the simulator or project root directory",
            )
            return
        if not target.exists() or not target.is_file():
            self.send_error(404, f"File not found: {file_path}")
            return

        try:
            nodes, warnings = read_model_excel(str(target))
            model = build_device_model(nodes)
            sim.reload_model(model)

            result = {
                "ok": True,
                "node_count": len(model.nodes),
                "group_count": len(model.groups),
                "groups": list(model.groups.keys()),
                "warnings": warnings,
            }
            self._json(result)
            log.info(
                "Model loaded from %s: %d nodes, %d groups",
                target,
                len(model.nodes),
                len(model.groups),
            )
        except Exception as exc:
            log.exception("Failed to load model from %s", target)
            self._json({"ok": False, "error": str(exc)}, status=400)

    # -- Static files ----------------------------------------------------

    def _serve_static(self, path: str) -> None:
        if path == "/":
            path = "/index.html"
        content = read_dist(path)
        if content is not None:
            ext = Path(path).suffix
            mime = MIME_TYPES.get(ext, "application/octet-stream")
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self._cors()
            self.end_headers()
            self.wfile.write(content)
            return
        # SPA fallback
        content = read_dist("index.html")
        if content is not None:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self._cors()
            self.end_headers()
            self.wfile.write(content)
            return
        self.send_error(404, "Not found")

    # -- Helpers ---------------------------------------------------------

    def _json(self, data: Any, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: Any) -> None:
        log.debug(fmt % args)
