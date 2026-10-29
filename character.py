from dataclasses import dataclass
from math import hypot


FRAME_WIDTH = 128
FRAME_HEIGHT = 128
FRAME_COUNT = 6
DRAW_WIDTH = 128
DRAW_HEIGHT = 128
# pico2d clip coordinates start at the bottom of the image.
STATE_ROWS = {"IDLE": 0, "WALK": 1, "RUN": 2}
ANIMATION_FPS = {"IDLE": 6, "WALK": 10, "RUN": 14}
WALK_SPEED = 160
RUN_SPEED = 320


@dataclass
class Character:
    x: float
    y: float
    state: str = "IDLE"
    facing_right: bool = True
    animation_time: float = 0.0

    def update(self, dt, direction=(0, 0), running=False):
        dx, dy = direction
        if dx:
            self.facing_right = dx > 0
        if not (dx or dy):
            next_state = "IDLE"
        else:
            next_state = "RUN" if running else "WALK"
        if next_state != self.state:
            self.state = next_state
            self.animation_time = 0.0
        else:
            self.animation_time += dt
        length = hypot(dx, dy)
        if length:
            dx, dy = dx / length, dy / length
        speed = RUN_SPEED if running else WALK_SPEED
        self.x += dx * speed * dt
        self.y += dy * speed * dt

    def constrain(self, width, height):
        self.x = max(DRAW_WIDTH / 2, min(self.x, width - DRAW_WIDTH / 2))
        self.y = max(DRAW_HEIGHT / 2, min(self.y, height - DRAW_HEIGHT / 2))

    @property
    def frame(self):
        # Avoid a one-frame lag from accumulated rounding at exact frame boundaries.
        return int(self.animation_time * ANIMATION_FPS[self.state] + 1e-9) % FRAME_COUNT

    @property
    def source_rect(self):
        return (
            self.frame * FRAME_WIDTH,
            STATE_ROWS[self.state] * FRAME_HEIGHT,
            FRAME_WIDTH,
            FRAME_HEIGHT,
        )
