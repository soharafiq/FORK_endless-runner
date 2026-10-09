
import os
import pygame
from .player import Player
from .obstacle import Obstacle

# Game colours
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (135, 206, 235)
PLAYER_BLUE = (30, 80, 200)
BROWN = (120, 80, 40)
DARK_GREEN = (30, 100, 30)
RED = (255, 80, 80)


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.ground_y = height - 40

        self.title_font = pygame.font.SysFont(
            "Arial", 48, bold=True
        )
        self.font = pygame.font.SysFont("Arial", 30)
        self.menu_font = pygame.font.SysFont("Arial", 25)

        # Load sound effects.
        self.sounds = {}
        self.sound_enabled = False

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            assets_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "assets",
            )

            self.sounds["jump"] = pygame.mixer.Sound(
                os.path.join(assets_dir, "jump.wav")
            )
            self.sounds["score"] = pygame.mixer.Sound(
                os.path.join(assets_dir, "score.wav")
            )
            self.sounds["game_over"] = pygame.mixer.Sound(
                os.path.join(assets_dir, "game_over.wav")
            )

            self.sound_enabled = True

        except (pygame.error, OSError) as error:
            print("Sound effects unavailable:", error)

        self.difficulties = {
            "Easy": {
                "speed": 4,
                "max_speed": 7,
                "spawn_interval": 90,
            },
            "Medium": {
                "speed": 6,
                "max_speed": 12,
                "spawn_interval": 70,
            },
            "Hard": {
                "speed": 9,
                "max_speed": 16,
                "spawn_interval": 50,
            },
        }

        self.difficulty = "Medium"
        self.reset_game()

    def play_sound(self, name):
        if self.sound_enabled and name in self.sounds:
            self.sounds[name].play()

    def reset_game(self):
        settings = self.difficulties[self.difficulty]

        self.player = Player(80, self.ground_y)

        self.speed = settings["speed"]
        self.max_speed = settings["max_speed"]
        self.speed_increase_per_frame = 0.003

        self.spawn_interval = settings["spawn_interval"]
        self._spawn_timer = 0
        self.obstacles = []

        self.distance = 0
        self.score = 0
        self.game_over = False

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if not self.game_over:
            if event.key in (
                pygame.K_SPACE,
                pygame.K_UP,
                pygame.K_w,
            ):
                # Play the sound only when a jump actually starts.
                if self.player.jump():
                    self.play_sound("jump")
            return

        # Replay with the selected difficulty.
        if event.key == pygame.K_1:
            self.difficulty = "Easy"
            self.reset_game()

        elif event.key == pygame.K_2:
            self.difficulty = "Medium"
            self.reset_game()

        elif event.key == pygame.K_3:
            self.difficulty = "Hard"
            self.reset_game()

        elif event.key in (pygame.K_ESCAPE, pygame.K_q):
            pygame.event.post(
                pygame.event.Event(pygame.QUIT)
            )

    def handle_input(self):
        pass

    def update(self):
        if self.game_over:
            return

        # Gradually increase speed up to the selected limit.
        self.speed = min(
            self.speed + self.speed_increase_per_frame,
            self.max_speed,
        )

        self.player.update()

        # Spawn obstacles.
        self._spawn_timer += 1

        if self._spawn_timer >= self.spawn_interval:
            self._spawn_timer = 0
            self.obstacles.append(
                Obstacle(
                    self.width,
                    self.ground_y,
                    self.speed,
                )
            )

        # Remember previous positions before moving obstacles.
        for obstacle in self.obstacles:
            obstacle.previous_x = obstacle.x
            obstacle.move()
            obstacle.speed = self.speed

        player_rect = self.player.rect()

        # Check collisions, including the path travelled this frame.
        for obstacle in self.obstacles:
            obstacle_rect = obstacle.rect()

            if obstacle_rect.colliderect(player_rect):
                self.game_over = True
                self.play_sound("game_over")
                return

            previous_x = obstacle.previous_x

            if obstacle.x < previous_x:
                swept_rect = pygame.Rect(
                    obstacle.x,
                    obstacle.y,
                    previous_x + obstacle.width - obstacle.x,
                    obstacle.height,
                )

                if swept_rect.colliderect(player_rect):
                    self.game_over = True
                    self.play_sound("game_over")
                    return

        # Award points when obstacles pass the player.
        for obstacle in self.obstacles:
            if (
                not obstacle.scored
                and obstacle.x + obstacle.width < self.player.x
            ):
                obstacle.scored = True
                self.score += 1
                self.play_sound("score")

        # Remove obstacles that have left the screen.
        self.obstacles = [
            obstacle
            for obstacle in self.obstacles
            if not obstacle.off_screen()
        ]

        self.distance += self.speed

    def render(self, screen):
        screen.fill(SKY_BLUE)

        # Ground.
        pygame.draw.line(
            screen,
            BROWN,
            (0, self.ground_y),
            (self.width, self.ground_y),
            4,
        )

        # Player and obstacles.
        pygame.draw.rect(
            screen,
            PLAYER_BLUE,
            self.player.rect(),
        )

        for obstacle in self.obstacles:
            pygame.draw.rect(
                screen,
                DARK_GREEN,
                obstacle.rect(),
            )

        # Score and difficulty.
        score_text = self.font.render(
            f"Score: {self.score}", True, BLACK
        )
        difficulty_text = self.menu_font.render(
            f"Difficulty: {self.difficulty}", True, BLACK
        )

        screen.blit(score_text, (10, 10))
        screen.blit(difficulty_text, (10, 45))

        if self.game_over:
            overlay = pygame.Surface(
                (self.width, self.height),
                pygame.SRCALPHA,
            )
            overlay.fill((0, 0, 0, 190))
            screen.blit(overlay, (0, 0))

            messages = [
                (
                    self.title_font.render(
                        "GAME OVER", True, RED
                    ),
                    self.height // 2 - 125,
                ),
                (
                    self.font.render(
                        f"Final Score: {self.score}",
                        True,
                        WHITE,
                    ),
                    self.height // 2 - 70,
                ),
                (
                    self.menu_font.render(
                        "Choose a difficulty to play again",
                        True,
                        WHITE,
                    ),
                    self.height // 2 - 20,
                ),
                (
                    self.menu_font.render(
                        "1 - Easy", True, WHITE
                    ),
                    self.height // 2 + 25,
                ),
                (
                    self.menu_font.render(
                        "2 - Medium", True, WHITE
                    ),
                    self.height // 2 + 60,
                ),
                (
                    self.menu_font.render(
                        "3 - Hard", True, WHITE
                    ),
                    self.height // 2 + 95,
                ),
                (
                    self.menu_font.render(
                        "ESC / Q - Exit", True, WHITE
                    ),
                    self.height // 2 + 140,
                ),
            ]

            for text_surface, y in messages:
                text_rect = text_surface.get_rect(
                    center=(self.width // 2, y)
                )
                screen.blit(text_surface, text_rect)
