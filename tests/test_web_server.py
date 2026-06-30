"""Tests for web_server.py helper functions and security guards.

Covers:
- _parse_multipart_file: well-formed, missing boundary, no file part
- _is_path_allowed: inside / outside allowlist, symlink-ish edge cases
- _consteq: correct/wrong/empty token comparison, timing-safe
- _parse_json_body: would need a handler stub; covered indirectly
- APIHandler._check_auth: token present/absent, public paths, static paths
"""

from pathlib import Path

import pytest

import web_server
from web_server import (
    PUBLIC_API_PATHS,
    _consteq,
    _is_path_allowed,
    _parse_multipart_file,
)


# ── _parse_multipart_file ───────────────────────────────────────────


def _make_multipart(boundary: str, filename: str, content: bytes) -> bytes:
    return (
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: application/octet-stream\r\n"
            f"\r\n"
        ).encode("utf-8")
        + content
        + f"\r\n--{boundary}--\r\n".encode("utf-8")
    )


def test_parse_multipart_extracts_filename_and_bytes():
    body = _make_multipart("BNDRY", "data.xlsx", b"hello world")
    name, data = _parse_multipart_file(body, "multipart/form-data; boundary=BNDRY")
    assert name == "data.xlsx"
    assert data == b"hello world"


def test_parse_multipart_handles_quoted_boundary():
    body = _make_multipart("XYZ", "f.xlsx", b"data")
    name, data = _parse_multipart_file(body, 'multipart/form-data; boundary="XYZ"')
    assert name == "f.xlsx"
    assert data == b"data"


def test_parse_multipart_missing_boundary_raises():
    with pytest.raises(ValueError, match="boundary"):
        _parse_multipart_file(b"whatever", "multipart/form-data")


def test_parse_multipart_no_file_part_raises():
    body = (
        b"--BNDRY\r\n"
        b'Content-Disposition: form-data; name="text_field"\r\n'
        b"\r\n"
        b"some text\r\n"
        b"--BNDRY--\r\n"
    )
    with pytest.raises(ValueError, match="No file part"):
        _parse_multipart_file(body, "multipart/form-data; boundary=BNDRY")


def test_parse_multipart_filename_with_path_components_preserved_as_is():
    """Parser returns the filename as-is; sanitization happens in _handle_multipart_upload."""
    body = _make_multipart("B", "../../etc/passwd", b"x")
    name, _ = _parse_multipart_file(body, "multipart/form-data; boundary=B")
    # Parser doesn't sanitize — that's the caller's job
    assert name == "../../etc/passwd"


# ── _is_path_allowed ────────────────────────────────────────────────


def test_is_path_allowed_inside_simulator_dir():
    p = Path(web_server.SCRIPT_DIR) / "uploads" / "test.xlsx"
    assert _is_path_allowed(p) is True


def test_is_path_allowed_inside_parent_dir():
    p = Path(web_server.SCRIPT_DIR).parent / "opc_list_test.xlsx"
    assert _is_path_allowed(p) is True


def test_is_path_allowed_rejects_outside_paths():
    p = Path("C:/Windows/System32/drivers/etc/hosts")
    assert _is_path_allowed(p) is False


def test_is_path_allowed_rejects_nonexistent_root():
    p = Path("Z:/nonexistent/path/file.xlsx")
    assert _is_path_allowed(p) is False


# ── _consteq ────────────────────────────────────────────────────────


def test_consteq_equal_strings():
    assert _consteq("abc", "abc") is True


def test_consteq_different_strings():
    assert _consteq("abc", "xyz") is False


def test_consteq_different_lengths():
    assert _consteq("abc", "abcd") is False


def test_consteq_empty_strings():
    assert _consteq("", "") is True


def test_consteq_one_empty():
    assert _consteq("abc", "") is False


# ── APIHandler._check_auth ──────────────────────────────────────────


class _FakeHeaders:
    def __init__(self, headers):
        self._h = headers

    def get(self, key, default=""):
        return self._h.get(key, default)


class _FakeHandler:
    """Minimal stub matching what _check_auth needs."""

    def __init__(self, auth_header=None):
        self.headers = _FakeHeaders(
            {"Authorization": auth_header} if auth_header else {}
        )

    # Bind the real method
    _check_auth = web_server.APIHandler._check_auth


@pytest.fixture
def no_token_env(monkeypatch):
    """Force API_TOKEN to empty (default deployment).

    Patches both the web_server re-export and the api_handler module's
    binding (the latter is what ``_check_auth`` actually reads).
    """
    monkeypatch.setattr(web_server, "API_TOKEN", "")
    import api_handler

    monkeypatch.setattr(api_handler, "API_TOKEN", "")
    return web_server


@pytest.fixture
def token_env(monkeypatch):
    """Enable auth with a known token."""
    monkeypatch.setattr(web_server, "API_TOKEN", "secret-token-123")
    import api_handler

    monkeypatch.setattr(api_handler, "API_TOKEN", "secret-token-123")
    return web_server


def test_check_auth_no_token_enabled_allows_all(no_token_env):
    h = _FakeHandler()
    assert h._check_auth("/api/nodes") is True
    assert h._check_auth("/api/health") is True
    assert h._check_auth("/index.html") is True


def test_check_auth_token_enabled_health_bypasses(token_env):
    h = _FakeHandler()  # no Authorization header
    assert h._check_auth("/api/health") is True


def test_check_auth_token_enabled_static_bypasses(token_env):
    h = _FakeHandler()
    assert h._check_auth("/index.html") is True
    assert h._check_auth("/api/nodes") is False  # API requires token


def test_check_auth_correct_bearer_token(token_env):
    h = _FakeHandler("Bearer secret-token-123")
    assert h._check_auth("/api/nodes") is True


def test_check_auth_wrong_bearer_token(token_env):
    h = _FakeHandler("Bearer wrong-token")
    assert h._check_auth("/api/nodes") is False


def test_check_auth_malformed_auth_header(token_env):
    h = _FakeHandler("secret-token-123")  # missing "Bearer " prefix
    assert h._check_auth("/api/nodes") is False
    h2 = _FakeHandler("Basic abc")
    assert h2._check_auth("/api/nodes") is False


def test_public_api_paths_includes_health():
    assert "/api/health" in PUBLIC_API_PATHS
