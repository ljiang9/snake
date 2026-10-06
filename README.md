# snake 贪吃蛇

终端贪吃蛇小游戏：吃食物变长，撞墙或撞到自己结束。

## 玩法

- `python -m snake` → 交互模式（有 curses 用方向键/WASD，无 curses 回退行输入）
- `python -m snake --auto` → 贪心 AI 无头演示 200 步
- `python -m snake --auto --steps 500 --seed 7 --verbose` → 更多步数并打印终盘
- `--width/--height` 调棋盘大小，`--seed` 固定随机

贪心 AI：每步选曼哈顿距离最接近食物、且不立刻撞死（撞墙/撞身）的方向；
不考虑长远死路，所以只是演示，不是高分选手。

## 已知局限

- AI 是简单贪心，经常把自己困死；典型 200 步得分个位数到十几分
- 交互需要终端（tty）；curses 在 Windows 默认不可用
- 无最高分存档、无难度分级
