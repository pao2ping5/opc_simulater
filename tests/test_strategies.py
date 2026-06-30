"""Tests for value-generation strategies in ``common.py``.

Covers:
- Each built-in strategy returns a value in range
- Edge cases: hi==lo, step_ratio=0, hi<lo, step=0 (previous ZeroDivisionError)
- Type coercion for bool / int / string / float
- StrategyRegistry.resolve() default selection per data_type
"""

import random

import pytest

from common import (
    NodeMeta,
    StrategyRegistry,
    _make_counter,
    _make_normal,
    _make_pressure,
    _make_ramp,
    _make_random_walk,
    _make_sinusoidal,
    _make_uniform,
    get_strategy_registry,
)


# ── Strategy return values stay in range ────────────────────────────


@pytest.mark.parametrize(
    "strategy_fn",
    [
        _make_uniform,
        _make_normal,
        _make_sinusoidal,
        _make_random_walk,
        _make_pressure,
    ],
)
def test_strategy_returns_value_in_range(strategy_fn):
    lo, hi = 10.0, 20.0
    random.seed(42)
    for _ in range(50):
        val = strategy_fn(lo, hi, {}, 15.0, 0.0, 0)
        assert lo <= val <= hi, (
            f"{strategy_fn.__name__} returned {val} out of [{lo}, {hi}]"
        )


# ── Division-by-zero edge cases (previously crashes) ────────────────


def test_ramp_hi_eq_lo_returns_lo():
    """hi == lo used to make step = 0 → ZeroDivisionError."""
    assert _make_ramp(50.0, 50.0, {}, 0, 0, 5) == 50.0


def test_ramp_step_ratio_zero_returns_lo():
    """step_ratio = 0 used to make step = 0 → ZeroDivisionError."""
    assert _make_ramp(0.0, 100.0, {"step_ratio": 0}, 0, 0, 5) == 0.0


def test_counter_hi_lt_lo_returns_lo():
    """hi < lo used to make modulus = hi - lo + step possibly 0 or negative."""
    assert _make_counter(100.0, 50.0, {"step": 1.0}, 0, 0, 5) == 100.0


def test_counter_step_zero_returns_lo():
    """step = 0 used to make modulus = hi - lo."""
    assert _make_counter(0.0, 100.0, {"step": 0}, 0, 0, 5) == 0.0


def test_ramp_normal_progression():
    """Sanity: ramp with reasonable params walks from lo upward."""
    val = _make_ramp(0.0, 100.0, {"step_ratio": 0.1}, 0, 0, 0)
    assert val == 0.0
    val = _make_ramp(0.0, 100.0, {"step_ratio": 0.1}, 0, 0, 5)
    assert val == 50.0


def test_counter_normal_progression():
    val = _make_counter(0.0, 10.0, {"step": 1.0}, 0, 0, 5)
    assert val == 5.0
    # Wraps at modulus
    val = _make_counter(0.0, 10.0, {"step": 1.0}, 0, 0, 11)
    assert val == 0.0  # (11 * 1) % 11 == 0


# ── StrategyRegistry.generate type coercion ────────────────────────


def _make_registry():
    return StrategyRegistry()


def test_generate_float_rounds_to_3_decimals():
    reg = _make_registry()
    node = NodeMeta(node_id="x", data_type="float", range_lo=0, range_hi=100)
    val = reg.generate(node, 0.0, 0.0, 0)
    assert isinstance(val, float)
    # 3 decimal places max
    assert round(val, 3) == val


def test_generate_int_returns_int():
    reg = _make_registry()
    node = NodeMeta(node_id="x", data_type="int", range_lo=0, range_hi=100)
    val = reg.generate(node, 0.0, 0.0, 0)
    assert isinstance(val, int)


def test_generate_bool_returns_0_or_1():
    reg = _make_registry()
    node = NodeMeta(node_id="x", data_type="bool")
    random.seed(0)
    vals = {reg.generate(node, 0, 0, 0) for _ in range(50)}
    assert vals.issubset({0, 1})


def test_generate_string_returns_str():
    reg = _make_registry()
    node = NodeMeta(
        node_id="x",
        data_type="string",
        gen_strategy="constant",
        gen_params={"value": 42.5},
    )
    val = reg.generate(node, 0, 0, 0)
    assert isinstance(val, str)
    assert "42" in val


# ── StrategyRegistry.resolve ───────────────────────────────────────


def test_resolve_explicit_strategy_wins():
    reg = _make_registry()
    node = NodeMeta(node_id="x", data_type="float", gen_strategy="sinusoidal")
    strat = reg.resolve(node)
    assert strat.name == "sinusoidal"


def test_resolve_defaults_per_data_type():
    reg = _make_registry()
    for dtype, expected in [
        ("bool", "binary_toggle"),
        ("string", "constant"),
        ("int", "random_uniform"),
        ("float", "random_uniform"),
    ]:
        node = NodeMeta(node_id="x", data_type=dtype)
        assert reg.resolve(node).name == expected


def test_resolve_unknown_strategy_falls_back_to_uniform():
    reg = _make_registry()
    node = NodeMeta(node_id="x", data_type="float", gen_strategy="nonexistent_strategy")
    assert reg.resolve(node).name == "random_uniform"


def test_get_strategy_registry_singleton():
    a = get_strategy_registry()
    b = get_strategy_registry()
    assert a is b


def test_list_all_returns_all_builtins():
    reg = _make_registry()
    names = {s["name"] for s in reg.list_all()}
    # Spot-check a few
    assert "random_uniform" in names
    assert "sinusoidal" in names
    assert "constant" in names
    assert "binary_toggle" in names
    assert len(names) >= 12  # 12 built-in strategies
