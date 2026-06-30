"""
OPC Simulator Test Client
━━━━━━━━━━━━━━━━━━━━━━━━
Queries the running OPC simulator's REST API and prints the address-space
tree with current values for all nodes.

The simulator's web server (web_server.py) is the only supported interface;
the local opcua.py is an in-process mock and does not expose an OPC UA wire
protocol, so a real OPC UA client cannot connect.

Usage:
    python test_client.py
    python test_client.py --endpoint http://localhost:18480
    python test_client.py --watch          # refresh every 2 seconds
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from urllib.error import URLError
from urllib.request import Request, urlopen


def _fetch_json(url: str, timeout: float = 10.0):
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=timeout) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} from {url}")
        return json.loads(resp.read().decode("utf-8"))


def render_tree(groups) -> list[str]:
    """Render the /api/nodes response as an indented tree."""
    lines: list[str] = []
    for group in groups:
        label = group.get("label") or group.get("key", "?")
        nodes = group.get("nodes", [])
        lines.append(f"{label}/  ({len(nodes)})")
        for n in nodes:
            name = (
                n.get("display_name")
                or (n.get("node_id", "").split(".")[-1])
                or n.get("node_id", "?")
            )
            value = n.get("value")
            unit = n.get("unit") or ""
            mode = n.get("mode", "?")
            unit_str = f" {unit}" if unit else ""
            lines.append(f"  {name} = {value}{unit_str}  [{mode}]")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="OPC Simulator Test Client (REST)")
    parser.add_argument(
        "--endpoint",
        default="http://localhost:18480",
        help="Web server base URL (default: %(default)s)",
    )
    parser.add_argument(
        "--watch", "-w",
        action="store_true",
        help="Poll values every 2 seconds (Ctrl+C to stop)",
    )
    args = parser.parse_args()

    base = args.endpoint.rstrip("/")
    nodes_url = f"{base}/api/nodes"
    health_url = f"{base}/api/health"

    def _show() -> None:
        try:
            groups = _fetch_json(nodes_url)
        except (URLError, RuntimeError) as exc:
            print(f"ERROR fetching {nodes_url}: {exc}")
            return
        if not groups:
            print("No nodes found — server may be empty or not ready.")
            return
        tree = render_tree(groups)
        for line in tree:
            print(line)

    # Connectivity probe
    try:
        _fetch_json(health_url)
    except (URLError, RuntimeError) as exc:
        print(f"ERROR: Could not reach {health_url}: {exc}")
        print("Is the simulator running? Try: python web_server.py")
        sys.exit(1)

    print(f"Connected to {base}")
    if args.watch:
        print("Watching values (Ctrl+C to stop)...")
        try:
            while True:
                print("\n" + "=" * 60)
                _show()
                time.sleep(2)
        except KeyboardInterrupt:
            print("\nStopped.")
    else:
        _show()


if __name__ == "__main__":
    main()
