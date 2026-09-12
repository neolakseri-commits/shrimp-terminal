"""Deterministic demo dataset for the terminal.

The shipped fixtures (data/fixtures/*.json) are a tiny hand-checked core - the
worked example, the graded rotations. This module inflates them into a fuller,
*shaped-like-real* sample so the four views look alive on the first run: a long
tape of sequences, one hot route for the MAP hero, and the FLOW fan feeding it.

Everything here is generated with a fixed seed, so it is stable across runs and
across machines. It is a demo of the UI, not a record of the chain - the live
adapter replaces these functions coin-for-coin later.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

from .models import FlowSource, RouteEdge, Sequence

SEED = 7
WINDOW_MIN = 30
# A fixed clock so the sample is identical everywhere. The live adapter uses now().
WINDOW_END = datetime(2026, 9, 12, 17, 22, 57, tzinfo=UTC)

_COINS = [
    "TruffleHog·7b08", "Piecoin·1a01", "SCRAPS·9de2", "MINER·5ea6",
    "INFERNET·d7f0", "CAT·fd23", "PACKZ·4a8c", "FEEZ·0c19", "LUNAH·0070",
    "SAGA·03dc", "EYWA·d7b5", "AUTON·5eab", "CASHPIG·38d6", "egregore·11af",
    "PONSLAB·bdb0", "HIPPOX·77a2", "VLADIATOR·2e1d", "BUILDING·d5f2",
    "Harvest·03dc", "TGCOINS·9515",
]

# The single hottest route - the MAP hero, matching the worked example.
_HOT = RouteEdge(
    sold="Piecoin·1a01", bought="TruffleHog·7b08",
    sold_addr="0x6c36..1a01", bought_addr="0x4ad5..7b08",
    wallets=54, rows=597, ambiguous=0, extra_seq=13,
)

# The FLOW fan: coins rotating into the hot destination, biggest first.
_FLOW = [
    FlowSource("Piecoin·1a01", 54, "clean"),
    FlowSource("SCRAPS·9de2", 12, "clean"),
    FlowSource("AUTON·5eab", 7, "clean"),
    FlowSource("egregore·11af", 4, "clean"),
    FlowSource("credit·13aa", 3, "clean"),
]


def _hex(rng: random.Random, n: int) -> str:
    return "".join(rng.choice("0123456789abcdef") for _ in range(n))


def hot_route() -> RouteEdge:
    return _HOT


def flow_sources(_dest: str | None = None) -> list[FlowSource]:
    return list(_FLOW)


def tape(n: int = 240) -> list[Sequence]:
    """A time-sorted tape of observed sequences over the replay window."""
    rng = random.Random(SEED)
    start = WINDOW_END - timedelta(minutes=WINDOW_MIN)
    span = (WINDOW_END - start).total_seconds()
    seqs: list[Sequence] = []
    for _ in range(n):
        ts = start + timedelta(seconds=rng.uniform(0, span))
        if rng.random() < 0.42:  # bias many rows onto the hot route
            sold, bought = _HOT.sold, _HOT.bought
        else:
            sold, bought = rng.sample(_COINS, 2)
        grade = rng.choices(["clean", "direct", "ambiguous"], weights=[80, 8, 12])[0]
        seqs.append(Sequence(
            ts=ts, wallet="0x" + _hex(rng, 40), sold=sold, bought=bought, grade=grade,
        ))
    seqs.sort(key=lambda s: s.ts)
    return seqs
