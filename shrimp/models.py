"""Core data types for Shrimp Terminal.

Everything the terminal shows resolves to these observed, checkable facts:
a Trade (who traded what, in which tx) and a Rotation (one wallet that sold
coin A and then bought coin B inside a time window). Nothing here implies
money flow, shared ownership, or a prediction - only what the chain recorded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class Trade:
    """A single observed swap, attributed by ERC-20 Transfer."""

    wallet: str          # 0x-address that traded
    side: str            # "buy" or "sell"
    coin: str            # ticker, e.g. "TruffleHog-7b08"
    amount: float        # token amount
    usdc: float          # USDC value observed on the venue
    venue: str           # "PONS" (bonding curve) or "UniV4"
    block: int
    ts: datetime         # UTC timestamp
    tx: str              # transaction hash

    @property
    def ts_hhmmss(self) -> str:
        return self.ts.astimezone(UTC).strftime("%H:%M:%S")

    @property
    def tx_short(self) -> str:
        return f"{self.tx[:6]}...{self.tx[-4:]}" if len(self.tx) > 12 else self.tx


@dataclass(frozen=True)
class Rotation:
    """One wallet sold coin A, then bought coin B inside the window.

    grade:
      direct    - sell and buy in the same transaction
      clean     - the wallet sold only A in the window
      ambiguous - it also sold other coins (listed, never counted in weight)
    """

    wallet: str
    sold: str
    bought: str
    gap_s: int           # seconds between the sell and the buy
    grade: str           # direct | clean | ambiguous
    sell_tx: str
    buy_tx: str
    also_sold: tuple[str, ...] = field(default_factory=tuple)

    @property
    def wallet_short(self) -> str:
        return f"{self.wallet[:6]}...{self.wallet[-4:]}"


@dataclass(frozen=True)
class InflowRow:
    """A ranked RADAR row: observed net inflow into one coin, parts visible."""

    coin: str
    wallets_in: int      # distinct wallets that bought in the window
    net_usdc: float      # observed net USDC inflow
    rotations_in: int    # rotations landing on this coin
    venue: str
