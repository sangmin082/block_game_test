#!/usr/bin/env python3
"""
TUI Block Breaker — curses version
Controls: ← → arrow keys (or A/D), Q to quit, R to restart
"""

import curses
import math
import random
import time

# ── 상수 ──────────────────────────────────────────────────────────────────────
COLS       = 14          # 블록 열 수
ROWS       = 5           # 블록 행 수
BLOCK_W    = 5           # 블록 너비 (chars)
BLOCK_H    = 1           # 블록 높이 (lines)
BLOCK_PAD  = 1           # 블록 사이 간격

PADDLE_W   = 9
BALL_CHAR  = "●"

FPS        = 30
TICK       = 1.0 / FPS

BLOCK_CHARS = ["▓▓▓▓▓", "▒▒▒▒▒", "░░░░░"]  # hp 3, 2, 1

COLOR_BLOCK  = [1, 2, 3, 4, 5, 6]   # curses color pair ids
COLOR_PADDLE = 7
COLOR_BALL   = 8
COLOR_HUD    = 9
COLOR_COMBO  = 10
COLOR_OVER   = 11


def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1,  curses.COLOR_RED,     -1)
    curses.init_pair(2,  curses.COLOR_YELLOW,  -1)
    curses.init_pair(3,  curses.COLOR_GREEN,   -1)
    curses.init_pair(4,  curses.COLOR_CYAN,    -1)
    curses.init_pair(5,  curses.COLOR_BLUE,    -1)
    curses.init_pair(6,  curses.COLOR_MAGENTA, -1)
    curses.init_pair(7,  curses.COLOR_CYAN,    -1)   # paddle
    curses.init_pair(8,  curses.COLOR_WHITE,   -1)   # ball
    curses.init_pair(9,  curses.COLOR_WHITE,   -1)   # hud
    curses.init_pair(10, curses.COLOR_YELLOW,  -1)   # combo
    curses.init_pair(11, curses.COLOR_RED,     -1)   # game over


# ── Block ─────────────────────────────────────────────────────────────────────
class Block:
    def __init__(self, col, row, hp=1):
        self.col = col
        self.row = row
        self.hp  = hp
        self.max_hp = hp
        self.alive = True
        self.color_id = COLOR_BLOCK[row % len(COLOR_BLOCK)]

    def hit(self):
        self.hp -= 1
        if self.hp <= 0:
            self.alive = False

    def char(self):
        idx = max(0, min(len(BLOCK_CHARS)-1, self.max_hp - self.hp))
        return BLOCK_CHARS[idx][:BLOCK_W]


# ── Game ──────────────────────────────────────────────────────────────────────
class Game:
    def __init__(self, stdscr):
        self.scr = stdscr
        self.h, self.w = stdscr.getmaxyx()
        self.reset()

    # ── 레이아웃 계산 ─────────────────────────────────────────────────────────
    @property
    def field_w(self):
        return COLS * (BLOCK_W + BLOCK_PAD) - BLOCK_PAD

    @property
    def offset_x(self):
        return max(0, (self.w - self.field_w) // 2)

    @property
    def offset_y(self):
        return 3   # HUD 아래

    @property
    def paddle_y(self):
        return self.h - 3

    @property
    def max_ball_y(self):
        return self.h - 2

    # ── 초기화 ────────────────────────────────────────────────────────────────
    def reset(self):
        self.score   = 0
        self.lives   = 3
        self.level   = 1
        self.combo   = 0
        self.combo_t = 0
        self.state   = "playing"   # playing / dead / win / over
        self._setup_level()

    def _setup_level(self):
        self.blocks = []
        for row in range(ROWS):
            for col in range(COLS):
                hp = 1
                if self.level >= 2 and row == 0:
                    hp = 2
                if self.level >= 3 and row == 0:
                    hp = 3
                self.blocks.append(Block(col, row, hp))

        self.paddle_x = float(self.offset_x + self.field_w // 2 - PADDLE_W // 2)
        spd = 0.4 + self.level * 0.15
        self.ball_x  = self.paddle_x + PADDLE_W / 2
        self.ball_y  = float(self.paddle_y - 1)
        angle = math.radians(random.randint(210, 330))
        self.ball_vx = spd * math.cos(angle)
        self.ball_vy = -abs(spd * math.sin(angle)) * 1.5  # y축 더 빠르게

    # ── 블록 좌표 ─────────────────────────────────────────────────────────────
    def block_x(self, b):
        return self.offset_x + b.col * (BLOCK_W + BLOCK_PAD)

    def block_y(self, b):
        return self.offset_y + b.row * (BLOCK_H + 1)

    # ── 입력 ──────────────────────────────────────────────────────────────────
    def handle_input(self, key):
        if key in (curses.KEY_LEFT, ord('a'), ord('A')):
            self.paddle_x = max(float(self.offset_x), self.paddle_x - 2)
        if key in (curses.KEY_RIGHT, ord('d'), ord('D')):
            self.paddle_x = min(float(self.offset_x + self.field_w - PADDLE_W), self.paddle_x + 2)
        if key in (ord('r'), ord('R')):
            self.reset()
        if self.state == "dead" and key in (ord(' '), ord('\n')):
            self.state = "playing"

    # ── 업데이트 ──────────────────────────────────────────────────────────────
    def update(self):
        if self.state != "playing":
            return

        if self.combo_t > 0:
            self.combo_t -= 1
        else:
            self.combo = 0

        self.ball_x += self.ball_vx
        self.ball_y += self.ball_vy

        # 좌우 벽
        left  = float(self.offset_x)
        right = float(self.offset_x + self.field_w - 1)
        if self.ball_x <= left:
            self.ball_x = left; self.ball_vx = abs(self.ball_vx)
        if self.ball_x >= right:
            self.ball_x = right; self.ball_vx = -abs(self.ball_vx)

        # 천장
        if self.ball_y <= float(self.offset_y - 1):
            self.ball_y = float(self.offset_y - 1); self.ball_vy = abs(self.ball_vy)

        # 패들 충돌
        bx, by = int(round(self.ball_x)), int(round(self.ball_y))
        px = int(round(self.paddle_x))
        if by == self.paddle_y and px <= bx < px + PADDLE_W and self.ball_vy > 0:
            # 각도 조절
            rel = (self.ball_x - self.paddle_x) / PADDLE_W  # 0~1
            angle = math.radians(150 - rel * 120)
            spd = math.hypot(self.ball_vx, self.ball_vy)
            self.ball_vx =  spd * math.cos(angle)
            self.ball_vy = -abs(spd * math.sin(angle))
            self.combo = 0

        # 블록 충돌
        for block in self.blocks:
            if not block.alive:
                continue
            bkx = self.block_x(block)
            bky = self.block_y(block)
            if bkx <= bx < bkx + BLOCK_W and bky <= by <= bky + BLOCK_H:
                block.hit()
                self.combo += 1
                self.combo_t = FPS * 2
                self.score += 10 * self.combo * self.level

                # 반사
                if abs(self.ball_x - (bkx + BLOCK_W/2)) > abs(self.ball_y - (bky + 0.5)):
                    self.ball_vx *= -1
                else:
                    self.ball_vy *= -1
                break

        # 공 낙사
        if self.ball_y >= float(self.max_ball_y):
            self.lives -= 1
            if self.lives <= 0:
                self.state = "over"
            else:
                self.state = "dead"
                self.ball_x = self.paddle_x + PADDLE_W / 2
                self.ball_y = float(self.paddle_y - 1)
                spd = 0.4 + self.level * 0.15
                self.ball_vx = spd * random.choice([-1, 1])
                self.ball_vy = -abs(spd) * 1.5

        # 클리어
        if all(not b.alive for b in self.blocks):
            if self.level >= 3:
                self.state = "win"
            else:
                self.level += 1
                self._setup_level()

    # ── 그리기 ────────────────────────────────────────────────────────────────
    def draw(self):
        self.scr.erase()
        H, W = self.h, self.w

        # HUD
        hud = f" SCORE: {self.score:>6}   LIVES: {'♥ ' * self.lives}  LV:{self.level} "
        try:
            self.scr.addstr(1, max(0, W//2 - len(hud)//2), hud,
                            curses.color_pair(COLOR_HUD) | curses.A_BOLD)
        except curses.error:
            pass

        # 경계선
        border = "─" * min(self.field_w + 2, W - 2)
        try:
            self.scr.addstr(2, self.offset_x - 1, "┌" + border + "┐")
            self.scr.addstr(self.h - 2, self.offset_x - 1, "└" + border + "┘")
            for y in range(3, self.h - 2):
                self.scr.addstr(y, self.offset_x - 1, "│")
                self.scr.addstr(y, self.offset_x + self.field_w, "│")
        except curses.error:
            pass

        # 블록
        for block in self.blocks:
            if not block.alive:
                continue
            bx = self.block_x(block)
            by = self.block_y(block)
            if 0 <= by < H and 0 <= bx < W:
                txt = block.char()
                try:
                    self.scr.addstr(by, bx, txt,
                                    curses.color_pair(block.color_id) | curses.A_BOLD)
                except curses.error:
                    pass

        # 패들
        px = int(round(self.paddle_x))
        try:
            self.scr.addstr(self.paddle_y, px, "╠" + "═" * (PADDLE_W - 2) + "╣",
                            curses.color_pair(COLOR_PADDLE) | curses.A_BOLD)
        except curses.error:
            pass

        # 공
        bx, by = int(round(self.ball_x)), int(round(self.ball_y))
        if 0 <= by < H and 0 <= bx < W - 1:
            try:
                self.scr.addstr(by, bx, BALL_CHAR,
                                curses.color_pair(COLOR_BALL) | curses.A_BOLD)
            except curses.error:
                pass

        # 콤보
        if self.combo >= 2 and self.combo_t > 0:
            msg = f" COMBO x{self.combo}! "
            try:
                self.scr.addstr(self.paddle_y + 1,
                                max(0, W//2 - len(msg)//2), msg,
                                curses.color_pair(COLOR_COMBO) | curses.A_BOLD)
            except curses.error:
                pass

        # 오버레이
        if self.state == "dead":
            self._overlay("BALL LOST!", "SPACE to continue  R to restart")
        elif self.state == "over":
            self._overlay(f"GAME OVER  Score:{self.score}", "R to restart")
        elif self.state == "win":
            self._overlay(f"YOU WIN! 🎉  Score:{self.score}", "R to restart")

        self.scr.refresh()

    def _overlay(self, title, sub):
        H, W = self.h, self.w
        try:
            t = f"  {title}  "
            self.scr.addstr(H//2 - 1, max(0, W//2 - len(t)//2), t,
                            curses.color_pair(COLOR_OVER) | curses.A_REVERSE | curses.A_BOLD)
            s = f"  {sub}  "
            self.scr.addstr(H//2 + 1, max(0, W//2 - len(s)//2), s,
                            curses.color_pair(COLOR_HUD))
        except curses.error:
            pass

    # ── 메인 루프 ─────────────────────────────────────────────────────────────
    def run(self):
        self.scr.nodelay(True)
        self.scr.keypad(True)
        curses.curs_set(0)

        last = time.time()
        while True:
            key = self.scr.getch()
            if key in (ord('q'), ord('Q')):
                break
            self.handle_input(key)

            now = time.time()
            if now - last >= TICK:
                self.update()
                self.draw()
                last = now
            else:
                time.sleep(0.01)


# ── 진입점 ────────────────────────────────────────────────────────────────────
def main(stdscr):
    init_colors()
    g = Game(stdscr)
    g.run()


if __name__ == "__main__":
    curses.wrapper(main)
