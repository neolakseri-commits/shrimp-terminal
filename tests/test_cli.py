"""The CLI runs and each command prints its section without color codes."""

from __future__ import annotations

import os

import pytest

from shrimp import cli

# Force plain output so assertions are not brittle against ANSI escapes.
os.environ["NO_COLOR"] = "1"


@pytest.mark.parametrize(
    "argv, marker",
    [
        ([], "commands:"),
        (["feed"], "FEED"),
        (["radar"], "RADAR"),
        (["rotations"], "ROTATIONS"),
    ],
)
def test_commands_run_and_print_their_section(argv, marker, capsys):
    code = cli.main(argv)
    out = capsys.readouterr().out
    assert code == 0
    assert marker in out


def test_feed_shows_a_transaction_hash(capsys):
    cli.main(["feed"])
    out = capsys.readouterr().out
    assert "0x" in out  # tx hashes are always visible


def test_rotations_flags_ambiguous_and_hides_it_from_the_weight(capsys):
    cli.main(["rotations"])
    out = capsys.readouterr().out
    assert "ambiguous" in out
    assert "not counted" in out
