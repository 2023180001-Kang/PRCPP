import pico2d as p


CONTROL_KEYS = {p.SDLK_LEFT, p.SDLK_RIGHT, p.SDLK_UP, p.SDLK_DOWN, p.SDLK_r}


class Controls:
    def __init__(self):
        self.pressed = set()

    def handle_event(self, event):
        if event.key not in CONTROL_KEYS:
            return
        if event.type == p.SDL_KEYDOWN:
            self.pressed.add(event.key)
        elif event.type == p.SDL_KEYUP:
            self.pressed.discard(event.key)

    @property
    def direction(self):
        return (
            int(p.SDLK_RIGHT in self.pressed) - int(p.SDLK_LEFT in self.pressed),
            int(p.SDLK_UP in self.pressed) - int(p.SDLK_DOWN in self.pressed),
        )

    @property
    def running(self):
        return p.SDLK_r in self.pressed
