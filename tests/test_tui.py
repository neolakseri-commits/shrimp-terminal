"""TUI smoke test - skipped when Textual is not installed.

Uses Textual's headless `run_test` pilot, wrapped in asyncio.run so the suite
needs no pytest-asyncio plugin.
"""

from __future__ import annotations

import asyncio

import pytest

textual = pytest.importorskip("textual")

from textual.widgets import ContentSwitcher, DataTable

from shrimp.tui.app import FeedView, FlowView, MapView, RadarView, ShrimpApp


def test_tui_streams_and_switches_all_views():
    async def scenario() -> None:
        app = ShrimpApp()
        async with app.run_test() as pilot:
            await pilot.pause(0.05)
            app._tick()
            app._tick()
            await pilot.pause(0.02)

            feed = app.query_one(FeedView).query_one(DataTable)
            assert feed.row_count >= 2

            for key, expect in [("r", "radar"), ("l", "flow"), ("m", "map"), ("f", "feed")]:
                await pilot.press(key)
                await pilot.pause(0.01)
                assert app.query_one(ContentSwitcher).current == expect

            await pilot.press("space")
            assert app._paused is True

            # each view renders its body without raising
            app.query_one(RadarView)._board()
            app.query_one(FlowView)._diagram()
            app.query_one(MapView)._map()

    asyncio.run(scenario())
