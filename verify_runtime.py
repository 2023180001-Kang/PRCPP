"""Exercise the real SDL renderer/event queue without manual keyboard input."""

import argparse
from contextlib import nullcontext
import ctypes
from time import perf_counter
from unittest.mock import patch

from character import Character
import main


def verify(seconds, fps, assume_focus=False):
    p = main.p
    original_events = p.get_events
    original_present = p.update_canvas
    original_load = main.load_asset
    original_spawn = main.spawn_books
    books = []
    book_draws = []

    def spawn_books():
        books.extend(original_spawn())
        assert 3 <= len(books) <= 5
        return books

    def load_asset(name):
        image = original_load(name)
        if name == "Book_Item.png":
            original_draw = image.draw

            def draw(*args):
                original_draw(*args)
                book_draws.append(args)

            image.draw = draw
        return image

    actors = []
    presented = []
    states = set()
    facings = set()
    animation_frames = {state: set() for state in ("IDLE", "WALK", "RUN")}
    movement_checks = 0
    previous = None
    stage = -1
    start = None
    schedule = (
        set(), {p.SDLK_RIGHT}, {p.SDLK_RIGHT, p.SDLK_r},
        {p.SDLK_RIGHT}, {p.SDLK_r}, {p.SDLK_LEFT},
        {p.SDLK_LEFT, p.SDLK_UP, p.SDLK_r},
        {p.SDLK_LEFT, p.SDLK_RIGHT}, {p.SDLK_DOWN}, set(),
    )
    held = set()

    def create_actor(*args):
        actor = Character(*args)
        actors.append(actor)
        return actor

    def push_key(key, event_type):
        event = p.SDL_Event()
        event.type = event_type
        event.key.keysym.sym = key
        event.key.state = p.SDL_PRESSED if event_type == p.SDL_KEYDOWN else p.SDL_RELEASED
        if p.SDL_PushEvent(ctypes.byref(event)) != 1:
            raise RuntimeError("SDL key event injection failed")

    def get_events():
        nonlocal start, stage, held
        now = perf_counter()
        if start is None:
            start = now
        elapsed = now - start
        if elapsed >= seconds:
            event = p.SDL_Event()
            event.type = p.SDL_QUIT
            if p.SDL_PushEvent(ctypes.byref(event)) != 1:
                raise RuntimeError("SDL quit event injection failed")
        else:
            next_stage = int(elapsed / 0.5) % len(schedule)
            if next_stage != stage:
                keys = schedule[next_stage]
                for key in held - keys:
                    push_key(key, p.SDL_KEYUP)
                for key in keys - held:
                    push_key(key, p.SDL_KEYDOWN)
                held = keys
                stage = next_stage
        return original_events()

    def present():
        nonlocal movement_checks, previous
        original_present()
        assert book_draws == [(x, y, main.BOOK_SIZE, main.BOOK_SIZE) for x, y in books]
        book_draws.clear()
        if actors:
            actor = actors[0]
            assert 64 <= actor.x <= 1216 and 64 <= actor.y <= 656
            assert 0 <= actor.frame < 6
            dx = int(p.SDLK_RIGHT in held) - int(p.SDLK_LEFT in held)
            dy = int(p.SDLK_UP in held) - int(p.SDLK_DOWN in held)
            expected = "IDLE" if not (dx or dy) else "RUN" if p.SDLK_r in held else "WALK"
            assert actor.state == expected, (stage, actor.state, expected)
            if previous is not None and previous[2] == stage:
                old_x, old_y, _ = previous
                if not dx:
                    assert actor.x == old_x
                elif 64 < old_x < 1216:
                    assert (actor.x - old_x) * dx > 0, "Horizontal movement stalled"
                    movement_checks += 1
                if not dy:
                    assert actor.y == old_y
                elif 64 < old_y < 656:
                    assert (actor.y - old_y) * dy > 0, "Vertical movement stalled"
                    movement_checks += 1
            previous = (actor.x, actor.y, stage)
            states.add(actor.state)
            facings.add(actor.facing_right)
            animation_frames[actor.state].add(actor.frame)
            presented.append(perf_counter())

    with (
        patch.object(main, "TARGET_FPS", fps),
        patch.object(main, "spawn_books", side_effect=spawn_books),
        patch.object(main, "load_asset", side_effect=load_asset),
        patch.object(main, "Character", side_effect=create_actor),
        patch.object(p, "get_events", side_effect=get_events),
        patch.object(p, "update_canvas", side_effect=present),
        patch.object(p, "SDL_GetKeyboardFocus", return_value=True) if assume_focus else nullcontext(),
    ):
        result = main.main()
    assert result == 0, f"Application exit code: {result}"
    assert states == {"IDLE", "WALK", "RUN"}, f"Missing states (check window focus): {states}"
    assert facings == {False, True}, f"Missing facing directions: {facings}"
    assert movement_checks > 0, "No unobstructed movement verified"
    assert all(len(frames) > 1 for frames in animation_frames.values()), animation_frames
    measured_fps = (len(presented) - 1) / (presented[-1] - presented[0])
    print(f"PASS: seconds={seconds}, frames={len(presented)}, target_fps={fps}, measured_fps={measured_fps:.2f}")
    print(f"States={sorted(states)}, both facings, frame bounds, screen bounds, native QUIT: PASS")
    print(f"Per-frame state and displacement checks={movement_checks}, all three animations advancing: PASS")
    print(f"Books={len(books)}, fixed spawn positions drawn every frame: PASS")
    print(f"Focus check: {'OVERRIDDEN (manual focus acceptance still required)' if assume_focus else 'native'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=5)
    parser.add_argument("--fps", type=int, choices=(30, 60), default=60)
    parser.add_argument("--assume-focus", action="store_true", help="Override focus only for noninteractive automation")
    args = parser.parse_args()
    if args.seconds < 5:
        parser.error("--seconds must be at least 5 to exercise the full input cycle")
    verify(args.seconds, args.fps, args.assume_focus)
