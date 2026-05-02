import pygame
import math
from settings import *
from copy import deepcopy
from random import randrange


class Square:
    def __init__(self, pos, surface, is_apple=False):
        self.pos = pos
        self.surface = surface
        self.is_apple = is_apple
        self.is_tail = False
        self.dir = [-1, 0]  # [x, y] Direction

        if self.is_apple:
            self.dir = [0, 0]

    def draw(self, clr=SNAKE_CLR, size_factor=1.0, all_round=False):
        x, y = self.pos[0], self.pos[1]
        ss, gs = SQUARE_SIZE, GAP_SIZE

        if self.is_apple:
            eff = max(4, int((ss - 2 * gs) * size_factor))
            ox = x * ss + (ss - eff) // 2
            oy = y * ss + (ss - eff) // 2
            pygame.draw.rect(self.surface, clr, (ox, oy, eff, eff),
                             border_radius=max(1, eff // 3))
            # Shiny highlight
            hl_w = max(2, eff // 3)
            hl_h = max(1, eff // 4)
            pygame.draw.ellipse(self.surface, APPLE_HIGHLIGHT_CLR,
                                (ox + eff // 5, oy + eff // 6, hl_w, hl_h))
            return

        # Subtle shading colours for a tube/bevel texture effect
        light = tuple(min(255, c + 55) for c in clr)
        dark  = tuple(max(0,   c - 45) for c in clr)
        r = max(2, ss // 5)   # corner radius for body/taper segments

        # Head: fully rounded square, centered in cell
        if all_round:
            rect = pygame.Rect(x * ss + gs, y * ss + gs, ss - 2 * gs, ss - 2 * gs)
            pygame.draw.rect(self.surface, clr, rect,
                             border_radius=max(2, ss // 4))
            pygame.draw.line(self.surface, light,
                             (rect.left + 2, rect.top + 2),
                             (rect.right - 2, rect.top + 2), 1)
            pygame.draw.line(self.surface, dark,
                             (rect.left + 2, rect.bottom - 3),
                             (rect.right - 2, rect.bottom - 3), 1)
            return

        d = self.dir

        # Horizontal movement: taper only the HEIGHT (lateral axis).
        # Each segment keeps the full longitudinal extent so consecutive
        # tapered segments stay visually connected.
        if d in ([-1, 0], [1, 0]):
            eff = max(2, int((ss - 2 * gs) * size_factor))
            oy = y * ss + (ss - eff) // 2   # centred vertically
            if d == [-1, 0]:
                rect = pygame.Rect(x * ss + gs, oy, ss, eff)
                pygame.draw.rect(self.surface, clr, rect,
                                 border_top_left_radius=r,
                                 border_bottom_left_radius=r,
                                 border_top_right_radius=0,
                                 border_bottom_right_radius=0)
            else:
                rect = pygame.Rect(x * ss - gs, oy, ss, eff)
                pygame.draw.rect(self.surface, clr, rect,
                                 border_top_right_radius=r,
                                 border_bottom_right_radius=r,
                                 border_top_left_radius=0,
                                 border_bottom_left_radius=0)
            if eff > 4:
                pygame.draw.line(self.surface, light,
                                 (rect.left, rect.top + 1),
                                 (rect.right, rect.top + 1), 1)
                pygame.draw.line(self.surface, dark,
                                 (rect.left, rect.bottom - 2),
                                 (rect.right, rect.bottom - 2), 1)

        # Vertical movement: taper only the WIDTH (lateral axis).
        elif d in ([0, 1], [0, -1]):
            eff = max(2, int((ss - 2 * gs) * size_factor))
            ox = x * ss + (ss - eff) // 2   # centred horizontally
            if d == [0, 1]:
                rect = pygame.Rect(ox, y * ss - gs, eff, ss)
                pygame.draw.rect(self.surface, clr, rect,
                                 border_bottom_left_radius=r,
                                 border_bottom_right_radius=r,
                                 border_top_left_radius=0,
                                 border_top_right_radius=0)
            else:
                rect = pygame.Rect(ox, y * ss + gs, eff, ss)
                pygame.draw.rect(self.surface, clr, rect,
                                 border_top_left_radius=r,
                                 border_top_right_radius=r,
                                 border_bottom_left_radius=0,
                                 border_bottom_right_radius=0)
            if eff > 4:
                pygame.draw.line(self.surface, light,
                                 (rect.left + 1, rect.top),
                                 (rect.left + 1, rect.bottom), 1)
                pygame.draw.line(self.surface, dark,
                                 (rect.right - 2, rect.top),
                                 (rect.right - 2, rect.bottom), 1)

    def move(self, direction):
        self.dir = direction
        self.pos[0] += self.dir[0]
        self.pos[1] += self.dir[1]

    def hitting_wall(self):
        return (self.pos[0] <= -1 or self.pos[0] >= ROWS or
                self.pos[1] <= -1 or self.pos[1] >= ROWS)


# ---------------------------------------------------------------------------
# Bomb
# ---------------------------------------------------------------------------

class Bomb:
    """A timed bomb that explodes after 3 seconds in a radius-1 area."""

    def __init__(self, pos, surface):
        self.pos = list(pos)
        self.surface = surface
        self.timer = 3.0          # seconds until explosion
        self.exploded = False
        self.done = False         # ready to be removed from the list
        self._flash_timer = 0.35  # how long the explosion flash is visible

    def update(self, dt):
        """Advance state. Returns 'explode' on the frame it detonates."""
        if not self.exploded:
            self.timer -= dt
            if self.timer <= 0:
                self.exploded = True
                return 'explode'
        else:
            self._flash_timer -= dt
            if self._flash_timer <= 0:
                self.done = True
        return None

    def get_explosion_positions(self):
        bx, by = self.pos
        return {(bx + dx, by + dy) for dx in range(-1, 2) for dy in range(-1, 2)}

    def draw(self):
        if self.done:
            return
        x, y = self.pos
        ss = SQUARE_SIZE
        cx, cy = x * ss + ss // 2, y * ss + ss // 2

        if self.exploded:
            fade = max(0.0, self._flash_timer / 0.35)
            intensity = int(255 * fade)
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    ex, ey = x + dx, y + dy
                    if 0 <= ex < ROWS and 0 <= ey < ROWS:
                        col = (min(255, intensity + 80), min(80, intensity // 4), 0)
                        pygame.draw.rect(self.surface, col,
                                         (ex * ss + 3, ey * ss + 3, ss - 6, ss - 6))
        else:
            progress = max(0.0, self.timer / 3.0)  # 1 → 0 as countdown runs
            r = max(3, int(3 + 6 * (1 - progress)))
            if self.timer < 1.0:
                pulse = 0.6 + 0.4 * abs(math.sin(pygame.time.get_ticks() * 0.012))
                clr = (255, int(80 * pulse), 0)
            else:
                clr = BOMB_CLR
            pygame.draw.circle(self.surface, clr, (cx, cy), r)
            pygame.draw.circle(self.surface, (20, 10, 0), (cx, cy), max(1, r - 2))
            # Countdown arc around bomb
            arc_r = r + 4
            arc_rect = pygame.Rect(cx - arc_r, cy - arc_r, 2 * arc_r, 2 * arc_r)
            start_a = math.pi / 2
            end_a = math.pi / 2 + 2 * math.pi * (1 - progress)
            try:
                pygame.draw.arc(self.surface, (255, 220, 0), arc_rect,
                                start_a, end_a, 2)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Snake
# ---------------------------------------------------------------------------

class Snake:
    def __init__(self, surface):
        self.surface = surface
        self.is_dead = False
        self.squares_start_pos = [[ROWS // 2 + i, ROWS // 2] for i in range(INITIAL_SNAKE_LENGTH)]
        self.turns = {}
        self.dir = [-1, 0]
        self.score = 0
        self.moves_without_eating = 0
        self.apple = Square([randrange(ROWS), randrange(ROWS)], self.surface, is_apple=True)
        self.extra_apples = []   # apples spawned via keybinds
        self.bombs = []          # active bombs

        self.squares = []
        for pos in self.squares_start_pos:
            self.squares.append(Square(pos, self.surface))

        self.head = self.squares[0]
        self.squares[-1].is_tail = True

        self.path = []
        self.is_virtual_snake = False
        self.total_moves = 0
        self.won_game = False
        self.quit_game = False
        self.invincible_timer = 0.0   # seconds of invincibility remaining

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self):
        """Draw the snake, apples and bombs onto the surface."""
        ticks = pygame.time.get_ticks()

        # Primary apple — pulse in/out
        pulse = 1.0 + 0.18 * math.sin(ticks * 0.004)
        self.apple.draw(APPLE_CLR, size_factor=pulse)

        # Extra apples — each slightly offset in phase
        for i, ea in enumerate(self.extra_apples):
            ep = 1.0 + 0.18 * math.sin(ticks * 0.004 + i * 0.7)
            ea.draw(APPLE_CLR, size_factor=ep)

        # Bombs
        for bomb in self.bombs:
            bomb.draw()

        # While invincible, flash the body between normal and a gold tint
        if self.invincible_timer > 0:
            flash = math.sin(ticks * 0.03) > 0
            body_clr = (255, 220, 50) if flash else SNAKE_CLR
            head_clr = (255, 220, 50) if flash else HEAD_CLR
        else:
            body_clr = SNAKE_CLR
            head_clr = HEAD_CLR

        # Body squares drawn back-to-front so head overlaps body
        n = len(self.squares)
        for i in range(n - 1, 0, -1):
            sqr = self.squares[i]
            # last 5 squares taper: dist 0 = tip (thinnest), 4 = 5th from end
            dist = (n - 1) - i
            if dist < 5:
                sf = 0.15 + 0.85 * (dist / 5.0)
            else:
                sf = 1.0
            if self.is_virtual_snake:
                sqr.draw(VIRTUAL_SNAKE_CLR, size_factor=sf)
            else:
                sqr.draw(body_clr, size_factor=sf)

        # Head drawn last (on top)
        self._draw_head(ticks, head_clr)

    def _draw_head(self, ticks, head_clr=HEAD_CLR):
        head = self.head
        x, y = head.pos[0], head.pos[1]
        ss = SQUARE_SIZE
        d = head.dir

        # Head body — fully rounded
        head.draw(head_clr, all_round=True)
        if self.is_virtual_snake:
            return

        cx = x * ss + ss // 2
        cy = y * ss + ss // 2

        # ---- Tongue (waggling, intermittent) ----
        if math.sin(ticks * 0.008) > 0.2:
            tlen = ss // 2 + 4
            flen = 5
            fspread = 3
            waggle = int(2 * math.sin(ticks * 0.025))
            gs = GAP_SIZE
            if d == [-1, 0]:
                base = (cx - gs - 1, cy)
                tip = (cx - tlen, cy)
                pygame.draw.line(self.surface, TONGUE_CLR, base, tip, 1)
                pygame.draw.line(self.surface, TONGUE_CLR, tip,
                                 (tip[0] - flen, tip[1] - fspread + waggle), 1)
                pygame.draw.line(self.surface, TONGUE_CLR, tip,
                                 (tip[0] - flen, tip[1] + fspread + waggle), 1)
            elif d == [1, 0]:
                base = (cx + gs + 1, cy)
                tip = (cx + tlen, cy)
                pygame.draw.line(self.surface, TONGUE_CLR, base, tip, 1)
                pygame.draw.line(self.surface, TONGUE_CLR, tip,
                                 (tip[0] + flen, tip[1] - fspread + waggle), 1)
                pygame.draw.line(self.surface, TONGUE_CLR, tip,
                                 (tip[0] + flen, tip[1] + fspread + waggle), 1)
            elif d == [0, -1]:
                base = (cx, cy - gs - 1)
                tip = (cx, cy - tlen)
                pygame.draw.line(self.surface, TONGUE_CLR, base, tip, 1)
                pygame.draw.line(self.surface, TONGUE_CLR, tip,
                                 (tip[0] - fspread + waggle, tip[1] - flen), 1)
                pygame.draw.line(self.surface, TONGUE_CLR, tip,
                                 (tip[0] + fspread + waggle, tip[1] - flen), 1)
            elif d == [0, 1]:
                base = (cx, cy + gs + 1)
                tip = (cx, cy + tlen)
                pygame.draw.line(self.surface, TONGUE_CLR, base, tip, 1)
                pygame.draw.line(self.surface, TONGUE_CLR, tip,
                                 (tip[0] - fspread + waggle, tip[1] + flen), 1)
                pygame.draw.line(self.surface, TONGUE_CLR, tip,
                                 (tip[0] + fspread + waggle, tip[1] + flen), 1)

        # ---- Eyes ----
        eye_r = max(2, ss // 10)
        pupil_r = max(1, eye_r // 2)
        fo = ss // 4   # offset towards the front
        so = ss // 4   # lateral offset

        if d == [-1, 0]:
            e1, e2 = (cx - fo, cy - so), (cx - fo, cy + so)
            pd = (-1, 0)
        elif d == [1, 0]:
            e1, e2 = (cx + fo, cy - so), (cx + fo, cy + so)
            pd = (1, 0)
        elif d == [0, -1]:
            e1, e2 = (cx - so, cy - fo), (cx + so, cy - fo)
            pd = (0, -1)
        elif d == [0, 1]:
            e1, e2 = (cx - so, cy + fo), (cx + so, cy + fo)
            pd = (0, 1)
        else:
            return

        for ep in (e1, e2):
            pygame.draw.circle(self.surface, EYE_CLR, ep, eye_r)
            pygame.draw.circle(self.surface, PUPIL_CLR,
                               (ep[0] + pd[0], ep[1] + pd[1]), pupil_r)

    # ------------------------------------------------------------------
    # Direction / input
    # ------------------------------------------------------------------

    def set_direction(self, direction):
        if direction == 'left' and self.dir != [1, 0]:
            self.dir = [-1, 0]
            self.turns[self.head.pos[0], self.head.pos[1]] = self.dir
        elif direction == 'right' and self.dir != [-1, 0]:
            self.dir = [1, 0]
            self.turns[self.head.pos[0], self.head.pos[1]] = self.dir
        elif direction == 'up' and self.dir != [0, 1]:
            self.dir = [0, -1]
            self.turns[self.head.pos[0], self.head.pos[1]] = self.dir
        elif direction == 'down' and self.dir != [0, -1]:
            self.dir = [0, 1]
            self.turns[self.head.pos[0], self.head.pos[1]] = self.dir

    def handle_events(self):
        """Process pygame events. Sets quit_game flag instead of calling pygame.quit()."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game = True
                return

            # Directional control
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                self.set_direction('left')
            elif keys[pygame.K_RIGHT]:
                self.set_direction('right')
            elif keys[pygame.K_UP]:
                self.set_direction('up')
            elif keys[pygame.K_DOWN]:
                self.set_direction('down')

            # Experimental keybinds (on key-down only)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    self.spawn_extra_apples(1)
                elif event.key == pygame.K_v:
                    self.spawn_extra_apples(10)
                elif event.key == pygame.K_b:
                    self.spawn_extra_apples(200)
                elif event.key == pygame.K_n:
                    self.spawn_bomb()

    # ------------------------------------------------------------------
    # Experimental spawn helpers
    # ------------------------------------------------------------------

    def spawn_extra_apples(self, count):
        for _ in range(count):
            pos = self._random_free_pos()
            if pos:
                self.extra_apples.append(
                    Square(list(pos), self.surface, is_apple=True))

    def spawn_bomb(self):
        pos = self._random_free_pos()
        if pos:
            self.bombs.append(Bomb(list(pos), self.surface))

    def _random_free_pos(self):
        apple_pos = list(self.apple.pos)
        extra_positions = [list(a.pos) for a in self.extra_apples]
        bomb_positions = [list(b.pos) for b in self.bombs]
        for _ in range(ROWS * ROWS * 4):
            pos = [randrange(ROWS), randrange(ROWS)]
            if (self.is_position_free(pos)
                    and pos != apple_pos
                    and pos not in extra_positions
                    and pos not in bomb_positions):
                return pos
        return None

    def move(self):
        for j, sqr in enumerate(self.squares):
            p = (sqr.pos[0], sqr.pos[1])
            if p in self.turns:
                turn = self.turns[p]
                sqr.move([turn[0], turn[1]])
                if j == len(self.squares) - 1:
                    self.turns.pop(p)
            else:
                sqr.move(sqr.dir)
        self.moves_without_eating += 1

    def add_square(self):
        self.squares[-1].is_tail = False
        tail = self.squares[-1]  # Tail before adding new square

        direction = tail.dir
        if direction == [1, 0]:
            self.squares.append(Square([tail.pos[0] - 1, tail.pos[1]], self.surface))
        if direction == [-1, 0]:
            self.squares.append(Square([tail.pos[0] + 1, tail.pos[1]], self.surface))
        if direction == [0, 1]:
            self.squares.append(Square([tail.pos[0], tail.pos[1] - 1], self.surface))
        if direction == [0, -1]:
            self.squares.append(Square([tail.pos[0], tail.pos[1] + 1], self.surface))

        self.squares[-1].dir = direction
        self.squares[-1].is_tail = True  # Tail after adding new square

    def reset(self):
        self.__init__(self.surface)

    def hitting_self(self):
        for sqr in self.squares[1:]:
            if sqr.pos == self.head.pos:
                return True

    def generate_apple(self):
        pos = self._random_free_pos()
        if pos:
            self.apple = Square(pos, self.surface, is_apple=True)
        else:
            # Grid is full — just keep the current apple position
            pass

    def eating_apple(self):
        if self.head.pos == self.apple.pos and not self.is_virtual_snake and not self.won_game:
            self.generate_apple()
            self.moves_without_eating = 0
            self.score += 1
            return True

    def go_to(self, position):  # Set head direction to target position
        if self.head.pos[0] - 1 == position[0]:
            self.set_direction('left')
        if self.head.pos[0] + 1 == position[0]:
            self.set_direction('right')
        if self.head.pos[1] - 1 == position[1]:
            self.set_direction('up')
        if self.head.pos[1] + 1 == position[1]:
            self.set_direction('down')

    def is_position_free(self, position):
        if position[0] >= ROWS or position[0] < 0 or position[1] >= ROWS or position[1] < 0:
            return False
        for sqr in self.squares:
            if sqr.pos == position:
                return False
        return True

    # Breadth First Search Algorithm
    def bfs(self, s, e):  # Find shortest path between (start_position, end_position)
        q = [s]  # Queue
        visited = {tuple(pos): False for pos in GRID}

        visited[s] = True

        # Prev is used to find the parent node of each node to create a feasible path
        prev = {tuple(pos): None for pos in GRID}

        while q:  # While queue is not empty
            node = q.pop(0)
            neighbors = ADJACENCY_DICT[node]
            for next_node in neighbors:
                if self.is_position_free(next_node) and not visited[tuple(next_node)]:
                    q.append(tuple(next_node))
                    visited[tuple(next_node)] = True
                    prev[tuple(next_node)] = node

        path = list()
        p_node = e  # Starting from end node, we will find the parent node of each node

        start_node_found = False
        while not start_node_found:
            if prev[p_node] is None:
                return []
            p_node = prev[p_node]
            if p_node == s:
                path.append(e)
                return path
            path.insert(0, p_node)

        return []  # Path not available

    def create_virtual_snake(self):  # Creates a copy of snake (same size, same position, etc..)
        v_snake = Snake(self.surface)
        for i in range(len(self.squares) - len(v_snake.squares)):
            v_snake.add_square()

        for i, sqr in enumerate(v_snake.squares):
            sqr.pos = deepcopy(self.squares[i].pos)
            sqr.dir = deepcopy(self.squares[i].dir)

        v_snake.dir = deepcopy(self.dir)
        v_snake.turns = deepcopy(self.turns)
        v_snake.apple.pos = deepcopy(self.apple.pos)
        v_snake.apple.is_apple = True
        v_snake.is_virtual_snake = True
        v_snake.extra_apples = []
        v_snake.bombs = []

        return v_snake

    def get_path_to_tail(self):
        tail_pos = deepcopy(self.squares[-1].pos)
        self.squares.pop(-1)
        path = self.bfs(tuple(self.head.pos), tuple(tail_pos))
        self.add_square()
        return path

    def get_available_neighbors(self, pos):
        valid_neighbors = []
        neighbors = get_neighbors(tuple(pos))
        for n in neighbors:
            if self.is_position_free(n) and self.apple.pos != n:
                valid_neighbors.append(tuple(n))
        return valid_neighbors

    def longest_path_to_tail(self):
        neighbors = self.get_available_neighbors(self.head.pos)
        path = []
        if neighbors:
            dis = -9999
            for n in neighbors:
                if distance(n, self.squares[-1].pos) > dis:
                    v_snake = self.create_virtual_snake()
                    v_snake.go_to(n)
                    v_snake.move()
                    if v_snake.eating_apple():
                        v_snake.add_square()
                    if v_snake.get_path_to_tail():
                        path.append(n)
                        dis = distance(n, self.squares[-1].pos)
            if path:
                return [path[-1]]

    def any_safe_move(self):
        neighbors = self.get_available_neighbors(self.head.pos)
        path = []
        if neighbors:
            path.append(neighbors[randrange(len(neighbors))])
            v_snake = self.create_virtual_snake()
            for move in path:
                v_snake.go_to(move)
                v_snake.move()
            if v_snake.get_path_to_tail():
                return path
            else:
                return self.get_path_to_tail()

    def set_path(self):
        # If there is only 1 apple left for snake to win and it's adjacent to head
        if self.score == SNAKE_MAX_LENGTH - 1 and self.apple.pos in get_neighbors(self.head.pos):
            winning_path = [tuple(self.apple.pos)]
            print('Snake is about to win..')
            return winning_path

        v_snake = self.create_virtual_snake()

        # Let the virtual snake check if path to apple is available
        path_1 = v_snake.bfs(tuple(v_snake.head.pos), tuple(v_snake.apple.pos))

        # This will be the path to virtual snake tail after it follows path_1
        path_2 = []

        if path_1:
            for pos in path_1:
                v_snake.go_to(pos)
                v_snake.move()

            v_snake.add_square()  # Because it will eat an apple
            path_2 = v_snake.get_path_to_tail()

        # v_snake.draw()

        if path_2:  # If there is a path between v_snake and it's tail
            return path_1  # Choose BFS path to apple (Fastest and shortest path)

        # If path_1 or path_2 not available, test these 3 conditions:
            # 1- Make sure that the longest path to tail is available
            # 2- If score is even, choose longest_path_to_tail() to follow the tail, if odd use any_safe_move()
            # 3- Change the follow tail method if the snake gets stuck in a loop
        if self.longest_path_to_tail() and\
                self.score % 2 == 0 and\
                self.moves_without_eating < MAX_MOVES_WITHOUT_EATING / 2:

            # Choose longest path to tail
            return self.longest_path_to_tail()

        # Play any possible safe move and make sure path to tail is available
        if self.any_safe_move():
            return self.any_safe_move()

        # If path to tail is available
        if self.get_path_to_tail():
            # Choose shortest path to tail
            return self.get_path_to_tail()

        # Snake couldn't find a path and will probably die
        print('No available path, snake in danger!')

    def _process_bombs(self, dt):
        """Advance all bombs; return 'dead' if head is in explosion radius."""
        for bomb in self.bombs[:]:
            result = bomb.update(dt)
            if result == 'explode':
                exp = bomb.get_explosion_positions()
                # Head in blast → instant death
                if tuple(self.head.pos) in exp:
                    return 'dead'
                # Cut tail from the first piece inside the blast radius
                cut_index = None
                for i in range(1, len(self.squares)):
                    if tuple(self.squares[i].pos) in exp:
                        cut_index = i
                        break
                if cut_index is not None:
                    self.squares = self.squares[:cut_index]
                    self.squares[-1].is_tail = True
            if bomb.done:
                self.bombs.remove(bomb)
        return None

    def _eat_extra_apples(self):
        """Eat any extra apples at the head position. Returns number eaten."""
        count = 0
        for apple in self.extra_apples[:]:
            if self.head.pos == apple.pos:
                self.extra_apples.remove(apple)
                self.moves_without_eating = 0
                self.score += 1
                count += 1
        return count

    def update(self, dt):
        """
        Advance game logic by dt seconds.
        Returns: None (normal), 'quit', 'dead', 'stuck', 'won'
        """
        self.handle_events()
        if self.quit_game:
            return 'quit'

        # Tick down invincibility
        if self.invincible_timer > 0:
            self.invincible_timer = max(0.0, self.invincible_timer - dt)

        # Bombs (invincibility shields against explosions too)
        bomb_result = self._process_bombs(dt)
        if bomb_result == 'dead' and self.invincible_timer <= 0:
            return 'dead'

        # AI
        self.path = self.set_path()
        if self.path:
            self.go_to(self.path[0])

        self.move()

        # Win condition
        if self.score >= ROWS * ROWS - INITIAL_SNAKE_LENGTH:
            self.won_game = True
            print("Snake won the game after {} moves".format(self.total_moves))
            return 'won'

        self.total_moves += 1

        # Death conditions (skipped while invincible)
        if self.invincible_timer <= 0:
            if self.hitting_self() or self.head.hitting_wall():
                print("Snake is dead!")
                return 'dead'

            if self.moves_without_eating >= MAX_MOVES_WITHOUT_EATING:
                print("Snake got stuck!")
                return 'stuck'

        # Eat primary apple
        if self.eating_apple():
            self.add_square()

        # Eat extra apples
        eaten = self._eat_extra_apples()
        for _ in range(eaten):
            self.add_square()

        return None
