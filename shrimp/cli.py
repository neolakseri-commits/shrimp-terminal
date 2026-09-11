"""Shrimp Terminal command-line entry point.

Zero-dependency by design: `shrimp` runs with nothing but the standard library
and a fixture file, so a fresh clone shows something on the first command. The
richer Textual TUI (`shrimp tui`) is an optional layer on top.

Commands:
    shrimp            banner + help
    shrimp feed       live-style stream of observed trades
    shrimp radar      ranked observed inflow (the scoreboard)
    shrimp rotations  wallets that sold A then bought B
    shrimp tui        launch the full-screen terminal (needs `textual`)
"""

from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__, data, theme

_ASCII = Path(__file__).resolve().parent.parent / "docs" / "ascii" / "shrimp.txt"

TAGLINE = "on-chain intel for the little guy  .  Robinhood Chain  .  read-only"


def banner() -> str:
    art = _ASCII.read_text(encoding="utf-8") if _ASCII.exists() else "  (o )~"
    lines = [theme.coral(line) for line in art.splitlines()]
    lines.append("")
    lines.append(theme.salmon("  S H R I M P   T E R M I N A L", bold=True)
                 + theme.muted(f"   v{__version__}"))
    lines.append(theme.muted("  " + TAGLINE))
    return "\n".join(lines)


def _hr(label: str = "") -> str:
    bar = theme.muted("-" * 64)
    return f"\n{bar}\n{theme.salmon(label, bold=True)}\n" if label else f"\n{bar}\n"


def cmd_feed(_: argparse.Namespace) -> int:
    print(banner())
    print(_hr("FEED  .  observed trades  .  fixture sample"))
    print(theme.muted("  time      wallet          side  coin              usdc      tx"))
    for t in data.load_trades():
        side = theme.pink(t.side.upper().ljust(4)) if t.side == "sell" else theme.sea(t.side.upper().ljust(4))
        wallet = f"{t.wallet[:6]}..{t.wallet[-4:]}"
        print(
            f"  {theme.muted(t.ts_hhmmss)}  {wallet}  {side}  "
            f"{theme.salmon(t.coin.ljust(16))}  {str(round(t.usdc,2)).rjust(8)}  "
            f"{theme.muted(t.tx_short)}"
        )
    print(_hr())
    print(theme.muted("  every row is a real tx hash - check it on the explorer.\n"))
    return 0


def cmd_radar(_: argparse.Namespace) -> int:
    print(banner())
    print(_hr("RADAR  .  observed inflow  .  parts visible"))
    print(theme.muted("  #   coin              wallets   net usdc     rotations  venue"))
    for i, row in enumerate(data.load_inflow(), start=1):
        print(
            f"  {theme.coral(str(i).ljust(3))} {theme.salmon(row.coin.ljust(16))}  "
            f"{str(row.wallets_in).rjust(6)}   {str(round(row.net_usdc,2)).rjust(9)}   "
            f"{str(row.rotations_in).rjust(8)}   {theme.muted(row.venue)}"
        )
    print(_hr())
    print(theme.muted("  a ranking of observed inflow, not a prediction. no advice.\n"))
    return 0


def cmd_rotations(_: argparse.Namespace) -> int:
    print(banner())
    print(_hr("ROTATIONS  .  sold A -> bought B  .  graded"))
    for r in data.load_rotations():
        g = theme.paint(r.grade, theme.grade_color(r.grade), bold=True)
        also = ""
        if r.also_sold:
            also = theme.muted(f"   (also sold: {', '.join(r.also_sold)} - not counted)")
        print(
            f"  {r.wallet_short}  sold {theme.pink(r.sold)} -> "
            f"bought {theme.sea(r.bought)}   gap {r.gap_s}s   [{g}]{also}"
        )
    print(_hr())
    print(theme.muted("  grades: direct / clean / ambiguous. see docs/EXAMPLES.md.\n"))
    return 0


def cmd_tui(_: argparse.Namespace) -> int:
    try:
        from .tui.app import run as run_tui
    except ModuleNotFoundError:
        print(banner())
        print(theme.pink("\n  The full-screen terminal needs Textual:"))
        print(theme.muted("      pip install textual\n"))
        return 1
    return run_tui()


def cmd_default(_: argparse.Namespace) -> int:
    print(banner())
    print(_hr())
    print(theme.muted("  commands:"))
    print(f"    {theme.salmon('shrimp feed')}       stream of observed trades")
    print(f"    {theme.salmon('shrimp radar')}      ranked observed inflow")
    print(f"    {theme.salmon('shrimp rotations')}  sold A -> bought B, graded")
    print(f"    {theme.salmon('shrimp tui')}        full-screen terminal (needs textual)")
    print(theme.muted("\n  read-only . no advice . no promises . data is a fixture sample\n"))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="shrimp",
        description="Shrimp Terminal - on-chain intel for the little guy on Robinhood Chain.",
    )
    p.add_argument("--version", action="version", version=f"shrimp {__version__}")
    p.set_defaults(func=cmd_default)
    sub = p.add_subparsers(dest="command")
    sub.add_parser("feed", help="stream of observed trades").set_defaults(func=cmd_feed)
    sub.add_parser("radar", help="ranked observed inflow").set_defaults(func=cmd_radar)
    sub.add_parser("rotations", help="sold A -> bought B, graded").set_defaults(func=cmd_rotations)
    sub.add_parser("tui", help="full-screen terminal (needs textual)").set_defaults(func=cmd_tui)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
