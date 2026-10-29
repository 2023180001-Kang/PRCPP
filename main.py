import pico2d as p


WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720


def main():
    p.open_canvas(WINDOW_WIDTH, WINDOW_HEIGHT)
    try:
        p.hide_lattice()
        running = True
        while running:
            for event in p.get_events():
                if event.type == p.SDL_QUIT:
                    running = False
                elif event.type == p.SDL_KEYDOWN and event.key == p.SDLK_ESCAPE:
                    running = False
            if not running:
                break
            p.clear_canvas()
            p.update_canvas()
            p.delay(0.01)
    finally:
        p.close_canvas()


if __name__ == "__main__":
    main()
