from dataclasses import dataclass


FRAME_WIDTH = 128
FRAME_HEIGHT = 128
FRAME_COUNT = 6
DRAW_WIDTH = 128
DRAW_HEIGHT = 128
# pico2d clip coordinates start at the bottom of the image.
STATE_ROWS = {"IDLE": 0, "WALK": 1, "RUN": 2}
ANIMATION_FPS = {"IDLE": 6, "WALK": 10, "RUN": 14}
WALK_SPEED = 160


@dataclass
class Character:
    x: float
    y: float
    state: str = "IDLE"
    facing_right: bool = True
    animation_time: float = 0.0

    def update(self, dt, direction=(0, 0)):
        dx, dy = direction
        next_state = "WALK" if dx or dy else "IDLE"
        if next_state != self.state:
            self.state = next_state
            self.animation_time = 0.0
        else:
            self.animation_time += dt
        self.x += dx * WALK_SPEED * dt
        self.y += dy * WALK_SPEED * dt

    @property
    def frame(self):
        return int(self.animation_time * ANIMATION_FPS[self.state]) % FRAME_COUNT

    @property
    def source_rect(self):
        return (
            self.frame * FRAME_WIDTH,
            STATE_ROWS[self.state] * FRAME_HEIGHT,
            FRAME_WIDTH,
            FRAME_HEIGHT,
        )
