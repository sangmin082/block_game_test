import pygame
import sys
import math
import random

pygame.init()

# --- 상수 ---
WIDTH, HEIGHT = 800, 600
FPS = 60

# 색상
BLACK       = (0, 0, 0)
WHITE       = (255, 255, 255)
CYAN        = (0, 220, 255)
ORANGE      = (255, 140, 0)
YELLOW      = (255, 220, 0)
GREEN       = (60, 220, 60)
RED         = (220, 50, 50)
PURPLE      = (180, 80, 220)
GRAY        = (80, 80, 80)
DARK        = (15, 15, 30)
PADDLE_COL  = (60, 180, 255)
BALL_COL    = (255, 255, 255)

BLOCK_COLORS = [RED, ORANGE, YELLOW, GREEN, CYAN, PURPLE]

# 블록 설정
COLS        = 10
ROWS        = 6
BLOCK_W     = 70
BLOCK_H     = 28
BLOCK_PAD   = 5
OFFSET_X    = (WIDTH - (COLS * (BLOCK_W + BLOCK_PAD) - BLOCK_PAD)) // 2
OFFSET_Y    = 60

# 패들
PADDLE_W    = 110
PADDLE_H    = 14
PADDLE_Y    = HEIGHT - 50
PADDLE_SPD  = 7

# 공
BALL_R      = 9
BALL_SPD    = 5.5


class Block:
    def __init__(self, col, row, hp=1):
        self.col = col
        self.row = row
        self.hp = hp
        self.max_hp = hp
        self.rect = pygame.Rect(
            OFFSET_X + col * (BLOCK_W + BLOCK_PAD),
            OFFSET_Y + row * (BLOCK_H + BLOCK_PAD),
            BLOCK_W, BLOCK_H
        )
        self.color = BLOCK_COLORS[row % len(BLOCK_COLORS)]
        self.alive = True

    def hit(self):
        self.hp -= 1
        if self.hp <= 0:
            self.alive = False

    def draw(self, surf):
        if not self.alive:
            return
        alpha = int(80 + 175 * (self.hp / self.max_hp))
        col = tuple(min(255, int(c * (0.5 + 0.5 * self.hp / self.max_hp))) for c in self.color)
        pygame.draw.rect(surf, col, self.rect, border_radius=5)
        pygame.draw.rect(surf, WHITE, self.rect, 1, border_radius=5)
        if self.max_hp > 1:
            font = pygame.font.SysFont("Arial", 14, bold=True)
            txt = font.render(str(self.hp), True, WHITE)
            surf.blit(txt, txt.get_rect(center=self.rect.center))


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.randint(20, 40)
        self.max_life = self.life
        self.r = random.randint(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1
        self.life -= 1

    def draw(self, surf):
        alpha = int(255 * self.life / self.max_life)
        col = tuple(min(255, c) for c in self.color)
        pygame.draw.circle(surf, col, (int(self.x), int(self.y)), self.r)


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("BLOCK BREAKER")
        self.clock = pygame.time.Clock()
        self.font_big   = pygame.font.SysFont("Arial", 52, bold=True)
        self.font_med   = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 20)
        self.reset()

    def reset(self):
        self.paddle_x = WIDTH // 2 - PADDLE_W // 2
        self.ball_x   = float(WIDTH // 2)
        self.ball_y   = float(PADDLE_Y - BALL_R - 2)
        self.ball_vx  = BALL_SPD * random.choice([-1, 1])
        self.ball_vy  = -BALL_SPD
        self.score    = 0
        self.lives    = 3
        self.level    = 1
        self.blocks   = self._make_blocks()
        self.particles= []
        self.state    = "playing"   # playing / dead / win / over
        self.launch   = False       # 공이 패들에 붙어 있는지
        self.combo    = 0
        self.combo_timer = 0

    def _make_blocks(self):
        blocks = []
        for row in range(ROWS):
            for col in range(COLS):
                hp = 1
                if self.level >= 2 and row < 2:
                    hp = 2
                if self.level >= 3 and row == 0:
                    hp = 3
                blocks.append(Block(col, row, hp))
        return blocks

    def _next_level(self):
        self.level += 1
        self.blocks = self._make_blocks()
        self.ball_x = float(self.paddle_x + PADDLE_W // 2)
        self.ball_y = float(PADDLE_Y - BALL_R - 2)
        spd = BALL_SPD + (self.level - 1) * 0.4
        self.ball_vx = spd * random.choice([-1, 1])
        self.ball_vy = -spd
        self.state = "playing"

    def handle_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.paddle_x = max(0, self.paddle_x - PADDLE_SPD)
        if keys[pygame.K_RIGHT]:
            self.paddle_x = min(WIDTH - PADDLE_W, self.paddle_x + PADDLE_SPD)

        # 마우스 패들
        mx, _ = pygame.mouse.get_pos()
        self.paddle_x = max(0, min(WIDTH - PADDLE_W, mx - PADDLE_W // 2))

    def update(self):
        if self.state != "playing":
            return

        # 파티클
        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles:
            p.update()

        # 콤보 타이머
        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            self.combo = 0

        # 공 이동
        self.ball_x += self.ball_vx
        self.ball_y += self.ball_vy

        # 벽 반사
        if self.ball_x - BALL_R <= 0:
            self.ball_x = BALL_R
            self.ball_vx = abs(self.ball_vx)
        if self.ball_x + BALL_R >= WIDTH:
            self.ball_x = WIDTH - BALL_R
            self.ball_vx = -abs(self.ball_vx)
        if self.ball_y - BALL_R <= 0:
            self.ball_y = BALL_R
            self.ball_vy = abs(self.ball_vy)

        # 패들 충돌
        paddle_rect = pygame.Rect(self.paddle_x, PADDLE_Y, PADDLE_W, PADDLE_H)
        ball_rect   = pygame.Rect(self.ball_x - BALL_R, self.ball_y - BALL_R, BALL_R*2, BALL_R*2)
        if ball_rect.colliderect(paddle_rect) and self.ball_vy > 0:
            self.ball_vy = -abs(self.ball_vy)
            # 패들 어디에 맞았는지에 따라 각도 조절
            hit_pos = (self.ball_x - self.paddle_x) / PADDLE_W  # 0~1
            angle = math.radians(30 + 120 * hit_pos)  # 30~150도
            spd = math.hypot(self.ball_vx, self.ball_vy)
            self.ball_vx = spd * math.cos(math.pi - angle)
            self.ball_vy = -abs(spd * math.sin(math.pi - angle))
            self.combo = 0

        # 블록 충돌
        for block in self.blocks:
            if not block.alive:
                continue
            if ball_rect.colliderect(block.rect):
                block.hit()
                self.combo += 1
                self.combo_timer = 90
                pts = 10 * self.combo * self.level
                self.score += pts

                # 파티클
                for _ in range(12):
                    self.particles.append(Particle(block.rect.centerx, block.rect.centery, block.color))

                # 반사 방향 결정
                overlap_x = min(abs(self.ball_x - block.rect.left), abs(self.ball_x - block.rect.right))
                overlap_y = min(abs(self.ball_y - block.rect.top), abs(self.ball_y - block.rect.bottom))
                if overlap_x < overlap_y:
                    self.ball_vx *= -1
                else:
                    self.ball_vy *= -1
                break

        # 공이 바닥 아래로
        if self.ball_y - BALL_R > HEIGHT:
            self.lives -= 1
            if self.lives <= 0:
                self.state = "over"
            else:
                self.state = "dead"
                self.ball_x = float(self.paddle_x + PADDLE_W // 2)
                self.ball_y = float(PADDLE_Y - BALL_R - 2)
                spd = BALL_SPD + (self.level - 1) * 0.4
                self.ball_vx = spd * random.choice([-1, 1])
                self.ball_vy = -spd

        # 모든 블록 제거 → 다음 레벨
        if all(not b.alive for b in self.blocks):
            if self.level >= 3:
                self.state = "win"
            else:
                self._next_level()

    def draw(self):
        self.screen.fill(DARK)

        # 배경 격자
        for x in range(0, WIDTH, 40):
            pygame.draw.line(self.screen, (25, 25, 45), (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, 40):
            pygame.draw.line(self.screen, (25, 25, 45), (0, y), (WIDTH, y))

        # 블록
        for block in self.blocks:
            block.draw(self.screen)

        # 파티클
        for p in self.particles:
            p.draw(self.screen)

        # 패들
        paddle_rect = pygame.Rect(self.paddle_x, PADDLE_Y, PADDLE_W, PADDLE_H)
        pygame.draw.rect(self.screen, PADDLE_COL, paddle_rect, border_radius=7)
        pygame.draw.rect(self.screen, WHITE, paddle_rect, 1, border_radius=7)

        # 공
        pygame.draw.circle(self.screen, BALL_COL, (int(self.ball_x), int(self.ball_y)), BALL_R)
        pygame.draw.circle(self.screen, CYAN, (int(self.ball_x), int(self.ball_y)), BALL_R, 2)

        # HUD
        score_txt = self.font_med.render(f"SCORE  {self.score}", True, WHITE)
        self.screen.blit(score_txt, (10, 10))

        lives_txt = self.font_med.render(f"LIVES  {'♥ ' * self.lives}", True, RED)
        self.screen.blit(lives_txt, (WIDTH // 2 - lives_txt.get_width() // 2, 10))

        level_txt = self.font_med.render(f"LV {self.level}", True, YELLOW)
        self.screen.blit(level_txt, (WIDTH - level_txt.get_width() - 10, 10))

        # 콤보
        if self.combo >= 2 and self.combo_timer > 0:
            combo_txt = self.font_med.render(f"COMBO x{self.combo}!", True, ORANGE)
            alpha = min(255, self.combo_timer * 6)
            combo_txt.set_alpha(alpha)
            self.screen.blit(combo_txt, combo_txt.get_rect(center=(WIDTH // 2, HEIGHT - 20)))

        # 오버레이
        if self.state == "dead":
            self._overlay("BALL LOST!", "Click or SPACE to continue", ORANGE)
        elif self.state == "over":
            self._overlay("GAME OVER", f"Score: {self.score}   Press R to restart", RED)
        elif self.state == "win":
            self._overlay("YOU WIN! 🎉", f"Score: {self.score}   Press R to restart", YELLOW)

        pygame.display.flip()

    def _overlay(self, title, sub, color):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        t = self.font_big.render(title, True, color)
        self.screen.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))

        s = self.font_small.render(sub, True, WHITE)
        self.screen.blit(s, s.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20)))

    def run(self):
        pygame.mouse.set_visible(False)
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
                    if event.key == pygame.K_r:
                        self.reset()
                    if event.key == pygame.K_SPACE and self.state == "dead":
                        self.state = "playing"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == "dead":
                        self.state = "playing"

            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)


if __name__ == "__main__":
    Game().run()
