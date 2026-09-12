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
import sys

from . import __version__, brand, data, theme

TAGLINE = "on-chain intel for the little guy  .  Robinhood Chain  .  read-only"


def _ensure_utf8() -> bool:
    """Block glyphs need UTF-8 out. Switch the stream over; report if it stuck."""
    enc = (getattr(sys.stdout, "encoding", "") or "").lower()
    if "utf" in enc:
        return True
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        return True
    except (AttributeError, ValueError, OSError):
        return False


def banner() -> str:
    """The pixel shrimp beside the SHRIMP wordmark, then the tagline."""
    if not (_ensure_utf8() and theme._COLOR):
        # No colour, or a legacy codepage that cannot take block glyphs: plain banner.
        return (theme.coral("  (o )~  ", bold=True)
                + theme.salmon("SHRIMP TERMINAL", bold=True)
                + theme.muted(f"  v{__version__}\n  " + TAGLINE))
    shrimp = brand.shrimp_lines("ansi")
    word = brand.wordmark_ansi(theme.CORAL)
    # centre the 5-row wordmark against the taller shrimp, joined side by side
    pad = [""] * ((len(shrimp) - len(word)) // 2)
    right = pad + word + [""] * (len(shrimp) - len(word) - len(pad))
    lines = [f"  {s}   {r}" for s, r in zip(shrimp, right)]
    lines.append("")
    lines.append(theme.muted("  " + TAGLINE) + theme.muted(f"   v{__version__}"))
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


def cmd_whales(_: argparse.Namespace) -> int:
    print(banner())
    print(_hr("WHALES  .  large wallets  .  observed 24h net usdc"))
    print(theme.muted("  wallet          band    net 24h     buys/sells   last"))
    for w in data.load_whales():
        band = theme.paint(w.tag.ljust(5), theme.sea if w.tag == "mega" else theme.salmon)
        net = theme.paint(f"{w.net_24h:>+11,.0f}", theme.GOOD if w.net_24h >= 0 else theme.PINK)
        side = theme.pink("SELL") if w.last_side == "sell" else theme.sea("BUY ")
        print(
            f"  {w.wallet_short}  {band}  {net}   {w.buys:>3}/{w.sells:<3}   "
            f"{side} {theme.salmon(w.last_coin)} {theme.muted(w.last_hhmmss)}"
        )
    print(_hr())
    print(theme.muted("  a size band from observed flow, never an identity. no advice.\n"))
    return 0


def cmd_smart(_: argparse.Namespace) -> int:
    print(banner())
    print(_hr("SMART MONEY  .  strong observed history  .  realised pnl"))
    print(theme.muted("  wallet          kind      pnl usdc     win    trades   now in"))
    for s in data.load_smart():
        kind = theme.paint(s.tag.ljust(7), theme.salmon)
        pnl = theme.paint(f"{s.pnl_usdc:>+10,.0f}", theme.GOOD if s.pnl_usdc >= 0 else theme.PINK)
        win = theme.paint(f"{s.win_pct:>3}%", theme.GOOD if s.win_pct >= 60 else theme.MUTED)
        print(
            f"  {s.wallet_short}  {kind}  {pnl}   {win}   {s.trades:>5}   "
            f"{theme.salmon(s.now_in)}"
        )
    print(_hr())
    print(theme.muted("  past observed performance is not a prediction. no advice.\n"))
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
    print(f"    {theme.salmon('shrimp whales')}     large wallets by observed 24h net usdc")
    print(f"    {theme.salmon('shrimp smart')}      wallets with a strong observed history")
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
    sub.add_parser("whales", help="large wallets by observed 24h net usdc").set_defaults(func=cmd_whales)
    sub.add_parser("smart", help="wallets with a strong observed history").set_defaults(func=cmd_smart)
    sub.add_parser("tui", help="full-screen terminal (needs textual)").set_defaults(func=cmd_tui)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
