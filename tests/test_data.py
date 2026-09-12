"""Fixtures load and the grading rules behave as documented."""

from __future__ import annotations

from shrimp import data
from shrimp.models import InflowRow, Rotation, SmartWallet, Trade, Whale


def test_trades_load_and_are_time_sorted():
    trades = data.load_trades()
    assert trades, "fixture trades must not be empty"
    assert all(isinstance(t, Trade) for t in trades)
    assert trades == sorted(trades, key=lambda t: t.ts)


def test_trade_helpers_are_readable():
    t = data.load_trades()[0]
    assert ":" in t.ts_hhmmss  # HH:MM:SS
    assert "..." in t.tx_short


def test_rotations_load_with_valid_grades():
    rotations = data.load_rotations()
    assert rotations
    valid = {"direct", "clean", "ambiguous"}
    assert all(isinstance(r, Rotation) for r in rotations)
    assert all(r.grade in valid for r in rotations)


def test_ambiguous_rotation_lists_but_isolates_extra_sells():
    rotations = data.load_rotations()
    ambiguous = [r for r in rotations if r.grade == "ambiguous"]
    assert ambiguous, "sample should include an ambiguous case"
    # An ambiguous rotation must actually name the other coins it sold.
    assert all(r.also_sold for r in ambiguous)


def test_clean_rotation_sold_nothing_else():
    rotations = data.load_rotations()
    clean = [r for r in rotations if r.grade == "clean"]
    assert clean
    assert all(r.also_sold == () for r in clean)


def test_whales_are_ranked_descending_by_net_24h():
    whales = data.load_whales()
    assert whales
    assert all(isinstance(w, Whale) for w in whales)
    values = [w.net_24h for w in whales]
    assert values == sorted(values, reverse=True)
    assert all(w.tag in {"mega", "orca", "shark"} for w in whales)


def test_smart_money_is_ranked_descending_by_pnl_and_win_pct_in_range():
    smart = data.load_smart()
    assert smart
    assert all(isinstance(s, SmartWallet) for s in smart)
    values = [s.pnl_usdc for s in smart]
    assert values == sorted(values, reverse=True)
    assert all(0 <= s.win_pct <= 100 for s in smart)


def test_samples_are_deterministic():
    assert data.load_whales() == data.load_whales()
    assert data.load_smart() == data.load_smart()


def test_inflow_is_ranked_descending_by_net_usdc():
    inflow = data.load_inflow()
    assert inflow
    assert all(isinstance(i, InflowRow) for i in inflow)
    values = [i.net_usdc for i in inflow]
    assert values == sorted(values, reverse=True)
