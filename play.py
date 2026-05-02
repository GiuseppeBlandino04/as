from snake import *
from os import environ
import time as _time


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def draw_screen(surface):
    surface.fill(SURFACE_CLR)


def draw_grid(surface):
    x = y = 0
    for _ in range(ROWS):
        x += SQUARE_SIZE
        y += SQUARE_SIZE
        pygame.draw.line(surface, GRID_CLR, (x, 0), (x, HEIGHT))
        pygame.draw.line(surface, GRID_CLR, (0, y), (WIDTH, y))


def _font(size, bold=False):
    return pygame.font.SysFont('Arial', size, bold=bold)


def draw_death_screen(surface, score, round_time, death_timer, won=False):
    """Overlay a semi-transparent death / victory panel."""
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(170)
    overlay.fill((0, 0, 0))
    surface.blit(overlay, (0, 0))

    if won:
        title_clr, title_txt = (50, 255, 80), 'YOU WIN!'
    else:
        title_clr, title_txt = (255, 60, 60), 'GAME OVER'

    title = _font(58, bold=True).render(title_txt, True, title_clr)
    surface.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4 - 20))

    score_surf = _font(34).render(f'Score: {score}', True, (255, 215, 50))
    surface.blit(score_surf, (WIDTH // 2 - score_surf.get_width() // 2, HEIGHT // 2 - 45))

    mins, secs = int(round_time) // 60, int(round_time) % 60
    time_surf = _font(28).render(f'Time: {mins:02d}:{secs:02d}', True, (160, 210, 255))
    surface.blit(time_surf, (WIDTH // 2 - time_surf.get_width() // 2, HEIGHT // 2 + 10))

    secs_left = max(0, int(death_timer) + 1)
    restart_surf = _font(22).render(
        f'Press M to restart  (auto-restart in {secs_left}s)', True, (170, 170, 255))
    surface.blit(restart_surf,
                 (WIDTH // 2 - restart_surf.get_width() // 2, HEIGHT // 2 + 65))

    hint = _font(16).render(
        'C: +1 apple   V: +10 apples   B: +200 apples   N: bomb', True, (90, 90, 90))
    surface.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 28))


def calculate_score(apples_eaten, round_time, snake_length):
    """Score = 100 pts/apple + 1 pt/second survived + 5 pts/extra body square."""
    apple_pts = apples_eaten * 100
    time_pts = int(round_time)
    length_pts = max(0, snake_length - INITIAL_SNAKE_LENGTH) * 5
    return apple_pts + time_pts + length_pts


# ---------------------------------------------------------------------------
# Main game loop
# ---------------------------------------------------------------------------

def play_game():
    pygame.init()
    environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.display.set_caption('Snake Game')
    game_surface = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    snake = Snake(game_surface)
    game_state = 'playing'   # 'playing' | 'dead'
    death_timer = 10.0
    round_start = _time.time()
    final_score = 0
    final_time = 0.0
    won = False

    mainloop = True
    while mainloop:
        dt = clock.tick(FPS) / 1000.0

        if game_state == 'playing':
            draw_screen(game_surface)
            draw_grid(game_surface)
            result = snake.update(dt)
            snake.render()

            if result == 'quit':
                mainloop = False
            elif result in ('dead', 'stuck', 'won'):
                won = (result == 'won')
                final_time = _time.time() - round_start
                final_score = calculate_score(
                    snake.score, final_time, len(snake.squares))
                game_state = 'dead'
                death_timer = 10.0

        elif game_state == 'dead':
            death_timer = max(0.0, death_timer - dt)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    mainloop = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                    snake.reset()
                    game_state = 'playing'
                    round_start = _time.time()

            if death_timer <= 0 and game_state == 'dead':
                snake.reset()
                game_state = 'playing'
                round_start = _time.time()

            if game_state == 'dead':   # still dead — keep drawing
                draw_screen(game_surface)
                draw_grid(game_surface)
                snake.render()
                draw_death_screen(game_surface, final_score, final_time,
                                  death_timer, won=won)

        pygame.display.update()

    pygame.quit()


if __name__ == '__main__':
    play_game()
