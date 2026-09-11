"""Shrimp Terminal color palette and ANSI helpers.

The palette is "shrimp": coral / salmon / pink on near-black. It is defined once
here so the CLI (plain ANSI) and the Textual TUI (rich markup) stay in sync.

Truecolor ANSI is used with a graceful fallback: if a terminal does not support
it the escapes are simply ignored and the text still reads fine.
"""

from __future__ import annotations

import os
import sys

# --- Palette (hex, shared with the future web/ frontend) -------------------
CORAL = "#FF6B6B"      # primary   - shrimp shell
SALMON = "#FF8E72"     # secondary - warm accent
PINK = "#FF4D6D"       # alert / hot
SHELL = "#FFD9C0"      # light text on dark
INK = "#1A0F0F"        # background
MUTED = "#8A5A5A"      # dim labels
SEA = "#3A6EA5"        # cool accent (whales / links)
GOOD = "#5AD1A0"       # positive / clean grade
WARN = "#F2C14E"       # caution / ambiguous grade

# --- Truecolor ANSI --------------------------------------------------------
_RESET = "\x1b[0m"
_BOLD = "\x1b[1m"
_DIM = "\x1b[2m"


def _rgb(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"\x1b[38;2;{r};{g};{b}m"


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return sys.stdout.isatty()


_COLOR = _supports_color()


def paint(text: str, hex_color: str, *, bold: bool = False, dim: bool = False) -> str:
    """Wrap text in a truecolor ANSI code (no-op when color is unsupported)."""
    if not _COLOR:
        return text
    prefix = _rgb(hex_color)
    if bold:
        prefix = _BOLD + prefix
    if dim:
        prefix = _DIM + prefix
    return f"{prefix}{text}{_RESET}"


def coral(t: str, **kw: bool) -> str:
    return paint(t, CORAL, **kw)


def salmon(t: str, **kw: bool) -> str:
    return paint(t, SALMON, **kw)


def pink(t: str, **kw: bool) -> str:
    return paint(t, PINK, **kw)


def muted(t: str, **kw: bool) -> str:
    return paint(t, MUTED, **kw)


def sea(t: str, **kw: bool) -> str:
    return paint(t, SEA, **kw)


def grade_color(grade: str) -> str:
    """Map a rotation grade to its palette color."""
    return {
        "direct": SEA,
        "clean": GOOD,
        "ambiguous": WARN,
    }.get(grade, MUTED)
