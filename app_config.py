"""Configuration for the OPC Simulator web server.

All path/host/port/CORS/auth constants live here so they can be imported
by ``helpers.py``, ``static.py``, ``api_handler.py``, and ``web_server.py``
without circular dependencies.

Most values are overridable via environment variables for containerized
or production deployments.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Filesystem locations
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
DIST_DIR = SCRIPT_DIR / "frontend" / "dist"
DEFAULT_XLSX = SCRIPT_DIR.parent / "opc_list_test.xlsx"
STATE_FILE = SCRIPT_DIR / "model_state.json"
UPLOAD_DIR = SCRIPT_DIR / "uploads"

# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------

WEB_PORT = 18480

# Bind address: default 127.0.0.1 (loopback only).  Set OPC_WEB_HOST=0.0.0.0
# in the environment to expose on all interfaces (e.g. containerized deploy).
WEB_HOST = os.environ.get("OPC_WEB_HOST", "127.0.0.1")

# ---------------------------------------------------------------------------
# Request limits
# ---------------------------------------------------------------------------

# Request body size limit (10 MB) — guards against OOM via oversized uploads
MAX_REQUEST_BYTES = 10 * 1024 * 1024

# Where file_path-based model loads may read from.  Absolute paths outside
# this allowlist are rejected.
MODEL_PATH_ALLOWLIST: tuple[Path, ...] = (SCRIPT_DIR, SCRIPT_DIR.parent)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

# Default: same-origin only (no ACAO header sent).
# Set OPC_CORS_ORIGIN=http://example.com to allow a specific origin,
# or OPC_CORS_ORIGIN=* to restore the old wide-open behavior (not recommended
# for industrial control networks).
_CORS_ORIGIN_ENV = os.environ.get("OPC_CORS_ORIGIN", "")
CORS_ALLOWED_ORIGINS: tuple[str, ...] = tuple(
    o.strip() for o in _CORS_ORIGIN_ENV.split(",") if o.strip()
)

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

# Optional static API token.  When set, all /api/* endpoints except
# /api/health require ``Authorization: Bearer <token>``.  Default empty →
# no auth (same-origin + loopback bind is the only protection).  Set
# OPC_API_TOKEN=<some-random-string> in the environment to enable.
API_TOKEN = os.environ.get("OPC_API_TOKEN", "")

# Endpoints that bypass token auth (health probe, login probe).
PUBLIC_API_PATHS = {"/api/health"}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger("opc-sim")
