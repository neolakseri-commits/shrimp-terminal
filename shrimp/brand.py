"""Shrimp Terminal brand marks, drawn in the terminal itself - no image files, no font.

Two things live here:

* a pixel shrimp, rendered as terminal half-blocks (one '▀' carries two vertical
  pixels: the upper is the glyph colour, the lower is the cell background), so a
  small colour grid becomes a crisp coloured mascot in any truecolor terminal; and
* the word SHRIMP as 5-row block glyphs, so the wordmark needs no font either.

Both render to plain truecolor ANSI (the CLI) or Rich markup (the Textual TUI)
from one grid, so the CLI banner and the TUI header always match.
"""

from __future__ import annotations

from . import theme

# --- the pixel shrimp -------------------------------------------------------
# A curled prawn: tail fan upper-right, body arcing down to the head lower-left,
# one dark eye, little legs. Keys: O outline · C coral shell · H highlight ·
# E eye · '.' transparent. Two rows collapse into one line of half-blocks.
_SHRIMP = [
    "..........................H...",
    "...............OOOOOOO..HH....",
    "............OOOOCCCCCOOOH.HH..",
    "..........OOOCCCCCCCCCCHHH....",
    ".........OOCCCCCCCCCOOOOH.....",
    "........OOCCCCCCOOOOO....HH...",
    ".......OOCCCCCCOO.............",
    ".......OCCCCCCOO..............",
    "......OOCCCCCOO...............",
    "......OCCCCCCO................",
    ".....OOCCCCCCO................",
    ".....OCCCCCCCO................",
    ".....OCCEECCCO................",
    "....OOCOOCCCCOO...............",
    ".....OOCCCCCCO................",
    "...OOOCCCCCCOO.O..O...........",
    "..O.OOOCOCCCOO.O..O...........",
    "......OOOOOOO.................",
]

_COLORS = {
    "O": "#8A3A2A",  # outline / shell edge
    "C": theme.CORAL,  # shell body
    "H": theme.SALMON,  # highlight
    "E": "#1A0C0A",  # eye
}
_BG = theme.INK

# --- SHRIMP wordmark, 5 rows x 6 columns per glyph --------------------------
_GLYPHS = {
    "S": ["██████", "██    ", "██████", "    ██", "██████"],
    "H": ["██  ██", "██  ██", "██████", "██  ██", "██  ██"],
    "R": ["█████ ", "██  ██", "█████ ", "██ ██ ", "██  ██"],
    "I": ["██████", "  ██  ", "  ██  ", "  ██  ", "██████"],
    "M": ["██  ██", "██████", "██████", "██  ██", "██  ██"],
    "P": ["██████", "██  ██", "██████", "██    ", "██    "],
}
_WORD = "SHRIMP"


def _hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _cell_ansi(top: str, bottom: str) -> str:
    """One '▀': upper pixel is the foreground, lower pixel is the background."""
    if top == "." and bottom == ".":
        return " "
    tc = _COLORS.get(top, _BG)
    bc = _COLORS.get(bottom, _BG)
    tr, tg, tb = _hex_rgb(tc)
    br, bg, bb = _hex_rgb(bc)
    return f"\x1b[38;2;{tr};{tg};{tb};48;2;{br};{bg};{bb}m▀\x1b[0m"


def _cell_rich(top: str, bottom: str) -> str:
    if top == "." and bottom == ".":
        return " "
    tc = _COLORS.get(top, _BG)
    bc = _COLORS.get(bottom, _BG)
    return f"[{tc} on {bc}]▀[/]"


def shrimp_lines(fmt: str = "ansi") -> list[str]:
    """The pixel shrimp as half-block lines. fmt: 'ansi' (CLI) or 'rich' (Textual)."""
    grid = _SHRIMP
    if len(grid) % 2:  # pad to an even number of rows
        grid = [*grid, " " * len(grid[0])]
    width = max(len(r) for r in grid)
    grid = [r.ljust(width) for r in grid]
    lines = []
    for y in range(0, len(grid), 2):
        lines.append("".join(_cell_ansi(grid[y][x], grid[y + 1][x]) if fmt == "ansi"
                             else _cell_rich(grid[y][x], grid[y + 1][x])
                             for x in range(width)))
    return lines


def wordmark_lines() -> list[str]:
    """SHRIMP as 5 rows of block glyphs (uncoloured; the caller paints them)."""
    return [" ".join(_GLYPHS[ch][row] for ch in _WORD) for row in range(5)]


def wordmark_ansi(color: str = theme.CORAL) -> list[str]:
    return [theme.paint(line, color, bold=True) for line in wordmark_lines()]
