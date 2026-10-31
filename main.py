from time import perf_counter, sleep
from pathlib import Path
import random
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
SPRITE_FILENAME = "tino_sprite_pico2d_final.png"
BOOK_FILENAME = "algorithm_book_pico2d_128.png"
BOOK_SIZE = 96


def spawn_books():
    # Sample without replacement from spaced slots so books cannot overlap.
    positions = [
        (x, y)
        for x in range(BOOK_SIZE // 2, WINDOW_WIDTH - BOOK_SIZE // 2 + 1, BOOK_SIZE + 16)
        for y in range(BOOK_SIZE // 2, WINDOW_HEIGHT - BOOK_SIZE // 2 + 1, BOOK_SIZE + 16)
    ]
    return random.sample(positions, random.randint(3, 5))


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
    background = sprite = book = None
    try:
        p.hide_lattice()
        background = load_asset("arena.png")
        sprite = load_asset(SPRITE_FILENAME)
        expected_size = (FRAME_WIDTH * FRAME_COUNT, FRAME_HEIGHT * len(STATE_ROWS))
        if (sprite.w, sprite.h) != expected_size:
            raise ValueError(
                f"Invalid sprite size: {ASSET_DIR / SPRITE_FILENAME}; "
                f"expected {expected_size}, got {(sprite.w, sprite.h)}"
            )
        background_scale = min(WINDOW_WIDTH / background.w, WINDOW_HEIGHT / background.h)
        book = load_asset(BOOK_FILENAME)
        books = spawn_books()
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
            for x, y in books:
                book.draw(x, y, BOOK_SIZE, BOOK_SIZE)
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
        # Tracebacks may keep Image instances alive beyond renderer shutdown.
        for image in (background, sprite, book):
            if image is not None:
                p.SDL_DestroyTexture(image.texture)
                image.texture = None
        background = sprite = book = None
        p.close_canvas()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
