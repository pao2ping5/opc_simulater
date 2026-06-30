"""
Generic OPC UA Simulator
════════════════════════
Single source of truth for the :class:`GenericOPCSimulator` used by both
``web_server.py`` (HTTP console mode) and ``server.py`` (CLI mode).

Previous versions had two diverging copies (one with locks + manual mode +
API surface, one without).  Bugs fixed in one were silently absent from the
other.  This module is the merged, lock-protected, value-preserving version.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from opcua import Server, ua

from common import (
    DeviceModel,
    NodeMeta,
    StrategyRegistry,
    get_strategy_registry,
    node_meta_to_dict,
    save_model_state,
)

log = logging.getLogger("opc-sim")

# Default OPC UA endpoint — the local opcua.py mock does not actually listen
# on this URL, but the value is exposed via ``server.endpoint`` for logging.
DEFAULT_OPC_ENDPOINT = "opc.tcp://0.0.0.0:14840/freeopcua/server/"


class GenericOPCSimulator:
    """OPC UA server that simulates sensor values for any device model.

    Reads a :class:`DeviceModel`, creates the OPC UA address space from
    node_id hierarchies, and uses the :class:`StrategyRegistry` for
    value generation.

    Thread-safe: all public mutators acquire ``self._lock``.  ``run()``
    ticks values under the lock; HTTP handlers may concurrently call
    ``set_mode`` / ``set_value`` / ``get_full_state`` etc. without
    corrupting state.
    """

    def __init__(
        self,
        endpoint: str = DEFAULT_OPC_ENDPOINT,
        strategy_registry: Optional[StrategyRegistry] = None,
        state_file: Optional[Any] = None,
    ) -> None:
        """Create the simulator.

        Parameters
        ----------
        endpoint:
            OPC UA endpoint URL (informational when using the local mock).
        strategy_registry:
            Optional custom strategy registry; defaults to the global singleton.
        state_file:
            Optional path to persist model state to via ``save_model_state``.
            When set, ``reload_model`` / ``update_node_meta`` / ``batch_update``
            will write to this file.  When ``None`` (CLI mode), persistence
            is skipped entirely.
        """
        self.server = Server()
        self.server.set_endpoint(endpoint)
        self.server.set_server_name("Generic OPC Simulator")

        self._strategy = strategy_registry or get_strategy_registry()
        self._state_file = state_file

        # node_id → (NodeMeta, ua.Node)
        self._nodes: Dict[str, Tuple[NodeMeta, ua.Node]] = {}
        # node_id → mode ("random" | "manual")
        self._modes: Dict[str, str] = {}
        # node_id → manual value
        self._manual_vals: Dict[str, float] = {}
        # node_id → current value snapshot (preserves actual typed value,
        # including strings/bools — not just floats)
        self._current_vals: Dict[str, Any] = {}

        self._model: Optional[DeviceModel] = None
        self.tick: int = 0
        self.running: bool = True
        self._lock = threading.Lock()
        self._start_time: float = 0.0

    # -- Setup ----------------------------------------------------------

    def setup(self, model: DeviceModel) -> None:
        """Create OPC UA address space from a :class:`DeviceModel`.

        The address space mirrors the node_id hierarchy.  Each dot-segment
        becomes a Folder, the leaf becomes a Variable.
        """
        self._model = model
        uri = "http://generic.opc.simulator"
        idx = self.server.register_namespace(uri)
        objects = self.server.get_objects_node()

        # Cache intermediate folders by full path to avoid duplicate creation
        # (server.py's one good idea, ported here).
        folder_cache: Dict[str, ua.Node] = {}
        group_folders: Dict[str, ua.Node] = {}
        for gk in model.groups:
            group_folders[gk] = objects.add_folder(idx, gk)
            folder_cache[gk] = group_folders[gk]

        for nid, meta in model.nodes.items():
            parent = group_folders.get(meta.group_key, objects)

            # Walk intermediate segments between group_depth and the leaf,
            # creating folders as needed (cached by full path).
            parts = meta.parts
            for depth in range(meta.group_depth + 1, len(parts)):
                folder_path = ".".join(parts[:depth])
                if folder_path not in folder_cache:
                    parent_key = ".".join(parts[: depth - 1])
                    parent_node = folder_cache.get(parent_key, objects)
                    folder_cache[folder_path] = parent_node.add_folder(
                        idx, parts[depth - 1]
                    )
                parent = folder_cache[folder_path]

            # Pick OPC UA variant type
            if meta.data_type == "bool":
                variant_type = ua.VariantType.Boolean
                initial: Any = False
            elif meta.data_type == "int":
                variant_type = ua.VariantType.Int32
                initial = 0
            elif meta.data_type == "string":
                variant_type = ua.VariantType.String
                initial = ""
            else:  # float (default)
                variant_type = ua.VariantType.Double
                initial = 0.0

            node = parent.add_variable(
                ua.NodeId(nid, idx),
                meta.effective_display_name,
                initial,
                variant_type,
            )
            node.set_writable()

            self._nodes[nid] = (meta, node)
            self._modes[nid] = "random"
            self._manual_vals[nid] = 0.0
            self._current_vals[nid] = initial

        log.info(
            "OPC address space created: %d nodes across %d groups",
            len(self._nodes),
            len(model.groups),
        )

    # -- Tick -----------------------------------------------------------

    def update_values(self) -> None:
        """Advance simulation one tick.  Called from the simulator thread."""
        elapsed = time.time() - self._start_time
        with self._lock:
            for nid, (meta, node) in self._nodes.items():
                try:
                    if self._modes.get(nid) == "manual":
                        val: Any = self._manual_vals.get(nid, 0.0)
                    else:
                        raw = self._strategy.generate(
                            meta,
                            self._current_vals.get(nid, 0.0),
                            elapsed,
                            self.tick,
                        )
                        val = raw
                    # Write to OPC node with proper type
                    if meta.data_type == "bool":
                        node.set_value(bool(val))
                        snapshot_val: Any = bool(val)
                    elif meta.data_type == "int":
                        node.set_value(int(val))
                        snapshot_val = int(val)
                    elif meta.data_type == "string":
                        node.set_value(str(val))
                        snapshot_val = str(val)
                    else:
                        node.set_value(float(val))
                        snapshot_val = float(val)
                    self._current_vals[nid] = snapshot_val
                except Exception:
                    log.exception("Failed to update value for %s", nid)
            self.tick += 1

    def run(self, tick_interval: float = 2.0) -> None:
        """Main simulation loop (runs in a daemon thread).

        ``tick_interval`` defaults to 2 seconds, matching the historical
        behavior.  CLI mode can pass a different value.
        """
        self._start_time = time.time()
        self.server.start()
        log.info("OPC server started at %s", self.server.endpoint)
        try:
            while self.running:
                self.update_values()
                time.sleep(tick_interval)
        except KeyboardInterrupt:
            pass
        finally:
            self.server.stop()
            log.info("OPC server stopped")

    # -- Model-level operations -----------------------------------------

    def reload_model(self, model: DeviceModel) -> None:
        """Stop current OPC server, rebuild address space, restart."""
        was_running = self.running
        self.running = False
        self.server.stop()

        # Re-init
        self.server = Server()
        self.server.set_endpoint(DEFAULT_OPC_ENDPOINT)
        self.server.set_server_name("Generic OPC Simulator")

        self._nodes.clear()
        self._modes.clear()
        self._manual_vals.clear()
        self._current_vals.clear()
        self.tick = 0

        self.setup(model)
        if self._state_file is not None:
            save_model_state(model, self._state_file)

        if was_running:
            self.running = True
            self._start_time = time.time()
            self.server.start()
            log.info("OPC server restarted with new model")

    # -- Thread-safe public API (used by HTTP handler) ------------------

    def get_model(self) -> Optional[DeviceModel]:
        return self._model

    def get_nodes_snapshot(self) -> Dict[str, Any]:
        """Thread-safe snapshot for /api/values."""
        with self._lock:
            return {"current_vals": dict(self._current_vals)}

    def get_full_state(self) -> List[Dict[str, Any]]:
        """Return full model data merged with live values for /api/nodes.

        Snapshot of model.groups / model.nodes is taken under the same lock
        that ``reload_model`` mutates, so we never iterate a dict that is
        being swapped out from under us.
        """
        with self._lock:
            if self._model is None:
                return []
            modes = dict(self._modes)
            current = dict(self._current_vals)
            manual = dict(self._manual_vals)
            groups_snapshot = list(self._model.groups.items())
            nodes_snapshot = dict(self._model.nodes)

        result: List[Dict[str, Any]] = []
        for gk, gi in groups_snapshot:
            nodes_out: List[Dict[str, Any]] = []
            for nid in gi.node_ids:
                meta = nodes_snapshot.get(nid)
                if meta is None:
                    continue
                node_data = node_meta_to_dict(meta)
                node_data.update(
                    mode=modes.get(nid, "random"),
                    value=current.get(nid, 0.0),
                    manual=manual.get(nid, 0.0),
                )
                nodes_out.append(node_data)
            result.append({"key": gk, "label": gi.label, "nodes": nodes_out})

        return result

    def get_strategies(self) -> List[Dict[str, str]]:
        return self._strategy.list_all()

    # -- Per-node operations (thread-safe) ------------------------------

    def set_mode(self, node_id: str, mode: str) -> bool:
        with self._lock:
            if node_id in self._modes:
                self._modes[node_id] = mode
                return True
            return False

    def set_value(self, node_id: str, value: float) -> bool:
        with self._lock:
            if node_id in self._manual_vals:
                self._manual_vals[node_id] = value
                self._modes[node_id] = "manual"
                return True
            return False

    def set_all_mode(self, mode: str) -> None:
        with self._lock:
            for key in self._modes:
                self._modes[key] = mode

    def update_node_meta(self, node_id: str, updates: Dict[str, Any]) -> bool:
        """Update metadata fields of a node.  Returns True if found.

        Acquires the lock, applies the changes, and persists once (when
        ``state_file`` is configured).
        """
        if self._model is None or node_id not in self._model.nodes:
            return False

        meta = self._model.nodes[node_id]
        allowed = {
            "data_type",
            "range_lo",
            "range_hi",
            "unit",
            "gen_strategy",
            "gen_params",
            "description",
            "display_name",
        }
        changed = False
        with self._lock:
            for key, val in updates.items():
                if key not in allowed:
                    continue
                if hasattr(meta, key):
                    setattr(meta, key, val)
                    changed = True
            if changed and self._state_file is not None:
                save_model_state(self._model, self._state_file)
        return changed

    def batch_update(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply a batch of meta updates in a single lock+save cycle.

        Single lock acquisition, single save at the end (when configured).
        """
        if self._model is None:
            return {
                "ok": 0,
                "failed": [str(u.get("node_id", "(missing)")) for u in updates],
            }

        allowed = {
            "data_type",
            "range_lo",
            "range_hi",
            "unit",
            "gen_strategy",
            "gen_params",
            "description",
            "display_name",
        }
        ok = 0
        failed: List[str] = []
        any_changed = False

        with self._lock:
            for item in updates:
                if not isinstance(item, dict):
                    failed.append("(invalid item)")
                    continue
                nid = item.get("node_id")
                if not nid or nid not in self._model.nodes:
                    failed.append(nid or "(missing)")
                    continue
                meta = self._model.nodes[nid]
                item_changed = False
                for key, val in item.items():
                    if key in allowed and hasattr(meta, key):
                        setattr(meta, key, val)
                        item_changed = True
                if item_changed:
                    any_changed = True
                    ok += 1
                else:
                    failed.append(nid)
            if any_changed and self._state_file is not None:
                save_model_state(self._model, self._state_file)

        return {"ok": ok, "failed": failed}
