"""Full-screen Shrimp Terminal (Textual).

Three panels, one dataset, one session clock:

    LEFT    TOP INFLOW - coins ranked by observed inflow, score + 1h + source
    CENTER  the active view, switched by hotkey:
              RADAR  the full inflow board with bars and 1h change
              FLOW   the fan of coins rotating into the hottest destination
              MAP    the hero graph: N wallets sold A -> bought B
    RIGHT   TAPE - a live stream of observed sequences, always running

The top bar is the shared clock: mode (FIXTURE / REPLAY / LIVE), speed, UTC time
and the replay window. Replay and live are always labelled - the terminal never
passes the shipped sample off as live data.

Run with:  shrimp tui   (requires `textual`)
"""

from __future__ import annotations

import itertools
from dataclasses import replace
from datetime import timedelta
from typing import ClassVar

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import ContentSwitcher, DataTable, Footer, Static

from .. import data, theme
from ..models import Sequence
from ..sample import WINDOW_END, WINDOW_MIN

SHRIMP = "(o )~"
TAPE_CAP = 80
TABS = [("1", "radar", "RADAR"), ("2", "flow", "FLOW"), ("3", "map", "MAP")]


def _short(addr: str) -> str:
    return f"{addr[:6]}..{addr[-4:]}" if len(addr) > 12 else addr


def _pct(v: float) -> Text:
    style = theme.GOOD if v >= 0 else theme.PINK
    return Text(f"{'+' if v >= 0 else ''}{v:,.0f}% 1h", style=style)


# --------------------------------------------------------------------------- #
# Top bar - shared session clock                                              #
# --------------------------------------------------------------------------- #
class TopBar(Static):
    clock = reactive("--:--:--")
    view = reactive("map")
    paused = reactive(False)
    streamed = reactive(0)

    def render(self) -> Text:
        t = Text()
        t.append(f" {SHRIMP} ", style=f"bold {theme.CORAL}")
        t.append("SHRIMP", style=f"bold {theme.SALMON}")
        t.append("   ", style=theme.MUTED)
        for key, vid, label in TABS:
            if vid == self.view:
                t.append(f" {key} {label} ", style=f"bold {theme.INK} on {theme.CORAL}")
            else:
                t.append(f" {key} {label} ", style=theme.MUTED)
            t.append(" ", style=theme.MUTED)
        mode = "REPLAY (paused)" if self.paused else "REPLAY 20x"
        t.append("  ", style=theme.MUTED)
        t.append(f"{mode}", style=f"bold {theme.WARN}")
        t.append("  CLOCK ", style=theme.MUTED)
        t.append(f"{self.clock} UTC", style=theme.SHELL)
        start = (WINDOW_END - timedelta(minutes=WINDOW_MIN)).strftime("%H:%M:%S")
        t.append(f"  RANGE {start}-{WINDOW_END.strftime('%H:%M:%S')}", style=theme.MUTED)
        return t


# --------------------------------------------------------------------------- #
# Left board - TOP INFLOW                                                     #
# --------------------------------------------------------------------------- #
class InflowBoard(Static):
    def render(self) -> Text:
        rows = data.load_inflow()
        t = Text()
        t.append(" TOP INFLOW\n", style=f"bold {theme.SALMON}")
        t.append(" last 10 min\n\n", style=theme.MUTED)
        for i, r in enumerate(rows, start=1):
            t.append(f" {i:<2}", style=theme.MUTED)
            t.append(f"{r.score:>3}  ", style=f"bold {theme.CORAL}")
            t.append(f"{r.coin}\n", style=f"bold {theme.SALMON}")
            t.append(f"       <- {r.source} {r.source_wallets}", style=theme.MUTED)
            t.append(f" +{r.extra_sources}   ", style=theme.MUTED)
            t.append(_pct(r.pct_1h))
            t.append("\n")
        return t


# --------------------------------------------------------------------------- #
# Center views                                                                #
# --------------------------------------------------------------------------- #
class RadarView(Static):
    def render(self) -> Text:
        rows = data.load_inflow()
        top = max((r.net_usdc for r in rows), default=1.0)
        t = Text()
        t.append(" RADAR", style=f"bold {theme.PINK}")
        t.append("  .  observed inflow  .  all parts visible\n\n", style=theme.MUTED)
        t.append("  #  score  coin               wallets    net usdc   1h change   inflow\n",
                 style=theme.MUTED)
        for i, r in enumerate(rows, start=1):
            width = round(18 * r.net_usdc / top)
            t.append(f"  {i:<2} ", style=theme.MUTED)
            t.append(f"{r.score:>4}   ", style=f"bold {theme.CORAL}")
            t.append(f"{r.coin:<17}  ", style=f"bold {theme.SALMON}")
            t.append(f"{r.wallets_in:>6}   ", style=theme.SHELL)
            t.append(f"{r.net_usdc:>9,.0f}   ", style=theme.SHELL)
            pct = _pct(r.pct_1h)
            pct.pad_right(max(0, 10 - len(pct.plain)))
            t.append(pct)
            t.append(f"  {'|' * max(width, 1)}\n", style=theme.CORAL)
        t.append("\n  ranked by observed net inflow. a ranking, not a prediction.\n",
                 style=theme.MUTED)
        return t


class FlowView(Static):
    def render(self) -> Text:
        hot = data.hot_route()
        sources = data.flow_sources(hot.bought)
        total = sum(s.wallets for s in sources)
        t = Text()
        t.append(" FLOW", style=f"bold {theme.PINK}")
        t.append("  .  coins rotating into one destination\n\n", style=theme.MUTED)
        n = len(sources)
        for i, s in enumerate(sources):
            elbow = "\\" if i == 0 else ("/" if i == n - 1 else "-")
            mid = i == n // 2
            arm = f"  {s.coin:>16} {elbow}"
            t.append(arm, style=theme.SALMON)
            if mid:
                t.append("---==>  ", style=theme.CORAL)
                t.append(f"{hot.bought}", style=f"bold {theme.CORAL}")
            else:
                t.append("---+", style=theme.MUTED)
            t.append(f"    {s.wallets} wallets  [{s.grade}]\n",
                     style=theme.grade_color(s.grade))
        t.append(f"\n  {total} wallets rotated in over {WINDOW_MIN} min", style=theme.SHELL)
        t.append("  .  edge weight counts wallets, never rows\n", style=theme.MUTED)
        return t


class MapView(Static):
    def render(self) -> Text:
        hot = data.hot_route()
        pad = "              "
        t = Text()
        t.append("\n")
        t.append(f"{pad}      B . BOUGHT\n", style=theme.CORAL)
        t.append(f"{pad}   {hot.bought}\n", style=f"bold {theme.CORAL}")
        t.append(f"{pad}     {hot.bought_addr}\n", style=theme.MUTED)
        t.append(f"{pad}          @\n", style=f"bold {theme.CORAL}")
        t.append(f"{pad}          |\n", style=theme.CORAL)
        t.append(f"{pad}          |\n", style=theme.CORAL)
        t.append(f"{pad}          O\n", style=f"bold {theme.SALMON}")
        t.append(f"{pad}      A . SOLD\n", style=theme.SALMON)
        t.append(f"{pad}    {hot.sold}\n", style=f"bold {theme.SALMON}")
        t.append(f"{pad}      {hot.sold_addr}\n", style=theme.MUTED)
        t.append(f"{pad}     +{hot.extra_seq} sequences\n\n\n", style=theme.PINK)
        t.append(f"   {hot.wallets} WALLETS\n", style=f"bold {theme.CORAL}")
        t.append("   SOLD ", style=f"bold {theme.SHELL}")
        t.append(f"{hot.sold}", style=f"bold {theme.PINK}")
        t.append("  ->  BOUGHT ", style=f"bold {theme.SHELL}")
        t.append(f"{hot.bought}\n", style=f"bold {theme.CORAL}")
        t.append(
            f"   within {WINDOW_MIN} min  .  observed sequences  .  "
            f"{hot.rows} rows  .  ambiguous {hot.ambiguous} not counted\n",
            style=theme.MUTED)
        return t


# --------------------------------------------------------------------------- #
# Right panel - TAPE                                                          #
# --------------------------------------------------------------------------- #
class Tape(Static):
    def compose(self) -> ComposeResult:
        yield Static(id="tape-head")
        table = DataTable(id="tape-table", zebra_stripes=False, cursor_type="none")
        yield table

    def on_mount(self) -> None:
        self._total = len(data.load_tape())
        head = self.query_one("#tape-head", Static)
        head.update(self._header())
        table = self.query_one("#tape-table", DataTable)
        table.add_columns("time", "wallet", "sold", "bought", "g")
        self._keys: list = []

    def _header(self) -> Text:
        t = Text()
        t.append(" TAPE", style=f"bold {theme.SALMON}")
        t.append(f"  .  {self._total:,} observed sequences\n", style=theme.MUTED)
        t.append(" time . wallet . SOLD -> BOUGHT . grade", style=theme.MUTED)
        return t

    def push(self, s: Sequence) -> None:
        table = self.query_one("#tape-table", DataTable)
        key = table.add_row(
            Text(s.ts_hhmmss, style=theme.MUTED),
            Text(_short(s.wallet), style=theme.SHELL),
            Text(s.sold[:11], style=theme.PINK),
            Text(s.bought[:11], style=theme.SALMON),
            Text(s.grade[0], style=theme.grade_color(s.grade)),
        )
        self._keys.append(key)
        if len(self._keys) > TAPE_CAP:
            table.remove_row(self._keys.pop(0))
        table.scroll_end(animate=False)


# --------------------------------------------------------------------------- #
# App                                                                         #
# --------------------------------------------------------------------------- #
class ShrimpApp(App):
    TITLE = "SHRIMP TERMINAL"

    CSS = f"""
    Screen {{ background: {theme.INK}; }}
    TopBar {{ dock: top; height: 1; background: {theme.INK}; color: {theme.SHELL};
              border-bottom: solid {theme.MUTED}; }}
    #body {{ height: 1fr; }}
    InflowBoard {{ width: 34; padding: 1 1; border-right: solid {theme.MUTED};
                   color: {theme.SHELL}; }}
    #center {{ width: 1fr; padding: 1 2; }}
    Tape {{ width: 46; border-left: solid {theme.MUTED}; padding: 1 1; }}
    #tape-head {{ height: 2; color: {theme.SHELL}; }}
    #tape-table {{ height: 1fr; }}
    RadarView, FlowView, MapView {{ height: 1fr; }}
    """

    BINDINGS: ClassVar[list[tuple[str, str, str]]] = [
        ("1", "view('radar')", "RADAR"),
        ("2", "view('flow')", "FLOW"),
        ("3", "view('map')", "MAP"),
        ("r", "view('radar')", "RADAR"),
        ("l", "view('flow')", "FLOW"),
        ("m", "view('map')", "MAP"),
        ("space", "toggle_pause", "pause"),
        ("q", "quit", "quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._clock = WINDOW_END
        self._stream = itertools.cycle(data.load_tape())
        self._paused = False
        self._streamed = 0

    def compose(self) -> ComposeResult:
        yield TopBar()
        with Horizontal(id="body"):
            yield InflowBoard()
            with ContentSwitcher(initial="map", id="center"):
                yield RadarView(id="radar")
                yield FlowView(id="flow")
                yield MapView(id="map")
            yield Tape()
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_bar()
        self.set_interval(0.5, self._tick)

    def _tick(self) -> None:
        if self._paused:
            return
        self._clock += timedelta(seconds=3)
        s = replace(next(self._stream), ts=self._clock)
        self.query_one(Tape).push(s)
        self._streamed += 1
        self._refresh_bar()

    def _refresh_bar(self) -> None:
        bar = self.query_one(TopBar)
        bar.clock = self._clock.strftime("%H:%M:%S")
        bar.paused = self._paused
        bar.streamed = self._streamed

    def action_view(self, name: str) -> None:
        self.query_one(ContentSwitcher).current = name
        self.query_one(TopBar).view = name

    def action_toggle_pause(self) -> None:
        self._paused = not self._paused
        self._refresh_bar()


def run() -> int:
    ShrimpApp().run()
    return 0
