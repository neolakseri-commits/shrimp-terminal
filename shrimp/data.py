"""Fixture data loading.

For now Shrimp Terminal ships with a small recorded sample under data/fixtures/
so the terminal runs, and looks alive, with zero setup and no RPC keys. A live
Robinhood Chain adapter (Alchemy / public RPC / indexer) plugs in behind the
same functions later - the rest of the app never learns where the rows came from.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from . import sample
from .models import FlowSource, InflowRow, Rotation, RouteEdge, Sequence, Trade

_FIXTURES = Path(__file__).resolve().parent.parent / "data" / "fixtures"


def _load(name: str) -> list[dict]:
    path = _FIXTURES / name
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_trades() -> list[Trade]:
    rows = _load("trades.json")
    trades = [
        Trade(
            wallet=r["wallet"],
            side=r["side"],
            coin=r["coin"],
            amount=float(r["amount"]),
            usdc=float(r["usdc"]),
            venue=r["venue"],
            block=int(r["block"]),
            ts=datetime.fromisoformat(r["ts"]),
            tx=r["tx"],
        )
        for r in rows
    ]
    trades.sort(key=lambda t: t.ts)
    return trades


def load_rotations() -> list[Rotation]:
    rows = _load("rotations.json")
    return [
        Rotation(
            wallet=r["wallet"],
            sold=r["sold"],
            bought=r["bought"],
            gap_s=int(r["gap_s"]),
            grade=r["grade"],
            sell_tx=r["sell_tx"],
            buy_tx=r["buy_tx"],
            also_sold=tuple(r.get("also_sold", ())),
        )
        for r in rows
    ]


def load_inflow() -> list[InflowRow]:
    rows = _load("inflow.json")
    inflow = [
        InflowRow(
            coin=r["coin"],
            wallets_in=int(r["wallets_in"]),
            net_usdc=float(r["net_usdc"]),
            rotations_in=int(r["rotations_in"]),
            venue=r["venue"],
            score=int(r.get("score", 0)),
            pct_1h=float(r.get("pct_1h", 0.0)),
            source=r.get("source", ""),
            source_wallets=int(r.get("source_wallets", 0)),
            extra_sources=int(r.get("extra_sources", 0)),
        )
        for r in rows
    ]
    inflow.sort(key=lambda i: i.net_usdc, reverse=True)
    return inflow


# --- richer sample-backed views (tape / hero route / flow fan) ------------- #
def load_tape(n: int = 240) -> list[Sequence]:
    """A long, time-sorted tape of observed sequences for the streaming panel."""
    return sample.tape(n)


def hot_route() -> RouteEdge:
    """The single hottest route - the MAP hero."""
    return sample.hot_route()


def flow_sources(dest: str | None = None) -> list[FlowSource]:
    """Coins rotating into the chosen destination - the FLOW fan."""
    return sample.flow_sources(dest)
