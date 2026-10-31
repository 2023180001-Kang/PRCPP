from contextlib import ExitStack, redirect_stderr
import io
from math import hypot
from pathlib import Path
import random
import unittest
from unittest.mock import Mock, call, patch

from character import Character, ANIMATION_FPS, FRAME_COUNT, STATE_ROWS
from controls import Controls, p
import main


def key_event(event_type, key):
    event = p.Event(event_type)
    event.key = key
    return event


class CharacterTests(unittest.TestCase):
    def test_initial_state(self):
        actor = Character(640, 360)
        self.assertEqual((actor.x, actor.y, actor.state), (640, 360, "IDLE"))
        self.assertTrue(actor.facing_right)
        self.assertEqual(actor.source_rect, (0, 0, 128, 128))

    def test_idle_does_not_move(self):
        actor = Character(640, 360)
        actor.update(3)
        self.assertEqual((actor.x, actor.y), (640, 360))

    def test_four_directions(self):
        for direction in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            with self.subTest(direction=direction):
                actor = Character(640, 360)
                actor.update(1, direction)
                self.assertEqual(actor.state, "WALK")
                self.assertEqual((actor.x, actor.y), (
                    640 + 160 * direction[0], 360 + 160 * direction[1],
                ))

    def test_run_is_twice_walk_speed(self):
        walk, run = Character(0, 0), Character(0, 0)
        walk.update(1, (1, 0))
        run.update(1, (1, 0), True)
        self.assertEqual(run.x, walk.x * 2)
        self.assertEqual(run.state, "RUN")

    def test_r_alone_is_idle(self):
        actor = Character(640, 360)
        actor.update(1, (0, 0), True)
        self.assertEqual((actor.state, actor.x, actor.y), ("IDLE", 640, 360))

    def test_state_transitions_without_repressing_direction(self):
        actor = Character(640, 360)
        for direction, running, expected in (
            ((1, 0), False, "WALK"), ((1, 0), True, "RUN"),
            ((1, 0), False, "WALK"), ((1, 0), True, "RUN"),
            ((0, 0), True, "IDLE"),
        ):
            actor.update(0.1, direction, running)
            self.assertEqual(actor.state, expected)
            self.assertEqual(actor.animation_time, 0)
            self.assertEqual(actor.frame, 0)

    def test_same_state_does_not_reset_animation(self):
        actor = Character(0, 0)
        actor.update(0.1, (1, 0))
        actor.update(0.25, (1, 0))
        self.assertEqual(actor.frame, 2)

    def test_all_animation_frames_and_rows(self):
        for state, row in STATE_ROWS.items():
            actor = Character(0, 0, state=state)
            for frame in range(FRAME_COUNT * 3):
                actor.animation_time = (frame + 0.1) / ANIMATION_FPS[state]
                self.assertEqual(actor.source_rect, ((frame % 6) * 128, row * 128, 128, 128))

    def test_final_sheet_layout_and_last_frame_bounds(self):
        self.assertEqual(STATE_ROWS, {"IDLE": 0, "WALK": 1, "RUN": 2})
        self.assertEqual(FRAME_COUNT, 6)
        for state, bottom in (("IDLE", 0), ("WALK", 128), ("RUN", 256)):
            actor = Character(0, 0, state=state)
            actor.animation_time = 5.1 / ANIMATION_FPS[state]
            self.assertEqual(actor.source_rect, (640, bottom, 128, 128))
            left, y, width, height = actor.source_rect
            self.assertLessEqual(left + width, 768)
            self.assertLessEqual(y + height, 384)

    def test_diagonal_distance(self):
        for running, distance in ((False, 320), (True, 640)):
            for direction in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                actor = Character(0, 0)
                actor.update(2, direction, running)
                self.assertAlmostEqual(hypot(actor.x, actor.y), distance)

    def test_30_and_60_fps_distance_and_animation(self):
        for direction, running in (((1, 0), False), ((1, 0), True), ((1, 1), True)):
            actors = []
            for fps in (30, 60):
                actor = Character(0, 0)
                actor.update(0, direction, running)
                for _ in range(fps * 2):
                    actor.update(1 / fps, direction, running)
                actors.append(actor)
            self.assertAlmostEqual(actors[0].x, actors[1].x)
            self.assertAlmostEqual(actors[0].y, actors[1].y)
            self.assertAlmostEqual(actors[0].animation_time, actors[1].animation_time)
            self.assertEqual(actors[0].frame, actors[1].frame)

    def test_facing_persists_when_idle_or_vertical(self):
        actor = Character(640, 360)
        for right in (False, True):
            actor.update(0.1, (1 if right else -1, 0))
            actor.update(0.1)
            actor.update(0.1, (0, 1))
            actor.update(0.1, (0, -1))
            self.assertEqual(actor.facing_right, right)

    def test_bounds_and_state_at_edge(self):
        for direction, expected in (((-1, -1), (64, 64)), ((1, 1), (1216, 656))):
            actor = Character(640, 360)
            actor.update(100, direction, True)
            actor.constrain(1280, 720)
            self.assertEqual((actor.x, actor.y), expected)
            self.assertEqual(actor.state, "RUN")


class ControlsTests(unittest.TestCase):
    def setUp(self):
        self.controls = Controls()

    def test_press_repeat_and_release(self):
        down = key_event(p.SDL_KEYDOWN, p.SDLK_LEFT)
        up = key_event(p.SDL_KEYUP, p.SDLK_LEFT)
        for event in (down, down):
            self.controls.handle_event(event)
        self.assertEqual(self.controls.direction, (-1, 0))
        for event in (up, up):
            self.controls.handle_event(event)
        self.assertEqual(self.controls.direction, (0, 0))

    def test_unrelated_events(self):
        self.controls.handle_event(key_event(p.SDL_KEYDOWN, p.SDLK_a))
        self.controls.handle_event(p.Event(p.SDL_QUIT))
        self.assertFalse(self.controls.pressed)

    def test_opposite_keys_cancel_per_axis(self):
        self.controls.pressed = {p.SDLK_LEFT, p.SDLK_RIGHT, p.SDLK_UP}
        self.assertEqual(self.controls.direction, (0, 1))
        self.controls.pressed.add(p.SDLK_DOWN)
        self.assertEqual(self.controls.direction, (0, 0))

    def test_cancellation_with_r_is_idle(self):
        self.controls.pressed = {p.SDLK_LEFT, p.SDLK_RIGHT, p.SDLK_r}
        actor = Character(640, 360)
        actor.update(1, self.controls.direction, self.controls.running)
        self.assertEqual(actor.state, "IDLE")

    def test_r_press_and_release(self):
        self.controls.handle_event(key_event(p.SDL_KEYDOWN, p.SDLK_r))
        self.assertTrue(self.controls.running)
        self.controls.handle_event(key_event(p.SDL_KEYUP, p.SDLK_r))
        self.assertFalse(self.controls.running)

    def test_focus_loss_and_regain(self):
        self.controls.pressed = {p.SDLK_RIGHT, p.SDLK_r}
        self.controls.reset_if_unfocused(True)
        self.assertTrue(self.controls.running)
        self.controls.reset_if_unfocused(False)
        self.controls.reset_if_unfocused(True)
        self.assertFalse(self.controls.pressed)
        self.assertEqual(self.controls.direction, (0, 0))


class BookSpawnTests(unittest.TestCase):
    def test_counts_bounds_and_no_overlap_across_seeds(self):
        counts = set()
        layouts = set()
        for seed in range(100):
            with patch.object(main, "random", random.Random(seed)):
                books = main.spawn_books()
            counts.add(len(books))
            layouts.add(tuple(books))
            self.assertIn(len(books), (3, 4, 5))
            for index, (x, y) in enumerate(books):
                self.assertTrue(main.BOOK_SIZE / 2 <= x <= main.WINDOW_WIDTH - main.BOOK_SIZE / 2)
                self.assertTrue(main.BOOK_SIZE / 2 <= y <= main.WINDOW_HEIGHT - main.BOOK_SIZE / 2)
                for other_x, other_y in books[:index]:
                    self.assertTrue(abs(x - other_x) >= main.BOOK_SIZE or abs(y - other_y) >= main.BOOK_SIZE)
        self.assertEqual(counts, {3, 4, 5})
        self.assertGreater(len(layouts), 1)


class MainTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.mocks = {}
        for name in (
            "open_canvas", "close_canvas", "hide_lattice", "clear_canvas",
            "update_canvas", "SDL_DestroyTexture",
        ):
            self.mocks[name] = self.stack.enter_context(patch.object(p, name))
        self.stack.enter_context(patch.object(main, "sleep"))
        self.books = [(160, 160), (384, 272), (944, 496)]
        self.spawner = self.stack.enter_context(patch.object(main, "spawn_books", return_value=self.books))
        self.stack.enter_context(patch.object(p, "SDL_GetKeyboardFocus", return_value=True))
        self.background = Mock(w=1672, h=941)
        self.sprite = Mock(w=768, h=384)
        self.book = Mock(w=1254, h=1254)
        self.loader = self.stack.enter_context(patch.object(
            p, "load_image", side_effect=[self.background, self.sprite, self.book],
        ))

    def run_events(self, batches):
        with patch.object(p, "get_events", side_effect=batches):
            return main.main()

    def test_quit_and_esc_cleanup(self):
        for event in (p.Event(p.SDL_QUIT), key_event(p.SDL_KEYDOWN, p.SDLK_ESCAPE)):
            self.loader.side_effect = [self.background, self.sprite, self.book]
            self.assertEqual(self.run_events([[event]]), 0)
        self.assertEqual(self.mocks["close_canvas"].call_count, 2)

    def test_render_order_dimensions_and_single_load(self):
        calls = Mock()
        calls.attach_mock(self.background.draw, "background")
        calls.attach_mock(self.book.draw, "book")
        calls.attach_mock(self.sprite.clip_composite_draw, "sprite")
        self.assertEqual(self.run_events([[], [], [p.Event(p.SDL_QUIT)]]), 0)
        self.assertEqual(self.loader.call_count, 3)
        self.assertEqual([c[0] for c in calls.mock_calls], ["background", "book", "book", "book", "sprite"] * 2)
        self.spawner.assert_called_once_with()
        self.assertEqual(self.book.draw.call_args_list, [call(x, y, 96, 96) for x, y in self.books] * 2)
        _, _, width, height = self.background.draw.call_args.args
        self.assertAlmostEqual(width / height, 1672 / 941)
        self.assertEqual(self.sprite.clip_composite_draw.call_args.args[-2:], (128, 128))

    def test_left_input_reaches_flipped_renderer(self):
        self.run_events([[key_event(p.SDL_KEYDOWN, p.SDLK_LEFT)], [p.Event(p.SDL_QUIT)]])
        self.assertEqual(self.sprite.clip_composite_draw.call_args.args[5], "h")

    def test_only_final_sprite_is_loaded(self):
        self.run_events([[], [p.Event(p.SDL_QUIT)]])
        self.assertEqual(self.loader.call_args_list, [
            call(str(main.ASSET_DIR / "arena.png")),
            call(str(main.ASSET_DIR / "tino_sprite_pico2d_final.png")),
            call(str(main.ASSET_DIR / "Book_Item.png")),
        ])

    def test_missing_final_sprite_does_not_fall_back(self):
        output = io.StringIO()
        with patch.object(Path, "is_file", side_effect=[True, False]), redirect_stderr(output):
            self.assertEqual(main.main(), 1)
        self.assertIn("tino_sprite_pico2d_final.png", output.getvalue())
        self.loader.assert_called_once_with(str(main.ASSET_DIR / "arena.png"))
        self.mocks["close_canvas"].assert_called_once()

    def test_missing_book_fails_cleanly(self):
        textures = [self.background.texture, self.sprite.texture]
        output = io.StringIO()
        with patch.object(Path, "is_file", side_effect=[True, True, False]), redirect_stderr(output):
            self.assertEqual(main.main(), 1)
        self.assertIn("Book_Item.png", output.getvalue())
        self.assertEqual(self.mocks["SDL_DestroyTexture"].call_args_list, [call(t) for t in textures])
        self.mocks["close_canvas"].assert_called_once()

    def test_corrupt_book_fails_cleanly(self):
        self.loader.side_effect = [self.background, self.sprite, OSError("invalid image")]
        output = io.StringIO()
        with redirect_stderr(output):
            self.assertEqual(main.main(), 1)
        self.assertIn("Book_Item.png", output.getvalue())
        self.assertEqual(self.mocks["SDL_DestroyTexture"].call_count, 2)
        self.mocks["close_canvas"].assert_called_once()

    def test_corrupt_final_sprite_does_not_fall_back(self):
        texture = self.background.texture
        self.loader.side_effect = [self.background, OSError("invalid image")]
        output = io.StringIO()
        with redirect_stderr(output):
            self.assertEqual(main.main(), 1)
        self.assertIn("tino_sprite_pico2d_final.png", output.getvalue())
        self.assertEqual(self.loader.call_count, 2)
        self.mocks["SDL_DestroyTexture"].assert_called_once_with(texture)
        self.mocks["close_canvas"].assert_called_once()

    def test_missing_resource_path_and_failure_code(self):
        output = io.StringIO()
        with patch.object(main, "ASSET_DIR", Path("missing-test-assets").resolve()), redirect_stderr(output):
            self.assertEqual(main.main(), 1)
        self.assertIn("arena.png", output.getvalue())
        self.mocks["close_canvas"].assert_called_once()

    def test_load_failure_includes_path(self):
        self.loader.side_effect = OSError("invalid image")
        with self.assertRaisesRegex(OSError, "arena.png"):
            main.load_asset("arena.png")

    def test_invalid_sprite_size_fails_cleanly(self):
        self.sprite.w = 767
        output = io.StringIO()
        with redirect_stderr(output):
            self.assertEqual(main.main(), 1)
        self.assertIn("tino_sprite_pico2d_final.png", output.getvalue())
        self.mocks["close_canvas"].assert_called_once()

    def test_unexpected_render_exception_still_closes(self):
        self.sprite.clip_composite_draw.side_effect = RuntimeError("render failed")
        with self.assertRaisesRegex(RuntimeError, "render failed"):
            self.run_events([[]])
        self.mocks["close_canvas"].assert_called_once()

    def test_textures_released_before_renderer_even_with_traceback(self):
        textures = [self.background.texture, self.sprite.texture, self.book.texture]
        destroyed = []
        self.mocks["SDL_DestroyTexture"].side_effect = destroyed.append

        def check_close():
            self.assertEqual(destroyed, textures)
            self.assertIsNone(self.background.texture)
            self.assertIsNone(self.sprite.texture)
            self.assertIsNone(self.book.texture)

        self.mocks["close_canvas"].side_effect = check_close
        self.sprite.clip_composite_draw.side_effect = RuntimeError("render failed")
        with self.assertRaisesRegex(RuntimeError, "render failed"):
            self.run_events([[]])
        self.mocks["close_canvas"].assert_called_once()


if __name__ == "__main__":
    unittest.main()
