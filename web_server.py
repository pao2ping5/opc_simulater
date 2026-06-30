"""
OPC Simulator — Generic Web Console & REST API
═══════════════════════════════════════════════
Serves the React SPA + provides a REST API for controlling OPC node metadata,
values, and model management (upload / export).  No industry-specific logic.

This module is now a thin entry point — actual logic lives in:
- ``config.py``        : paths, ports, env-driven settings, logging
- ``helpers.py``       : request parsing, multipart, path/auth helpers
- ``static.py``        : SPA static file serving
- ``api_handler.py``   : APIHandler class (REST endpoints + upload)
- ``simulator.py``     : GenericOPCSimulator (also used by server.py CLI)

Usage:  python web_server.py
"""
from __future__ import annotations

import os
import threading

from common import (
    build_device_model,
    load_model_state,
    read_model_excel,
    save_model_state,
)
from app_config import (
    DEFAULT_XLSX,
    STATE_FILE,
    WEB_HOST,
    WEB_PORT,
    API_TOKEN,
    CORS_ALLOWED_ORIGINS,
    SCRIPT_DIR,
    log,
)
from helpers import ThreadingHTTPServer
from api_handler import APIHandler
from simulator import GenericOPCSimulator

# Re-export public symbols used by tests / external callers via ``web_server.X``.
# After the refactor, the canonical homes are config/helpers/api_handler, but
# we keep backward-compatible aliases here so existing importers don't break.
from app_config import (  # noqa: F401  (re-export)
    MAX_REQUEST_BYTES,
    MODEL_PATH_ALLOWLIST,
    UPLOAD_DIR,
    PUBLIC_API_PATHS,
    CORS_ALLOWED_ORIGINS as _CORS,  # already imported above; alias to silence linter
)
from helpers import (  # noqa: F401  (re-export)
    MIME_TYPES,
    _consteq,
    _is_path_allowed,
    _parse_json_body,
    _parse_multipart_file,
    _require_fields,
)
from static import read_dist  # noqa: F401  (re-export)


def main() -> None:
    xlsx_path = os.environ.get("OPC_POINT_TABLE", str(DEFAULT_XLSX))

    # ── Load model ──────────────────────────────────────────────
    # Try saved state first, otherwise parse Excel
    model = load_model_state(STATE_FILE)
    if model is not None:
        log.info("Restored model state from %s: %d nodes, %d groups",
                 STATE_FILE, len(model.nodes), len(model.groups))
    else:
        log.info("Loading model from %s", xlsx_path)
        nodes, warnings = read_model_excel(xlsx_path)
        for w in warnings:
            log.warning("  %s", w)
        model = build_device_model(nodes)
        save_model_state(model, STATE_FILE)
        log.info("Parsed %d nodes across %d groups",
                 len(model.nodes), len(model.groups))

    # ── Start simulator ─────────────────────────────────────────
    sim = GenericOPCSimulator(state_file=STATE_FILE)
    sim.setup(model)

    opc_thread = threading.Thread(target=sim.run, daemon=True, name="opc-sim")
    opc_thread.start()

    APIHandler.simulator = sim

    # ── Start web server ────────────────────────────────────────
    httpd = ThreadingHTTPServer((WEB_HOST, WEB_PORT), APIHandler)
    log.info("Web console: http://%s:%d", WEB_HOST, WEB_PORT)
    if WEB_HOST == "127.0.0.1":
        log.info("  (loopback only; set OPC_WEB_HOST=0.0.0.0 to expose on LAN)")
    log.info("OPC server:  opc.tcp://localhost:14840")
    if CORS_ALLOWED_ORIGINS:
        log.info("CORS allowlist: %s", ",".join(CORS_ALLOWED_ORIGINS))
    else:
        log.info("CORS: same-origin only (no ACAO header)")
    if API_TOKEN:
        log.info("API auth: Bearer token enabled")
    else:
        log.info("API auth: DISABLED (set OPC_API_TOKEN to enable)")
    log.info("Press Ctrl+C to stop")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        sim.running = False
        httpd.shutdown()
        log.info("Shutdown complete")


if __name__ == "__main__":
    main()
