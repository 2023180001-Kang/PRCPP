from time import perf_counter, sleep
from pathlib import Path
import sys

import pico2d as p

from character import (
    Character, DRAW_HEIGHT, DRAW_WIDTH, FRAME_COUNT, FRAME_HEIGHT, FRAME_WIDTH, STATE_ROWS,
)
from controls import Controls


WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
TARGET_FPS = 60
ASSET_DIR = Path(__file__).resolve().parent


def load_asset(name):
    path = ASSET_DIR / name
    if not path.is_file():
        raise OSError(f"Missing resource: {path}")
    try:
        return p.load_image(str(path))
    except OSError as error:
        raise OSError(f"Cannot load resource: {path}") from error


def main():
    p.open_canvas(WINDOW_WIDTH, WINDOW_HEIGHT)
    background = sprite = None
    try:
        p.hide_lattice()
        background = load_asset("arena.png")
        sprite = load_asset("tino_sprite_pico2d.png")
        expected_size = (FRAME_WIDTH * FRAME_COUNT, FRAME_HEIGHT * len(STATE_ROWS))
        if (sprite.w, sprite.h) != expected_size:
            raise ValueError(
                f"Invalid sprite size: {ASSET_DIR / 'tino_sprite_pico2d.png'}; "
                f"expected {expected_size}, got {(sprite.w, sprite.h)}"
            )
        background_scale = min(WINDOW_WIDTH / background.w, WINDOW_HEIGHT / background.h)
        character = Character(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)
        controls = Controls()
        running = True
        previous_time = perf_counter()
        while running:
            frame_start = perf_counter()
            dt = frame_start - previous_time
            previous_time = frame_start
            for event in p.get_events():
                controls.handle_event(event)
                if event.type == p.SDL_QUIT:
                    running = False
                elif event.type == p.SDL_KEYDOWN and event.key == p.SDLK_ESCAPE:
                    running = False
            if not running:
                break
            # pico2d filters out SDL window-focus events; query focus after polling.
            controls.reset_if_unfocused(bool(p.SDL_GetKeyboardFocus()))
            character.update(dt, controls.direction, controls.running)
            character.constrain(WINDOW_WIDTH, WINDOW_HEIGHT)
            p.clear_canvas()
            background.draw(
                WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2,
                background.w * background_scale, background.h * background_scale,
            )
            sprite.clip_composite_draw(
                *character.source_rect, 0, "" if character.facing_right else "h",
                character.x, character.y, DRAW_WIDTH, DRAW_HEIGHT,
            )
            p.update_canvas()
            sleep(max(0, 1 / TARGET_FPS - (perf_counter() - frame_start)))
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    finally:
        # Image destructors must run while their SDL renderer still exists.
        background = sprite = None
        p.close_canvas()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
