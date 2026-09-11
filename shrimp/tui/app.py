"""Full-screen Shrimp Terminal (Textual).

This is the skeleton of the TUI shown in the README mock: a shared session
clock across the top, a left summary column and a right live-feed column, with
views switched by hotkey (FEED / RADAR / FLOW / MAP). Only FEED and RADAR are
wired to fixture data so far; FLOW and MAP are placeholders.

Run with:  shrimp tui   (requires `textual`)
"""

from __future__ import annotations

from typing import ClassVar

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Footer, Header, Static

from .. import __version__, data, theme
from ..cli import TAGLINE

SHRIMP = "(o )~"


class Summary(Static):
    """Left column - headline numbers over the sample."""

    def on_mount(self) -> None:
        inflow = data.load_inflow()
        rotations = data.load_rotations()
        trades = data.load_trades()
        top = inflow[0] if inflow else None
        lines = [
            f"[b]{SHRIMP}  SHRIMP TERMINAL[/]  v{__version__}",
            f"[dim]{TAGLINE}[/]",
            "",
            f"[b]{len(trades)}[/] observed trades",
            f"[b]{len(rotations)}[/] rotations",
            f"[b]{len(inflow)}[/] coins with inflow",
        ]
        if top:
            lines += ["", "[b]TOP INFLOW[/]", f"  {top.coin}  +{top.net_usdc:,.0f} usdc"]
        self.update("\n".join(lines))


class Feed(DataTable):
    """Right column - the live-style stream of trades."""

    def on_mount(self) -> None:
        self.cursor_type = "row"
        self.add_columns("time", "wallet", "side", "coin", "usdc", "tx")
        for t in data.load_trades():
            wallet = f"{t.wallet[:6]}..{t.wallet[-4:]}"
            self.add_row(t.ts_hhmmss, wallet, t.side.upper(), t.coin,
                         f"{t.usdc:,.2f}", t.tx_short)


class ShrimpApp(App):
    """Skeleton app; FLOW and MAP are not yet implemented."""

    TITLE = "SHRIMP TERMINAL"
    CSS = f"""
    Screen {{ background: {theme.INK}; }}
    #summary {{ width: 34; padding: 1 2; color: {theme.SHELL}; border-right: solid {theme.MUTED}; }}
    DataTable {{ height: 1fr; }}
    """
    BINDINGS: ClassVar[list[tuple[str, str, str]]] = [
        ("f", "view('feed')", "FEED"),
        ("r", "view('radar')", "RADAR"),
        ("q", "quit", "quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield Summary(id="summary")
            with Vertical():
                yield Feed()
        yield Footer()

    def action_view(self, name: str) -> None:
        # Placeholder: FEED is the default view; RADAR/FLOW/MAP come next.
        self.notify(f"view: {name} (fixture mode)", timeout=2)


def run() -> int:
    ShrimpApp().run()
    return 0
