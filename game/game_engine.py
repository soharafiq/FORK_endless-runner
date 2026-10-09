
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

        self.title_font = pygame.font.SysFont("Arial", 48, bold=True)
        self.font = pygame.font.SysFont("Arial", 30)
        self.menu_font = pygame.font.SysFont("Arial", 25)

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
        self._game_over_logged = False

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if not self.game_over:
            if event.key in (
                pygame.K_SPACE,
                pygame.K_UP,
                pygame.K_w,
            ):
                self.player.jump()
            return

        # Choose a difficulty to restart the game.
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

        # Increase speed without exceeding the selected limit.
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

        # Check collisions.
        player_rect = self.player.rect()

        for obstacle in self.obstacles:
            obstacle_rect = obstacle.rect()
            previous_x = obstacle.previous_x

            # Normal collision detection.
            if obstacle_rect.colliderect(player_rect):
                self.game_over = True
                return

            # Check the full horizontal path travelled this frame.
            if obstacle.x < previous_x:
                swept_rect = pygame.Rect(
                    obstacle.x,
                    obstacle.y,
                    previous_x + obstacle.width - obstacle.x,
                    obstacle.height,
                )

                if swept_rect.colliderect(player_rect):
                    self.game_over = True
                    return

        # Award points when obstacles pass the player.
        for obstacle in self.obstacles:
            if (
                not obstacle.scored
                and obstacle.x + obstacle.width < self.player.x
            ):
                obstacle.scored = True
                self.score += 1

        # Remove obstacles that leave the screen.
        self.obstacles = [
            obstacle
            for obstacle in self.obstacles
            if not obstacle.off_screen()
        ]

        self.distance += self.speed

    def render(self, screen):
        # Sky-blue background so the player is visible.
        screen.fill(SKY_BLUE)

        # Draw the ground.
        pygame.draw.line(
            screen,
            BROWN,
            (0, self.ground_y),
            (self.width, self.ground_y),
            4,
        )

        # Draw the blue player and green obstacles.
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

        # Display score and selected difficulty.
        score_text = self.font.render(
            f"Score: {self.score}",
            True,
            BLACK,
        )

        difficulty_text = self.menu_font.render(
            f"Difficulty: {self.difficulty}",
            True,
            BLACK,
        )

        screen.blit(score_text, (10, 10))
        screen.blit(difficulty_text, (10, 45))

        # Display Game Over screen and replay options.
        if self.game_over:
            overlay = pygame.Surface(
                (self.width, self.height),
                pygame.SRCALPHA,
            )
            overlay.fill((0, 0, 0, 190))
            screen.blit(overlay, (0, 0))

            title = self.title_font.render(
                "GAME OVER",
                True,
                RED,
            )

            final_score = self.font.render(
                f"Final Score: {self.score}",
                True,
                WHITE,
            )

            prompt = self.menu_font.render(
                "Choose a difficulty to play again",
                True,
                WHITE,
            )

            easy = self.menu_font.render(
                "1 - Easy",
                True,
                WHITE,
            )

            medium = self.menu_font.render(
                "2 - Medium",
                True,
                WHITE,
            )

            hard = self.menu_font.render(
                "3 - Hard",
                True,
                WHITE,
            )

            exit_text = self.menu_font.render(
                "ESC / Q - Exit",
                True,
                WHITE,
            )

            messages = [
                (title, self.height // 2 - 125),
                (final_score, self.height // 2 - 70),
                (prompt, self.height // 2 - 20),
                (easy, self.height // 2 + 25),
                (medium, self.height // 2 + 60),
                (hard, self.height // 2 + 95),
                (exit_text, self.height // 2 + 140),
            ]

            for text_surface, y in messages:
                text_rect = text_surface.get_rect(
                    center=(self.width // 2, y)
                )
                screen.blit(text_surface, text_rect)
