"""Integration tests for the GenericOPCSimulator class.

Covers:
- setup: address space built from a DeviceModel
- update_values: tick produces typed values (bool/int/string/float)
- mode switching: random → manual, manual value preserved
- set_value auto-switches to manual
- set_all_mode
- get_nodes_snapshot / get_full_state shape
- update_node_meta / batch_update (with and without state_file)
- reload_model: clears and rebuilds
"""
import random
from pathlib import Path

import pytest

from common import (
    DeviceModel,
    GroupInfo,
    NodeMeta,
    build_device_model,
)
from simulator import GenericOPCSimulator


@pytest.fixture
def small_model():
    nodes = [
        NodeMeta(node_id="A.B.temp", data_type="float", range_lo=0, range_hi=100, unit="C"),
        NodeMeta(node_id="A.B.switch", data_type="bool"),
        NodeMeta(node_id="A.C.counter", data_type="int", range_lo=0, range_hi=1000),
        NodeMeta(node_id="A.C.label", data_type="string"),
    ]
    return build_device_model(nodes)


@pytest.fixture
def sim(small_model):
    s = GenericOPCSimulator()
    s.setup(small_model)
    import time
    s._start_time = time.time()
    return s


# ── setup ───────────────────────────────────────────────────────────


def test_setup_creates_all_nodes(sim, small_model):
    assert len(sim._nodes) == len(small_model.nodes)
    for nid in small_model.nodes:
        assert nid in sim._nodes
        assert nid in sim._modes
        assert nid in sim._manual_vals
        assert nid in sim._current_vals


def test_setup_initial_modes_are_random(sim):
    for mode in sim._modes.values():
        assert mode == "random"


def test_setup_groups_match_model(sim, small_model):
    assert set(sim._model.groups.keys()) == set(small_model.groups.keys())


# ── update_values ───────────────────────────────────────────────────


def test_update_values_produces_typed_snapshots(sim):
    sim.update_values()
    assert sim.tick == 1
    assert isinstance(sim._current_vals["A.B.temp"], float)
    assert isinstance(sim._current_vals["A.B.switch"], bool)
    assert isinstance(sim._current_vals["A.C.counter"], int)
    assert isinstance(sim._current_vals["A.C.label"], str)


def test_update_values_in_range(sim):
    random.seed(0)
    for _ in range(10):
        sim.update_values()
    assert 0.0 <= sim._current_vals["A.B.temp"] <= 100.0
    assert 0 <= sim._current_vals["A.C.counter"] <= 1000
    assert sim._current_vals["A.B.switch"] in (True, False)


def test_update_values_advances_tick(sim):
    assert sim.tick == 0
    sim.update_values()
    assert sim.tick == 1
    sim.update_values()
    assert sim.tick == 2


# ── Mode / value control ────────────────────────────────────────────


def test_set_mode_to_manual(sim):
    assert sim.set_mode("A.B.temp", "manual") is True
    assert sim._modes["A.B.temp"] == "manual"


def test_set_mode_unknown_node(sim):
    assert sim.set_mode("DOES.NOT.EXIST", "manual") is False


def test_set_value_switches_to_manual(sim):
    assert sim.set_value("A.B.temp", 42.5) is True
    assert sim._modes["A.B.temp"] == "manual"
    assert sim._manual_vals["A.B.temp"] == 42.5


def test_set_value_then_tick_preserves_manual(sim):
    sim.set_value("A.B.temp", 42.5)
    sim.update_values()
    # Manual value should be preserved as a float in snapshot
    assert sim._current_vals["A.B.temp"] == 42.5


def test_set_value_unknown_node(sim):
    assert sim.set_value("NOPE", 1.0) is False


def test_set_all_mode(sim):
    sim.set_all_mode("manual")
    assert all(m == "manual" for m in sim._modes.values())
    sim.set_all_mode("random")
    assert all(m == "random" for m in sim._modes.values())


# ── Snapshots ───────────────────────────────────────────────────────


def test_get_nodes_snapshot_returns_current_vals(sim):
    sim.update_values()
    snap = sim.get_nodes_snapshot()
    assert "current_vals" in snap
    assert len(snap["current_vals"]) == len(sim._nodes)


def test_get_full_state_shape(sim):
    sim.update_values()
    state = sim.get_full_state()
    assert len(state) == len(sim._model.groups)
    for group in state:
        assert "key" in group
        assert "label" in group
        assert "nodes" in group
        for n in group["nodes"]:
            assert "node_id" in n
            assert "mode" in n
            assert "value" in n
            assert "manual" in n


def test_get_full_state_empty_when_no_model():
    sim = GenericOPCSimulator()
    assert sim.get_full_state() == []


# ── Metadata updates ────────────────────────────────────────────────


def test_update_node_meta_changes_field(sim):
    assert sim.update_node_meta("A.B.temp", {"unit": "F"}) is True
    assert sim._model.nodes["A.B.temp"].unit == "F"


def test_update_node_meta_unknown_node(sim):
    assert sim.update_node_meta("NOPE", {"unit": "X"}) is False


def test_update_node_meta_ignores_disallowed_field(sim):
    # node_id is not in the allowed set
    original_id = sim._model.nodes["A.B.temp"].node_id
    sim.update_node_meta("A.B.temp", {"node_id": "hacked"})
    assert sim._model.nodes["A.B.temp"].node_id == original_id


def test_batch_update_single_save(sim, tmp_path: Path):
    """When state_file is configured, batch_update should save once at the end."""
    sim._state_file = tmp_path / "state.json"
    result = sim.batch_update([
        {"node_id": "A.B.temp", "unit": "K"},
        {"node_id": "A.C.counter", "unit": "Hz"},
        {"node_id": "NONEXISTENT", "unit": "X"},
    ])
    assert result["ok"] == 2
    assert "NONEXISTENT" in result["failed"]
    assert sim._model.nodes["A.B.temp"].unit == "K"
    assert sim._model.nodes["A.C.counter"].unit == "Hz"
    # State file should exist (persistence happened)
    assert sim._state_file.exists()


def test_batch_update_no_state_file_skips_persistence(sim):
    """Without state_file, batch_update succeeds but doesn't touch disk."""
    result = sim.batch_update([{"node_id": "A.B.temp", "unit": "Z"}])
    assert result["ok"] == 1
    assert sim._model.nodes["A.B.temp"].unit == "Z"


def test_batch_update_invalid_item_recorded(sim):
    result = sim.batch_update([
        "not a dict",  # invalid
        {"node_id": "A.B.temp", "unit": "X"},
    ])
    assert result["ok"] == 1
    assert any("invalid" in f for f in result["failed"])


# ── reload_model ────────────────────────────────────────────────────


def test_reload_model_rebuilds(sim):
    new_nodes = [
        NodeMeta(node_id="X.Y.z", data_type="float"),
        NodeMeta(node_id="X.Y.w", data_type="int"),
    ]
    new_model = build_device_model(new_nodes)
    sim.reload_model(new_model)
    assert len(sim._nodes) == 2
    assert "X.Y.z" in sim._nodes
    assert "X.Y.w" in sim._nodes
    # Old nodes gone
    assert "A.B.temp" not in sim._nodes


def test_reload_model_resets_tick(sim):
    sim.update_values()
    sim.update_values()
    assert sim.tick == 2
    new_model = build_device_model([NodeMeta(node_id="X.y", data_type="float")])
    sim.reload_model(new_model)
    assert sim.tick == 0
