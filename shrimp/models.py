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
    score: int = 0       # 0-99 gauge of recent inflow intensity
    pct_1h: float = 0.0  # observed price change over the last hour (%)
    source: str = ""     # the single biggest coin rotating into this one
    source_wallets: int = 0
    extra_sources: int = 0  # how many other source coins feed it (the "+N")


@dataclass(frozen=True)
class Sequence:
    """One tape row: a wallet that sold A then bought B, with its grade."""

    ts: datetime
    wallet: str
    sold: str
    bought: str
    grade: str

    @property
    def ts_hhmmss(self) -> str:
        return self.ts.astimezone(UTC).strftime("%H:%M:%S")

    @property
    def wallet_short(self) -> str:
        return f"{self.wallet[:6]}..{self.wallet[-4:]}"


@dataclass(frozen=True)
class RouteEdge:
    """The single hottest route, for the MAP hero: N wallets sold A -> bought B."""

    sold: str
    bought: str
    sold_addr: str
    bought_addr: str
    wallets: int      # distinct wallets on this route (the edge weight)
    rows: int         # sequence rows (a wallet buying nine times is nine rows)
    ambiguous: int    # rows that also sold other coins, listed, never counted
    extra_seq: int    # the small "+N sequences" tag on the node


@dataclass(frozen=True)
class FlowSource:
    """One branch of the FLOW fan: a coin rotating into the chosen destination."""

    coin: str
    wallets: int
    grade: str


@dataclass(frozen=True)
class Whale:
    """A large wallet, ranked by observed 24h net USDC moved on the venues."""

    wallet: str
    tag: str          # "mega" | "shark" | "orca" - a size band, observed not assigned
    net_24h: float    # net USDC over the last 24h (buys minus sells)
    buys: int
    sells: int
    last_side: str    # "buy" | "sell"
    last_coin: str
    last_ts: datetime

    @property
    def wallet_short(self) -> str:
        return f"{self.wallet[:6]}..{self.wallet[-4:]}"

    @property
    def last_hhmmss(self) -> str:
        return self.last_ts.astimezone(UTC).strftime("%H:%M:%S")


@dataclass(frozen=True)
class SmartWallet:
    """A wallet with a strong observed history - realised PnL and hit rate."""

    wallet: str
    tag: str          # "smart" | "sniper" | "rotator"
    pnl_usdc: float   # realised PnL over the sample window
    win_rate: float   # 0..1 share of closed trades in profit
    trades: int
    best_coin: str
    now_in: str       # the coin this wallet is holding right now

    @property
    def wallet_short(self) -> str:
        return f"{self.wallet[:6]}..{self.wallet[-4:]}"

    @property
    def win_pct(self) -> int:
        return round(self.win_rate * 100)
