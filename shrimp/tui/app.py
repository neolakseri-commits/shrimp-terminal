"""Full-screen Shrimp Terminal (Textual).

A single session drives four views over one dataset, switched by hotkey:

    FEED   a live-style stream of observed trades (replay over the fixture)
    RADAR  coins ranked by observed inflow, with visible bars
    FLOW   sold-A -> bought-B rotations grouped by route
    MAP    coins laid out by venue and sized by inflow

The top bar is the shared session clock: MODE (FIXTURE / REPLAY / LIVE) and the
UTC time, mirrored on every view. Replay and live are always labelled - nothing
here pretends fixture data is live.

Run with:  shrimp tui   (requires `textual`)
"""

from __future__ import annotations

import itertools
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import ClassVar

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import ContentSwitcher, DataTable, Footer, Static

from .. import __version__, data, theme
from ..models import Trade

SHRIMP = "(o )~"
TAGLINE = "on-chain intel for the little guy"
FEED_CAP = 60  # rows kept in the streaming feed


# --------------------------------------------------------------------------- #
# Top bar - the shared session clock                                          #
# --------------------------------------------------------------------------- #
class TopBar(Static):
    """One line, present on every view: mode + clock + active view + counts."""

    mode = reactive("REPLAY")
    clock = reactive("--:--:--")
    view = reactive("FEED")
    trades = reactive(0)
    rotations = reactive(0)

    def render(self) -> Text:
        t = Text()
        t.append(f" {SHRIMP} ", style=f"bold {theme.CORAL}")
        t.append("SHRIMP TERMINAL", style=f"bold {theme.SALMON}")
        t.append(f"  v{__version__}   ", style=theme.MUTED)
        t.append("MODE ", style=theme.MUTED)
        t.append(f"{self.mode}", style=f"bold {theme.WARN}")
        t.append("   CLOCK ", style=theme.MUTED)
        t.append(f"{self.clock} UTC", style=theme.SHELL)
        t.append("   VIEW ", style=theme.MUTED)
        t.append(f"{self.view}", style=f"bold {theme.PINK}")
        t.append(f"   {self.trades} trades / {self.rotations} rotations", style=theme.MUTED)
        return t


# --------------------------------------------------------------------------- #
# Views                                                                       #
# --------------------------------------------------------------------------- #
class FeedView(Vertical):
    """Right-scrolling stream of observed trades (replay)."""

    def compose(self) -> ComposeResult:
        yield Static(" FEED  .  observed trades  .  replay over fixture sample",
                     classes="section")
        table = DataTable(id="feed-table", zebra_stripes=False, cursor_type="none")
        yield table

    def on_mount(self) -> None:
        table = self.query_one("#feed-table", DataTable)
        table.add_columns("time", "wallet", "side", "coin", "usdc", "venue", "tx")
        self._keys: list = []

    def push(self, tr: Trade) -> None:
        table = self.query_one("#feed-table", DataTable)
        side = Text(tr.side.upper().ljust(4),
                    style=theme.PINK if tr.side == "sell" else theme.SEA)
        key = table.add_row(
            Text(tr.ts_hhmmss, style=theme.MUTED),
            f"{tr.wallet[:6]}..{tr.wallet[-4:]}",
            side,
            Text(tr.coin, style=theme.SALMON),
            f"{tr.usdc:,.2f}",
            Text(tr.venue, style=theme.MUTED),
            Text(tr.tx_short, style=theme.MUTED),
        )
        self._keys.append(key)
        if len(self._keys) > FEED_CAP:
            table.remove_row(self._keys.pop(0))
        table.scroll_end(animate=False)


class RadarView(Vertical):
    """Coins ranked by observed inflow, with visible bars."""

    def compose(self) -> ComposeResult:
        yield Static(" RADAR  .  observed inflow  .  parts visible", classes="section")
        yield Static(self._board(), id="radar-body")

    def _board(self) -> Text:
        rows = data.load_inflow()
        top = max((r.net_usdc for r in rows), default=1.0)
        out = Text()
        out.append("  #   coin              wallets    net usdc   venue   inflow\n",
                   style=theme.MUTED)
        for i, r in enumerate(rows, start=1):
            width = round(28 * r.net_usdc / top)
            bar = "#" * max(width, 1)
            out.append(f"  {i:<3} ", style=theme.CORAL)
            out.append(f"{r.coin:<16}  ", style=theme.SALMON)
            out.append(f"{r.wallets_in:>6}   ", style=theme.SHELL)
            out.append(f"{r.net_usdc:>9,.0f}  ", style=theme.SHELL)
            out.append(f"{r.venue:<6}  ", style=theme.MUTED)
            out.append(f"{bar}\n", style=theme.PINK)
        out.append("\n  a ranking of observed inflow, not a prediction. no advice.",
                   style=theme.MUTED)
        return out


class FlowView(Vertical):
    """sold-A -> bought-B rotations grouped by destination coin."""

    def compose(self) -> ComposeResult:
        yield Static(" FLOW  .  sold A -> bought B  .  grouped by route", classes="section")
        yield Static(self._diagram(), id="flow-body")

    def _diagram(self) -> Text:
        rotations = data.load_rotations()
        by_dest: dict[str, list] = {}
        for r in rotations:
            by_dest.setdefault(r.bought, []).append(r)
        out = Text()
        for dest, rots in by_dest.items():
            out.append(f"\n  ==> {dest}", style=f"bold {theme.SEA}")
            out.append(f"   ({len(rots)} wallet(s))\n", style=theme.MUTED)
            for r in rots:
                out.append(f"        {r.wallet_short}  sold ", style=theme.SHELL)
                out.append(f"{r.sold}", style=theme.PINK)
                out.append(f"  gap {r.gap_s}s  ", style=theme.MUTED)
                out.append(f"[{r.grade}]", style=f"bold {theme.grade_color(r.grade)}")
                if r.also_sold:
                    out.append(f"  (also sold {', '.join(r.also_sold)} - not counted)",
                               style=theme.MUTED)
                out.append("\n")
        out.append(
            "\n  edge weight counts distinct wallets, never rows. see docs/EXAMPLES.md.",
            style=theme.MUTED)
        return out


class MapView(Vertical):
    """Coins laid out by venue (columns) and sized by inflow (bars)."""

    def compose(self) -> ComposeResult:
        yield Static(" MAP  .  coins by venue  .  sized by inflow", classes="section")
        yield Static(self._map(), id="map-body")

    def _map(self) -> Text:
        rows = data.load_inflow()
        top = max((r.net_usdc for r in rows), default=1.0)
        venues = ["PONS", "UniV4"]
        out = Text()
        for venue in venues:
            out.append(f"\n  [ {venue} ]\n", style=f"bold {theme.WARN}")
            for r in [x for x in rows if x.venue == venue]:
                size = max(round(6 * r.net_usdc / top), 1)
                node = "(" + "o" * size + ")"
                out.append(f"     {node} ", style=theme.CORAL)
                out.append(f"{r.coin}", style=theme.SALMON)
                out.append(f"  {r.wallets_in} wallets  +{r.net_usdc:,.0f} usdc\n",
                           style=theme.MUTED)
        out.append("\n  a spatial layout of observed data, not a network of ownership.",
                   style=theme.MUTED)
        return out


# --------------------------------------------------------------------------- #
# App                                                                         #
# --------------------------------------------------------------------------- #
class ShrimpApp(App):
    TITLE = "SHRIMP TERMINAL"

    CSS = f"""
    Screen {{ background: {theme.INK}; }}
    TopBar {{
        dock: top; height: 1; background: {theme.INK}; color: {theme.SHELL};
        border-bottom: solid {theme.MUTED};
    }}
    .section {{ color: {theme.SALMON}; text-style: bold; padding: 0 1; height: 1; }}
    #summary {{
        width: 30; padding: 1 2; color: {theme.SHELL};
        border-right: solid {theme.MUTED};
    }}
    DataTable {{ height: 1fr; }}
    #radar-body, #flow-body, #map-body {{ padding: 0 1; }}
    """

    BINDINGS: ClassVar[list[tuple[str, str, str]]] = [
        ("f", "view('feed')", "FEED"),
        ("r", "view('radar')", "RADAR"),
        ("l", "view('flow')", "FLOW"),
        ("m", "view('map')", "MAP"),
        ("space", "toggle_pause", "pause"),
        ("q", "quit", "quit"),
    ]

    _VIEW_NAMES: ClassVar[dict[str, str]] = {
        "feed": "FEED", "radar": "RADAR", "flow": "FLOW", "map": "MAP",
    }

    def __init__(self) -> None:
        super().__init__()
        self._clock = datetime.now(UTC)
        self._stream = itertools.cycle(data.load_trades())
        self._paused = False
        self._trade_count = 0

    def compose(self) -> ComposeResult:
        yield TopBar()
        with Horizontal():
            yield Static(self._summary(), id="summary")
            with ContentSwitcher(initial="feed"):
                yield FeedView(id="feed")
                yield RadarView(id="radar")
                yield FlowView(id="flow")
                yield MapView(id="map")
        yield Footer()

    def on_mount(self) -> None:
        bar = self.query_one(TopBar)
        bar.rotations = len(data.load_rotations())
        self._refresh_bar()
        self.set_interval(0.7, self._tick)

    # -- session loop ------------------------------------------------------- #
    def _tick(self) -> None:
        if self._paused:
            return
        self._clock += timedelta(seconds=7)
        tr = replace(next(self._stream), ts=self._clock)
        self.query_one(FeedView).push(tr)
        self._trade_count += 1
        self._refresh_bar()

    def _refresh_bar(self) -> None:
        bar = self.query_one(TopBar)
        bar.mode = "REPLAY (paused)" if self._paused else "REPLAY"
        bar.clock = self._clock.strftime("%H:%M:%S")
        bar.trades = self._trade_count

    def _summary(self) -> Text:
        inflow = data.load_inflow()
        top = inflow[0] if inflow else None
        out = Text()
        out.append(f"{SHRIMP} SHRIMP\n", style=f"bold {theme.CORAL}")
        out.append(f"{TAGLINE}\n\n", style=theme.MUTED)
        out.append("OVERVIEW\n", style=f"bold {theme.SALMON}")
        out.append(f"{len(data.load_trades())} ", style=f"bold {theme.SHELL}")
        out.append("coins traded\n", style=theme.MUTED)
        out.append(f"{len(inflow)} ", style=f"bold {theme.SHELL}")
        out.append("coins w/ inflow\n", style=theme.MUTED)
        out.append(f"{len(data.load_rotations())} ", style=f"bold {theme.SHELL}")
        out.append("rotations\n\n", style=theme.MUTED)
        if top:
            out.append("TOP INFLOW\n", style=f"bold {theme.SALMON}")
            out.append(f"{top.coin}\n", style=theme.SALMON)
            out.append(f"+{top.net_usdc:,.0f} usdc", style=theme.SHELL)
        return out

    # -- actions ------------------------------------------------------------ #
    def action_view(self, name: str) -> None:
        self.query_one(ContentSwitcher).current = name
        self.query_one(TopBar).view = self._VIEW_NAMES.get(name, name.upper())

    def action_toggle_pause(self) -> None:
        self._paused = not self._paused
        self._refresh_bar()


def run() -> int:
    ShrimpApp().run()
    return 0
