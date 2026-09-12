"""TUI smoke test - skipped when Textual is not installed.

Uses Textual's headless `run_test` pilot, wrapped in asyncio.run so the suite
needs no pytest-asyncio plugin.
"""

from __future__ import annotations

import asyncio

import pytest

textual = pytest.importorskip("textual")

from textual.widgets import ContentSwitcher, DataTable

from shrimp.tui.app import FlowView, MapView, RadarView, ShrimpApp, Tape


def test_tui_streams_tape_and_switches_all_views():
    async def scenario() -> None:
        app = ShrimpApp()
        async with app.run_test() as pilot:
            await pilot.pause(0.05)
            app._tick()
            app._tick()
            await pilot.pause(0.02)

            tape = app.query_one(Tape).query_one(DataTable)
            assert tape.row_count >= 2

            # default view is MAP; switch through every view by hotkey
            for key, expect in [("1", "radar"), ("2", "flow"), ("3", "map")]:
                await pilot.press(key)
                await pilot.pause(0.01)
                assert app.query_one(ContentSwitcher).current == expect

            await pilot.press("space")
            assert app._paused is True

            # every center view renders its body without raising
            app.query_one(RadarView).render()
            app.query_one(FlowView).render()
            app.query_one(MapView).render()

    asyncio.run(scenario())
