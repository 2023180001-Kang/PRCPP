from time import perf_counter, sleep
from pathlib import Path

import pico2d as p

from character import Character, DRAW_HEIGHT, DRAW_WIDTH


WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
TARGET_FPS = 60
ASSET_DIR = Path(__file__).resolve().parent


def main():
    p.open_canvas(WINDOW_WIDTH, WINDOW_HEIGHT)
    try:
        p.hide_lattice()
        background = p.load_image(str(ASSET_DIR / "arena.png"))
        sprite = p.load_image(str(ASSET_DIR / "tino_sprite_pico2d.png"))
        background_scale = min(WINDOW_WIDTH / background.w, WINDOW_HEIGHT / background.h)
        character = Character(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)
        running = True
        previous_time = perf_counter()
        while running:
            frame_start = perf_counter()
            dt = frame_start - previous_time
            previous_time = frame_start
            for event in p.get_events():
                if event.type == p.SDL_QUIT:
                    running = False
                elif event.type == p.SDL_KEYDOWN and event.key == p.SDLK_ESCAPE:
                    running = False
            if not running:
                break
            p.clear_canvas()
            background.draw(
                WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2,
                background.w * background_scale, background.h * background_scale,
            )
            sprite.clip_draw(
                *character.source_rect, character.x, character.y, DRAW_WIDTH, DRAW_HEIGHT,
            )
            p.update_canvas()
            sleep(max(0, 1 / TARGET_FPS - (perf_counter() - frame_start)))
    finally:
        p.close_canvas()


if __name__ == "__main__":
    main()
