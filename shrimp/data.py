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

from .models import InflowRow, Rotation, Trade

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
        )
        for r in rows
    ]
    inflow.sort(key=lambda i: i.net_usdc, reverse=True)
    return inflow
