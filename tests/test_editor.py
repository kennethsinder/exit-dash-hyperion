"""Level editor: the data model, persistence round-trip, and the editor->play path."""

from __future__ import annotations

import pygame

from exit_dash.core.app import Application
from exit_dash.core.scene import Push, SceneManager
from exit_dash.core.settings import Settings
from exit_dash.scenes.level import LevelScene
from exit_dash.world.editing import GRID, EditorModel
from exit_dash.world.level import DoorRec, PlatformRec
from exit_dash.world.loader import MAX_PLATFORMS


def test_blank_level_is_playable():
    ok, _ = EditorModel.blank().playability()
    assert ok


def test_add_then_erase_platform():
    model = EditorModel.blank()
    n = len(model.platforms)
    assert model.add_platform(2000, 500, 200)
    assert len(model.platforms) == n + 1
    assert model.erase_at(2010, 510)  # a point inside the new platform
    assert len(model.platforms) == n


def test_placements_snap_to_grid():
    model = EditorModel.blank()
    model.add_platform(207, 493, 100)
    placed = model.platforms[-1]
    assert placed.x % GRID == 0
    assert placed.y % GRID == 0


def test_platform_slot_limit_enforced():
    model = EditorModel(door=DoorRec(0, 0))
    for i in range(MAX_PLATFORMS):
        assert model.add_platform(i * 100, 500, 100)
    assert not model.add_platform(9999, 500, 100)
    assert len(model.platforms) == MAX_PLATFORMS


def test_round_trips_through_loader(tmp_path):
    model = EditorModel.blank()
    model.add_block(800, 400, coin=False)
    model.set_pool(1500, 500, 300, 240)
    model.fences = False
    path = tmp_path / "lvl_custom.dat"
    model.save(path)

    reloaded = EditorModel.load(path)
    assert len(reloaded.platforms) == len(model.platforms)
    assert len(reloaded.blocks) == len(model.blocks)
    assert reloaded.pool is not None
    assert reloaded.fences is False
    assert reloaded.door == model.door


def test_too_few_platforms_is_unplayable():
    model = EditorModel(
        platforms=[PlatformRec(0, 0, 100), PlatformRec(0, 0, 100)],
        door=DoorRec(0, 0),
    )
    ok, reason = model.playability()
    assert not ok
    assert "platform" in reason


def test_identical_x_platforms_is_unplayable():
    # All non-spawn platforms sharing an x would hang generate_mobs; must be rejected.
    model = EditorModel(
        platforms=[PlatformRec(0, 0, 100), PlatformRec(500, 100, 100), PlatformRec(500, 300, 100)],
        door=DoorRec(0, 0),
    )
    ok, _ = model.playability()
    assert not ok


def test_editor_scene_places_and_can_test_play(pygame_ready):
    from exit_dash.scenes.editor import EditorScene

    scene = EditorScene(Settings(music_enabled=False), audio=False)
    manager = SceneManager(scene)

    before = len(scene.model.platforms)
    manager.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(400, 300)))
    assert len(scene.model.platforms) == before + 1

    # Rendering a frame must not raise.
    scene.draw(pygame.Surface((1280, 720)), 0.0)

    # The blank level is playable, so test-play pushes a (sandbox) level scene.
    transition = scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p))
    assert isinstance(transition, Push)


def test_custom_level_runs_headless():
    # The full editor->play path: a level built from editor data boots and runs without
    # crashing or hanging (the latter being the generate_mobs risk playability() guards).
    data = EditorModel.blank().to_level_data()
    app = Application(headless=True)
    scene = LevelScene(
        1,
        1,
        Settings(music_enabled=False),
        audio=False,
        final_level=1,
        custom_data=data,
        sandbox=True,
    )
    try:
        frames = app.run(scene, max_frames=60)
    finally:
        app.quit()
    assert frames == 60
