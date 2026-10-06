#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
snake -- 终端贪吃蛇小游戏。

核心玩法:
- 蛇在棋盘上移动，吃食物变长；撞墙或撞到自己则结束。
- 交互模式用 curses（WASD/方向键），无 curses 时回退到行输入模式。
- --auto 用贪心 AI 头less 演示（朝食物走，避开即时碰撞）。

只依赖标准库。
"""

import argparse
import random
import sys

W, H = 20, 12

DIRS = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}
OPPOSITE = {"up": "down", "down": "up", "left": "right", "right": "left"}
KEYMAP = {
    "w": "up", "s": "down", "a": "left", "d": "right",
    "W": "up", "S": "down", "A": "left", "D": "right",
}


class Snake:
    """贪吃蛇游戏核心：与渲染解耦，可单独测试。"""

    def __init__(self, width=W, height=H, seed=None):
        self.width = width
        self.height = height
        self.rng = random.Random(seed)
        cx, cy = width // 2, height // 2
        self.body = [(cx - 2, cy), (cx - 1, cy), (cx, cy)]  # 头在最后
        self.direction = "right"
        self.score = 0
        self.alive = True
        self.food = None
        self._place_food()

    @property
    def head(self):
        return self.body[-1]

    def _place_food(self):
        free = [(x, y) for y in range(self.height) for x in range(self.width)
                if (x, y) not in self.body]
        self.food = self.rng.choice(free) if free else None

    def set_direction(self, d):
        if d in DIRS and d != OPPOSITE[self.direction]:
            self.direction = d

    def step(self):
        """前进一步。返回事件: 'move' | 'eat' | 'die'。"""
        if not self.alive:
            return "die"
        dx, dy = DIRS[self.direction]
        hx, hy = self.head
        nx, ny = hx + dx, hy + dy
        # 撞墙
        if not (0 <= nx < self.width and 0 <= ny < self.height):
            self.alive = False
            return "die"
        eating = (nx, ny) == self.food
        # 撞自己（吃食物时长尾不缩，否则尾格会空出来）
        tail = self.body[0]
        if (nx, ny) in self.body and not (not eating and (nx, ny) == tail):
            self.alive = False
            return "die"
        self.body.append((nx, ny))
        if eating:
            self.score += 1
            self._place_food()
            return "eat"
        self.body.pop(0)
        return "move"


def render_text(game):
    """纯文本棋盘渲染（headless 演示 / 回退模式用）。"""
    grid = [["·"] * game.width for _ in range(game.height)]
    if game.food:
        fx, fy = game.food
        grid[fy][fx] = "●"
    for i, (x, y) in enumerate(game.body):
        grid[y][x] = "○" if i < len(game.body) - 1 else "◎"
    lines = ["+" + "-" * (game.width * 2) + "+"]
    for row in grid:
        lines.append("|" + " ".join(row) + "|")
    lines.append("+" + "-" * (game.width * 2) + "+")
    return "\n".join(lines)


def greedy_direction(game):
    """贪心 AI：选让曼哈顿距离最接近食物、且不立刻撞死的方向。"""
    if game.food is None:
        return game.direction
    fx, fy = game.food
    hx, hy = game.head
    best, best_key = game.direction, None
    for name in DIRS:
        if name == OPPOSITE[game.direction]:
            continue
        dx, dy = DIRS[name]
        nx, ny = hx + dx, hy + dy
        if not (0 <= nx < game.width and 0 <= ny < game.height):
            continue
        eating = (nx, ny) == game.food
        tail = game.body[0]
        if (nx, ny) in game.body and not (not eating and (nx, ny) == tail):
            continue
        key = abs(nx - fx) + abs(ny - fy)
        if best_key is None or key < best_key:
            best, best_key = name, key
    return best


def auto_play(steps=200, width=W, height=H, seed=None, verbose=False):
    """无头自动演示。返回 (score, steps_done)。"""
    game = Snake(width, height, seed)
    done = 0
    for _ in range(steps):
        if not game.alive:
            break
        game.set_direction(greedy_direction(game))
        game.step()
        done += 1
    if verbose:
        print(render_text(game))
        print(f"得分: {game.score}  步数: {done}  存活: {'是' if game.alive else '否'}")
    return game.score, done


def play_line_mode(game):
    """无 curses 回退：每步输入 WASD。"""
    print("无 curses，用 WASD + 回车走一步，q 退出。")
    while game.alive:
        print(render_text(game))
        print(f"得分: {game.score}  (方向: {game.direction})")
        try:
            cmd = input("走 [wasd/q]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if cmd.lower() == "q":
            break
        if cmd and cmd[0] in KEYMAP:
            game.set_direction(KEYMAP[cmd[0]])
        ev = game.step()
        if ev == "die":
            print(render_text(game))
            print(f"游戏结束！最终得分: {game.score}")
            return
    print(f"最终得分: {game.score}")


def play_curses(game):
    import curses

    def loop(stdscr):
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.timeout(140)
        keymap = {curses.KEY_UP: "up", curses.KEY_DOWN: "down",
                  curses.KEY_LEFT: "left", curses.KEY_RIGHT: "right"}
        while game.alive:
            stdscr.clear()
            stdscr.addstr(0, 0, f"得分: {game.score}  (WASD/方向键, q 退出)")
            grid = render_text(game).splitlines()
            for i, line in enumerate(grid):
                try:
                    stdscr.addstr(i + 1, 0, line)
                except curses.error:
                    pass
            stdscr.refresh()
            try:
                ch = stdscr.getch()
            except Exception:
                ch = -1
            if ch == ord("q") or ch == ord("Q"):
                break
            if ch in keymap:
                game.set_direction(keymap[ch])
            elif 0 <= ch < 256 and chr(ch) in KEYMAP:
                game.set_direction(KEYMAP[chr(ch)])
            game.step()
        stdscr.nodelay(False)
        stdscr.addstr(game.height + 3, 0, f"游戏结束！最终得分: {game.score}，按任意键退出")
        stdscr.refresh()
        stdscr.getch()

    curses.wrapper(loop)


def main(argv=None):
    ap = argparse.ArgumentParser(description="终端贪吃蛇（snake）")
    ap.add_argument("--auto", action="store_true", help="无头自动演示（贪心 AI）")
    ap.add_argument("--steps", type=int, default=200, help="自动演示步数（默认 200）")
    ap.add_argument("--width", type=int, default=W)
    ap.add_argument("--height", type=int, default=H)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--verbose", action="store_true", help="自动演示后打印棋盘")
    args = ap.parse_args(argv)

    if args.auto:
        score, done = auto_play(args.steps, args.width, args.height, args.seed, args.verbose)
        print(f"自动演示结束：得分 {score}，步数 {done}")
        return 0

    if not sys.stdin.isatty():
        print("交互模式需要终端；可用 --auto 做无头演示。", file=sys.stderr)
        return 2
    game = Snake(args.width, args.height, args.seed)
    try:
        import curses  # noqa: F401
        play_curses(game)
    except Exception:
        play_line_mode(game)
    return 0


if __name__ == "__main__":
    sys.exit(main())
