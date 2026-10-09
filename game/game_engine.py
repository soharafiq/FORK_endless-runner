
import pygame
from .player import Player
from .obstacle import Obstacle

# Game Engine

WHITE = (255, 255, 255)
BROWN = (120, 80, 40)
DARK_GREEN = (30, 100, 30)


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.ground_y = height - 40

        self.player = Player(80, self.ground_y)

        self.speed = 6
        self.max_speed = 12
        self.speed_increase_per_frame = 0.003

        self.spawn_interval = 70
        self._spawn_timer = 0
        self.obstacles = []

        self.distance = 0
        self.score = 0
        self.font = pygame.font.SysFont("Arial", 30)
        self.game_over = False

    def handle_event(self, event):
        if (
            event.type == pygame.KEYDOWN
            and event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w)
        ):
            self.player.jump()

    def handle_input(self):
        # Reserved for continuously-held-key input.
        pass

    def update(self):
        if self.game_over:
            return

        # Increase speed gradually, with a maximum limit.
        self.speed = min(
            self.speed + self.speed_increase_per_frame,
            self.max_speed
        )

        self.player.update()

        # Spawn obstacles at regular intervals.
        self._spawn_timer += 1
        if self._spawn_timer >= self.spawn_interval:
            self._spawn_timer = 0
            self.obstacles.append(
                Obstacle(self.width, self.ground_y, self.speed)
            )

        # Save previous positions before moving obstacles.
        for obstacle in self.obstacles:
            obstacle.previous_x = obstacle.x
            obstacle.move()
            obstacle.speed = self.speed

        # Detect collisions with the player.
        player_rect = self.player.rect()

        for obstacle in self.obstacles:
            obstacle_rect = obstacle.rect()
            previous_x = obstacle.previous_x

            # Check collision at the current position.
            if obstacle_rect.colliderect(player_rect):
                self.game_over = True
                return

            # Check the full horizontal path travelled this frame.
            if obstacle.x < previous_x:
                swept_left = obstacle.x
                swept_right = previous_x + obstacle.width

                swept_rect = pygame.Rect(
                    swept_left,
                    obstacle.y,
                    swept_right - swept_left,
                    obstacle.height
                )

                # Require both horizontal and vertical overlap.
                if swept_rect.colliderect(player_rect):
                    self.game_over = True
                    return

        # Increase score when obstacles pass the player.
        for obstacle in self.obstacles:
            if (
                not obstacle.scored
                and obstacle.x + obstacle.width < self.player.x
            ):
                obstacle.scored = True
                self.score += 1

        # Remove obstacles that have left the screen.
        self.obstacles = [
            obstacle for obstacle in self.obstacles
            if not obstacle.off_screen()
        ]

        self.distance += self.speed

    def render(self, screen):
        pygame.draw.line(
            screen,
            BROWN,
            (0, self.ground_y),
            (self.width, self.ground_y),
            4
        )

        pygame.draw.rect(screen, WHITE, self.player.rect())

        for obstacle in self.obstacles:
            pygame.draw.rect(screen, DARK_GREEN, obstacle.rect())

        score_text = self.font.render(
            f"Score: {self.score}", True, (0, 0, 0)
        )
        screen.blit(score_text, (10, 10))

        if self.game_over and not getattr(
            self, "_game_over_logged", False
        ):
            print("Game over! Final score:", self.score)
            self._game_over_logged = True
