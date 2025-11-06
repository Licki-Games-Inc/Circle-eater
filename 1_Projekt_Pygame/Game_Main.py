import pygame
import random
import json
import os
from datetime import datetime
import Game_Backend as gb

# -------------------- Pygame Setup --------------------
pygame.init()
WIDTH, HEIGHT = 1000, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Circle Eater")
clock = pygame.time.Clock()

# -------------------- Fonts & Colors -------------------
FONT = pygame.font.Font(None, 36)
SMALL_FONT = pygame.font.Font(None, 28)
BIG_FONT = pygame.font.Font(None, 72)
TITLE_FONT = pygame.font.Font(None, 84)

try:
    MONO_FONT = pygame.font.SysFont("consolas", 24)
except Exception:
    MONO_FONT = SMALL_FONT

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (220, 220, 220)
DARK = (40, 40, 40)
ACCENT = (0, 180, 0)
RED = (220, 40, 40)
SHADOW = (0, 0, 0, 140)

# -------------------- Sounds / Music --------------------
Button_Click_sfx = pygame.mixer.Sound("Python/1_Projekt_Pygame/Assets/sfx/pickupCoin.wav")
Enemy_Kill_sfx = pygame.mixer.Sound("Python/1_Projekt_Pygame/Assets/sfx/powerUp.wav")

Music_Background = pygame.mixer.Sound("Python/1_Projekt_Pygame/Assets/music/background_music.mp3")
# -------------------- Storage Paths -------------------
LEADERBOARD_PATH = "Python/1_Projekt_Pygame/Assets/save_files/leaderboard.json"
SETTINGS_PATH = "Python/1_Projekt_Pygame/Assets/save_files/settings.json"

# -------------------- Settings ------------------------
DEFAULT_SETTINGS = {
    "last_name": "Player",
    "master_volume": 0.8,   # 0..1
    "sfx_volume": 0.9,      # 0..1
    "fullscreen": False,
    "difficulty": "Normal"  # Easy | Normal | Hard
}

def load_settings():
    data = DEFAULT_SETTINGS.copy()
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                raw = json.load(f)
            for k, v in DEFAULT_SETTINGS.items():
                data[k] = raw.get(k, v)
        except Exception:
            pass
    return data

def save_settings(data):
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

SETTINGS = load_settings()

def apply_display_settings():
    global screen
    flags = pygame.FULLSCREEN if SETTINGS.get("fullscreen") else 0
    # Recreate display; keep logical width/height
    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)

def apply_audio_settings():
    # Master * SFX controls effective volume for game sfx
    eff = float(SETTINGS.get("master_volume", 1.0)) * float(SETTINGS.get("sfx_volume", 1.0))
    eff = max(0.0, min(1.0, eff))
    Button_Click_sfx.set_volume(eff)
    Enemy_Kill_sfx.set_volume(eff)

def apply_all_settings():
    apply_display_settings()
    apply_audio_settings()

apply_all_settings()

# -------------------- Leaderboard Storage --------------
def load_leaderboard():
    if not os.path.exists(LEADERBOARD_PATH):
        return {"runs": [], "best_time": None}
    try:
        with open(LEADERBOARD_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "runs" not in data or not isinstance(data["runs"], list):
            data["runs"] = []
        if "best_time" not in data or (data["best_time"] is not None and not isinstance(data["best_time"], (int, float))):
            data["best_time"] = None
        return data
    except Exception:
        # Backup corrupted file and start fresh
        try:
            os.rename(LEADERBOARD_PATH, LEADERBOARD_PATH + ".bak")
        except Exception:
            pass
        return {"runs": [], "best_time": None}

def save_leaderboard(data):
    with open(LEADERBOARD_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_run_and_check_record(final_time_s, player_name):
    """
    Append a run; also keep legacy 'best_time' updated.
    Each run now has: time (float), date (str), name (str).
    """
    data = load_leaderboard()
    prev_best = data.get("best_time", None)
    is_new = (prev_best is None) or (final_time_s < prev_best - 1e-9)

    run = {
        "time": float(final_time_s),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "name": player_name if player_name else "Player"
    }

    data.setdefault("runs", []).append(run)

    if is_new:
        data["best_time"] = float(final_time_s)

    save_leaderboard(data)
    return is_new, data["best_time"]

# -------------------- UI Helpers ----------------------
def draw_centered(surface, surf, y_offset=0):
    rect = surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + y_offset))
    surface.blit(surf, rect)

def blur_surface(source_surf, factor=8):
    if factor < 2:
        return source_surf.copy()
    small = pygame.transform.smoothscale(
        source_surf, (max(1, WIDTH // factor), max(1, HEIGHT // factor))
    )
    return pygame.transform.smoothscale(small, (WIDTH, HEIGHT))

# Name Tag Drawing 
def draw_name_tag(surface, text, x, y, radius, y_gap=6):
    """Draws a label centered above the player's head that follows their position."""
    # Position: centered horizontally, a few pixels above the circle
    midbottom = (x, y - radius - y_gap)

    # Outline for readability
    label_main = SMALL_FONT.render(text, True, (255, 255, 255))  # white text
    label_shadow = SMALL_FONT.render(text, True, (0, 0, 0))      # black outline

    rect = label_main.get_rect(midbottom=midbottom)
    # simple 4-direction outline
    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
        surface.blit(label_shadow, rect.move(dx, dy))
    surface.blit(label_main, rect)


class Button:
    def __init__(self, text, center, size=(240, 64)):
        self.text = text
        self.center = center
        self.size = size
        self.rect = pygame.Rect(0, 0, *size)
        self.rect.center = center

    def draw(self, surface, hovered=False, disabled=False):
        if disabled:
            bg = (200, 200, 200)
            fg = (120, 120, 120)
            border = (160, 160, 160)
        else:
            bg = (235, 235, 235) if hovered else WHITE
            fg = BLACK
            border = DARK
        pygame.draw.rect(surface, bg, self.rect, border_radius=18)
        pygame.draw.rect(surface, border, self.rect, 3, border_radius=18)
        label = FONT.render(self.text, True, fg)
        label_rect = label.get_rect(center=self.rect.center)
        surface.blit(label, label_rect)

    def is_hover(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

# ----- Simple Slider UI (0..1) -----
class Slider:
    def __init__(self, topleft, width=280, value=1.0):
        self.track_rect = pygame.Rect(topleft[0], topleft[1], width, 10)
        self.handle_radius = 10
        self.value = max(0.0, min(1.0, float(value)))
        self.dragging = False

    def value_to_x(self):
        return self.track_rect.x + int(self.value * self.track_rect.w)

    def draw(self, surface):
        # Track
        pygame.draw.rect(surface, (210, 210, 210), self.track_rect, border_radius=5)
        # Fill to value
        fill_rect = self.track_rect.copy()
        fill_rect.w = int(self.value * self.track_rect.w)
        pygame.draw.rect(surface, ACCENT, fill_rect, border_radius=5)
        # Handle
        hx = self.value_to_x()
        hy = self.track_rect.centery
        pygame.draw.circle(surface, DARK, (hx, hy), self.handle_radius)
        pygame.draw.circle(surface, WHITE, (hx, hy), self.handle_radius - 3)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # Start drag if near handle
            hx, hy = self.value_to_x(), self.track_rect.centery
            if (mx - hx) ** 2 + (my - hy) ** 2 <= (self.handle_radius + 4) ** 2 or self.track_rect.collidepoint(mx, my):
                self.dragging = True
                self._set_value_from_mouse(mx)
                Button_Click_sfx.play()
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                Button_Click_sfx.play()
                return True
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_value_from_mouse(event.pos[0])
            return True
        return False

    def _set_value_from_mouse(self, mx):
        rel = (mx - self.track_rect.x) / float(self.track_rect.w)
        self.value = max(0.0, min(1.0, rel))

# -------------------- Text Input Dialog ----------------
def text_input_dialog(prompt, default_text="Player", max_len=16):
    """
    Simple blocking text input overlay that returns the entered string.
    Esc to cancel (returns default_text). Enter to accept.
    """
    # Capture background and dim
    captured = screen.copy()
    blurred = blur_surface(captured, factor=12)
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill(SHADOW)
    blurred.blit(overlay, (0, 0))

    # Input box
    box_w, box_h = 520, 160
    box_rect = pygame.Rect(0, 0, box_w, box_h)
    box_rect.center = (WIDTH // 2, HEIGHT // 2)

    text = list(default_text)
    caret_visible = True
    caret_timer = 0
    caret_interval = 400  # ms

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "".join(text) if text else default_text
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    Button_Click_sfx.play()
                    s = "".join(text).strip()
                    return s if s else default_text
                elif event.key == pygame.K_ESCAPE:
                    Button_Click_sfx.play()
                    Music_Background.stop()
                    return default_text
                elif event.key == pygame.K_BACKSPACE:
                    if text:
                        text.pop()
                else:
                    ch = event.unicode
                    if ch and ch.isprintable() and len(text) < max_len:
                        text.append(ch)

        # Blink caret
        caret_timer += clock.get_time()
        if caret_timer >= caret_interval:
            caret_visible = not caret_visible
            caret_timer = 0

        # Draw dialog
        screen.blit(blurred, (0, 0))
        # Card
        pygame.draw.rect(screen, WHITE, box_rect, border_radius=18)
        pygame.draw.rect(screen, DARK, box_rect, 3, border_radius=18)

        title = FONT.render(prompt, True, BLACK)
        screen.blit(title, (box_rect.x + 24, box_rect.y + 16))

        # Text line
        content = "".join(text)
        text_surf = BIG_FONT.render(content, True, ACCENT)
        tx = box_rect.x + 24
        ty = box_rect.y + 64
        screen.blit(text_surf, (tx, ty))

        # Caret
        if caret_visible:
            caret_x = tx + text_surf.get_width() + 6
            caret_y = ty + 6
            pygame.draw.rect(screen, ACCENT, (caret_x, caret_y, 3, text_surf.get_height() - 12))

        hint = SMALL_FONT.render("Enter = OK    •    Esc = Cancel", True, DARK)
        screen.blit(hint, (box_rect.centerx - hint.get_width() // 2, box_rect.bottom - 34))

        pygame.display.flip()
        clock.tick(60)

# -------------------- Game Classes --------------------
class Circle:
    def __init__(self, circles, player):
        self.r = random.randint(10, 30)
        self.color = (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        )
        # Try random positions until we don't overlap circles or player
        while True:
            self.x = random.randint(50, WIDTH - 50)
            self.y = random.randint(50, HEIGHT - 50)

            no_circle_overlap = all(not self.check_collision(other) for other in circles)
            no_player_overlap = not self.check_collision_player(player)

            if no_circle_overlap and no_player_overlap:
                break

    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (self.x, self.y), self.r)

    def check_collision(self, other):
        dx = self.x - other.x
        dy = self.y - other.y
        dist_sq = dx * dx + dy * dy
        rs = self.r + other.r
        return dist_sq < rs * rs

    def check_collision_player(self, player):
        dx = self.x - player.x
        dy = self.y - player.y
        dist_sq = dx * dx + dy * dy
        rs = self.r + player.radius
        return dist_sq <= rs * rs

# -------------------- Difficulty helpers ----------------
def get_difficulty_speed_multiplier():
    diff = SETTINGS.get("difficulty", "Normal")
    if diff == "Easy":
        return 0.75
    if diff == "Hard":
        return 1.25
    return 1.0  # Normal

# -------------------- Game Loop -----------------------
def run_game():
    
    Music_Background.play(-40)
    # Player
    player = gb.Player(100, 100, 25, 5, (255, 0, 0))
    player.health = 100

    # Circles
    num_circles = random.randint(5, 20)
    circles = [Circle([], player)]
    for _ in range(1, num_circles):
        circles.append(Circle(circles, player))

    # Velocities parallel to circles list (respect difficulty)
    base_speeds = [-5, 5]
    mult = get_difficulty_speed_multiplier()
    vels = [[random.choice(base_speeds) * mult, random.choice(base_speeds) * mult] for _ in range(len(circles))]

    # Score + timer
    points = 0
    start_ticks = pygame.time.get_ticks()
    game_won = False
    final_time_s = None
    blurred_frame = None
    is_new_record = False  # set upon win

    while True:
        # ---------- Events ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                Music_Background.stop()
                return ("menu", None)
            if event.type == pygame.KEYDOWN:
                if not game_won and event.key == pygame.K_ESCAPE:
                    Button_Click_sfx.play()
                    Music_Background.stop()
                    return ("menu", None)
                if game_won and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                    Button_Click_sfx.play()
                    Music_Background.stop()
                    return ("menu", None)

        keys = pygame.key.get_pressed()

        # ---------- Win Screen ----------
        if game_won:
            # Redraw blurred frame with overlays each tick
            screen.blit(blurred_frame, (0, 0))
            title = BIG_FONT.render("Game Won!", True, ACCENT)
            time_text = FONT.render(f"Your time: {final_time_s:.2f} s", True, WHITE)
            hint_text = FONT.render("Press ENTER or ESC to return", True, WHITE)

            draw_centered(screen, title, y_offset=-60)
            draw_centered(screen, time_text, y_offset=0)
            if is_new_record:
                nr_text = BIG_FONT.render("New Record!", True, RED)
                draw_centered(screen, nr_text, y_offset=60)
            draw_centered(screen, hint_text, y_offset=120)

            pygame.display.flip()
            clock.tick(60)
            Music_Background.stop()

            continue

        # ---------- Gameplay ----------
        # Move player
        if keys[pygame.K_LEFT]:
            player.x -= player.move_speed
        if keys[pygame.K_RIGHT]:
            player.x += player.move_speed
        if keys[pygame.K_UP]:
            player.y -= player.move_speed
        if keys[pygame.K_DOWN]:
            player.y += player.move_speed

        # Keep in bounds
        player.x = max(player.radius, min(player.x, WIDTH - player.radius))
        player.y = max(player.radius, min(player.y, HEIGHT - player.radius))

        # Move circles + bounce + destroy
        i = 0
        while i < len(circles):
            c = circles[i]
            vx, vy = vels[i]
            c.x += vx
            c.y += vy

            # Wall bounce
            if c.x - c.r <= 0:
                c.x = c.r
                vels[i][0] = -vx
            elif c.x + c.r >= WIDTH:
                c.x = WIDTH - c.r
                vels[i][0] = -vx

            if c.y - c.r <= 0:
                c.y = c.r
                vels[i][1] = -vy
            elif c.y + c.r >= HEIGHT:
                c.y = HEIGHT - c.r
                vels[i][1] = -vy

            # Circle-circle bounce (simple)
            for j in range(i + 1, len(circles)):
                if c.check_collision(circles[j]):
                    vels[i][0] = -vels[i][0]
                    vels[i][1] = -vels[i][1]
                    vels[j][0] = -vels[j][0]
                    vels[j][1] = -vels[j][1]

            # destroy on player collision
            if c.check_collision_player(player):
                points += 1
                circles.pop(i)
                vels.pop(i)
                Enemy_Kill_sfx.play()
                continue

            i += 1

        # ---------- Draw ----------
        screen.fill(WHITE)
        for c in circles:
            c.draw(screen)
        pygame.draw.circle(screen, player.color, (player.x, player.y), player.radius)
        draw_name_tag(screen, SETTINGS.get("last_name", "Player"), player.x, player.y, player.radius)


        # HUD
        elapsed_s = (pygame.time.get_ticks() - start_ticks) / 1000.0
        points_surf = FONT.render(f"Points: {points}", True, BLACK)
        timer_surf = FONT.render(f"Time: {elapsed_s:.2f} s", True, BLACK)
        screen.blit(points_surf, (10, 10))
        screen.blit(timer_surf, (10, 45))

        # Win check -> blur screen, show New Record if applicable, save run
        if len(circles) == 0 and not game_won:
            final_time_s = elapsed_s

            # Use stored name automatically
            name_entered = SETTINGS.get("last_name", "Player")


            # Determine record BEFORE saving (so we compare to previous best)
            prev = load_leaderboard().get("best_time", None)
            is_new_record = (prev is None) or (final_time_s < prev - 1e-9)

            # Save the run and update best
            _is_new_confirm, _best_after = add_run_and_check_record(final_time_s, name_entered)

            # Prepare blurred background
            captured = screen.copy()
            blurred = blur_surface(captured, factor=10)
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill(SHADOW)
            blurred.blit(overlay, (0, 0))
            blurred_frame = blurred
            game_won = True

        pygame.display.flip()
        clock.tick(60)

# -------------------- Leaderboard Screen ----------------
def leaderboard_screen():
    back_btn = Button("Back", center=(120, HEIGHT - 50), size=(180, 50))
    clear_btn = Button("Clear All", center=(WIDTH - 140, HEIGHT - 50), size=(200, 50))
    Music_Background.stop()

    # Layout
    TITLE_Y = 40
    SUMMARY_Y = 100
    TABLE_Y = 160
    ROW_START_Y = TABLE_Y + 36
    ROW_H = 32
    MAX_VISIBLE_ROWS = 8

    # Columns (x-positions)
    COL_RANK_X = 60
    COL_NAME_X = 130
    COL_TIME_X = 360
    COL_DATE_X = 470

    # State
    scroll = 0  # top-most visible index
    sort_mode = "recent"  # "recent" or "best"

    while True:
        data = load_leaderboard()
        runs = data.get("runs", [])
        total = len(runs)

        # Sort runs based on mode
        if sort_mode == "recent":
            runs_sorted = sorted(runs, key=lambda r: r.get("date", ""), reverse=True)
            title_suffix = "• Sorting: Recent"
        else:
            runs_sorted = sorted(runs, key=lambda r: r.get("time", float("inf")))
            title_suffix = "• Sorting: Best Times"

        # Compute best time display (robust)
        best_time = None
        if runs:
            try:
                best_time = min(r.get("time", float("inf")) for r in runs)
                if best_time == float("inf"):
                    best_time = None
            except Exception:
                best_time = data.get("best_time", None)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    Button_Click_sfx.play()
                    Music_Background.stop()
                    return
                elif event.key == pygame.K_UP:
                    scroll = max(0, scroll - 1)
                elif event.key == pygame.K_DOWN:
                    max_scroll = max(0, total - MAX_VISIBLE_ROWS)
                    scroll = min(max_scroll, scroll + 1)
                elif event.key == pygame.K_HOME:
                    scroll = 0
                elif event.key == pygame.K_END:
                    scroll = max(0, total - MAX_VISIBLE_ROWS)
                elif event.key == pygame.K_s:
                    # toggle sort
                    sort_mode = "best" if sort_mode == "recent" else "recent"
                    Button_Click_sfx.play()
                    scroll = 0
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse = pygame.mouse.get_pos()
                    if back_btn.is_hover(mouse):
                        Button_Click_sfx.play()
                        return
                    if clear_btn.is_hover(mouse) and total > 0:
                        Button_Click_sfx.play()
                        save_leaderboard({"runs": [], "best_time": None})
                        scroll = 0
                elif event.button == 4:  # wheel up
                    scroll = max(0, scroll - 1)
                elif event.button == 5:  # wheel down
                    max_scroll = max(0, total - MAX_VISIBLE_ROWS)
                    scroll = min(max_scroll, scroll + 1)

        # ----- Draw -----
        screen.fill(WHITE)

        # Title (centered top)
        title_surf = TITLE_FONT.render("Leaderboard", True, ACCENT)
        screen.blit(title_surf, ((WIDTH - title_surf.get_width()) // 2, TITLE_Y))

        # Summary (centered)
        best_text = "—" if best_time is None else f"{best_time:.2f} s"
        summary_line = f"Best Time: {best_text}   •   Total Plays: {total}   {title_suffix}"
        summary_surf = FONT.render(summary_line, True, BLACK)
        screen.blit(summary_surf, ((WIDTH - summary_surf.get_width()) // 2, SUMMARY_Y))

        # Headers
        header_rank = SMALL_FONT.render("Rank", True, DARK)
        header_name = SMALL_FONT.render("Name", True, DARK)
        header_time = SMALL_FONT.render("Time (s)", True, DARK)
        header_date = SMALL_FONT.render("Date", True, DARK)
        screen.blit(header_rank, (COL_RANK_X, TABLE_Y))
        screen.blit(header_name, (COL_NAME_X, TABLE_Y))
        screen.blit(header_time, (COL_TIME_X, TABLE_Y))
        screen.blit(header_date, (COL_DATE_X, TABLE_Y))

        # Horizontal guide line
        pygame.draw.line(screen, (200, 200, 200), (COL_RANK_X, TABLE_Y + 28), (WIDTH - 80, TABLE_Y + 28), 2)

        # Visible rows
        start = scroll
        end = min(total, start + MAX_VISIBLE_ROWS)
        y = ROW_START_Y
        for idx in range(start, end):
            run = runs_sorted[idx]
            rank = idx + 1
            t = run.get("time", 0.0)
            d = run.get("date", "")
            nm = run.get("name", "Player")

            rank_s = MONO_FONT.render(f"{rank}", True, BLACK)
            name_s = MONO_FONT.render(nm, True, BLACK)
            time_s = MONO_FONT.render(f"{t:.2f}", True, BLACK)
            date_s = MONO_FONT.render(d, True, BLACK)
            screen.blit(rank_s, (COL_RANK_X, y))
            screen.blit(name_s, (COL_NAME_X, y))
            screen.blit(time_s, (COL_TIME_X, y))
            screen.blit(date_s, (COL_DATE_X, y))

            y += ROW_H

        # Scroll hint + sort hint
        hint_text = "Scroll: Mouse Wheel / Up-Down • Home/End • S to toggle sorting • Enter/Esc to go back"
        hint = SMALL_FONT.render(hint_text, True, DARK)
        screen.blit(hint, (COL_RANK_X, y + 8))

        # Buttons
        mouse = pygame.mouse.get_pos()
        back_btn.draw(screen, hovered=back_btn.is_hover(mouse))
        clear_btn.draw(screen, hovered=clear_btn.is_hover(mouse), disabled=(total == 0))

        pygame.display.flip()
        clock.tick(60)

# -------------------- Settings Screen ----------------
def settings_screen():
    title_surf = TITLE_FONT.render("Settings", True, ACCENT)

    # ---- Vertical rhythm (tweak these numbers to taste)
    NAME_Y  = 140
    FULL_Y  = NAME_Y + 70
    DIFF_Y  = FULL_Y + 110        # extra space before Difficulty
    MV_Y    = DIFF_Y + 90        # Master Volume row
    SFX_Y   = MV_Y + 70          # SFX Volume row
    RESET_Y = SFX_Y + 140
    BACK_Y  = RESET_Y + 70

    MARGIN_X = 80
    SLIDER_W = max(360, WIDTH - 2 * MARGIN_X - 60)
    LABEL_TO_CTRL_GAP = 28

    # --- Buttons
    btn_change_name = Button("Change Name",       center=(WIDTH // 2, NAME_Y + 36), size=(260, 54))
    btn_toggle_full = Button("Toggle Fullscreen", center=(WIDTH // 2, FULL_Y + 36), size=(280, 54))
    btn_diff = Button(f"Difficulty: {SETTINGS.get('difficulty','Normal')}",
                      center=(WIDTH // 2, DIFF_Y), size=(260, 54))
    diff_hint = SMALL_FONT.render("(Press D to cycle difficulty)", True, DARK)
    diff_hint_pos = (WIDTH // 2 - diff_hint.get_width() // 2, DIFF_Y + 32)

    # --- Sliders
    master_label_pos = (MARGIN_X, MV_Y)
    master_slider = Slider((WIDTH // 2 - SLIDER_W // 2, MV_Y + LABEL_TO_CTRL_GAP),
                           width=SLIDER_W, value=SETTINGS.get("master_volume", 0.8))

    sfx_label_pos = (MARGIN_X, SFX_Y)
    sfx_slider = Slider((WIDTH // 2 - SLIDER_W // 2, SFX_Y + LABEL_TO_CTRL_GAP),
                        width=SLIDER_W, value=SETTINGS.get("sfx_volume", 0.9))

    btn_reset = Button("Reset to Defaults", center=(WIDTH // 2, RESET_Y), size=(260, 54))
    btn_back  = Button("Back",              center=(WIDTH // 2, BACK_Y),  size=(180, 50))

    # Pre-render helpers
    def render_name_label():
        return FONT.render(f"Name: {SETTINGS.get('last_name','Player')}", True, BLACK)

    def render_full_label():
        return FONT.render(f"Fullscreen: {'On' if SETTINGS.get('fullscreen') else 'Off'}", True, BLACK)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

            # Sliders handle drag first
            if master_slider.handle_event(event):
                SETTINGS["master_volume"] = round(master_slider.value, 3)
                save_settings(SETTINGS)
                apply_audio_settings()

            if sfx_slider.handle_event(event):
                SETTINGS["sfx_volume"] = round(sfx_slider.value, 3)
                save_settings(SETTINGS)
                apply_audio_settings()

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    Button_Click_sfx.play()
                    Music_Background.stop()
                    return
                if event.key == pygame.K_f:
                    SETTINGS["fullscreen"] = not SETTINGS.get("fullscreen", False)
                    save_settings(SETTINGS)
                    apply_display_settings()
                    Button_Click_sfx.play()
                if event.key == pygame.K_d:
                    SETTINGS["difficulty"] = next_difficulty(SETTINGS.get("difficulty", "Normal"))
                    btn_diff.text = f"Difficulty: {SETTINGS['difficulty']}"
                    save_settings(SETTINGS)
                    Button_Click_sfx.play()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()

                if btn_change_name.is_hover((mx, my)):
                    Button_Click_sfx.play()
                    new_name = text_input_dialog("Enter your display name:", SETTINGS.get("last_name", "Player"))
                    SETTINGS["last_name"] = new_name
                    save_settings(SETTINGS)

                elif btn_toggle_full.is_hover((mx, my)):
                    SETTINGS["fullscreen"] = not SETTINGS.get("fullscreen", False)
                    save_settings(SETTINGS)
                    apply_display_settings()
                    Button_Click_sfx.play()

                elif btn_diff.is_hover((mx, my)):
                    SETTINGS["difficulty"] = next_difficulty(SETTINGS.get("difficulty", "Normal"))
                    btn_diff.text = f"Difficulty: {SETTINGS['difficulty']}"
                    save_settings(SETTINGS)
                    Button_Click_sfx.play()

                elif btn_reset.is_hover((mx, my)):
                    SETTINGS.update(DEFAULT_SETTINGS)
                    save_settings(SETTINGS)
                    # Reflect defaults in UI and audio/display
                    btn_diff.text = f"Difficulty: {SETTINGS['difficulty']}"
                    master_slider.value = SETTINGS["master_volume"]
                    sfx_slider.value = SETTINGS["sfx_volume"]
                    apply_all_settings()
                    Button_Click_sfx.play()

                elif btn_back.is_hover((mx, my)):
                    Button_Click_sfx.play()
                    return

        # ---- Draw ----
        screen.fill(WHITE)
        # Title
        draw_centered(screen, title_surf, y_offset=-(HEIGHT // 2 - 60))

        # Row: Name
        screen.blit(render_name_label(), (MARGIN_X, NAME_Y))
        btn_change_name.draw(screen, hovered=btn_change_name.is_hover(pygame.mouse.get_pos()))

        # Row: Fullscreen
        screen.blit(render_full_label(), (MARGIN_X, FULL_Y))
        btn_toggle_full.draw(screen, hovered=btn_toggle_full.is_hover(pygame.mouse.get_pos()))

        # Row: Difficulty + hint
        btn_diff.draw(screen, hovered=btn_diff.is_hover(pygame.mouse.get_pos()))
        screen.blit(diff_hint, diff_hint_pos)

        # Row: Master Volume
        screen.blit(FONT.render("Master Volume", True, BLACK), master_label_pos)
        master_slider.draw(screen)
        mv_txt = SMALL_FONT.render(f"{int(master_slider.value * 100)}%", True, DARK)
        screen.blit(mv_txt, (master_slider.track_rect.right + 12, master_slider.track_rect.y - 8))

        # Row: SFX Volume
        screen.blit(FONT.render("SFX Volume", True, BLACK), sfx_label_pos)
        sfx_slider.draw(screen)
        sv_txt = SMALL_FONT.render(f"{int(sfx_slider.value * 100)}%", True, DARK)
        screen.blit(sv_txt, (sfx_slider.track_rect.right + 12, sfx_slider.track_rect.y - 8))

        # Bottom buttons
        btn_reset.draw(screen, hovered=btn_reset.is_hover(pygame.mouse.get_pos()))
        btn_back.draw(screen, hovered=btn_back.is_hover(pygame.mouse.get_pos()))

        # Footer hint
        footer = SMALL_FONT.render("Esc/Enter = Back  •  F = Toggle Fullscreen  •  D = Cycle Difficulty", True, DARK)
        screen.blit(footer, (WIDTH // 2 - footer.get_width() // 2, HEIGHT - 26 - footer.get_height()))

        pygame.display.flip()
        clock.tick(60)


def next_difficulty(cur):
    order = ["Easy", "Normal", "Hard"]
    try:
        i = order.index(cur)
    except ValueError:
        i = 1
    return order[(i + 1) % len(order)]

# -------------------- Main Menu -----------------------
def main_menu():
    title = TITLE_FONT.render("Circle Eater", True, ACCENT)
    subtitle = FONT.render("Eat all circles as fast as you can!", True, BLACK)

    btn_play = Button("Play", center=(WIDTH // 2, HEIGHT // 2))
    btn_leader = Button("Leaderboard", center=(WIDTH // 2, HEIGHT // 2 + 90), size=(260, 64))
    btn_settings = Button("Settings", center=(WIDTH // 2, HEIGHT // 2 + 180), size=(220, 64))
    btn_quit = Button("Quit", center=(WIDTH // 2, HEIGHT // 2 + 270))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    Button_Click_sfx.play()
                    return "play"
                if event.key == pygame.K_ESCAPE:
                    Music_Background.stop()
                    Button_Click_sfx.play()
                    return "quit"
                if event.key == pygame.K_l:
                    Button_Click_sfx.play()
                    Music_Background.stop()
                    return "leaderboard"
                if event.key == pygame.K_s:
                    Button_Click_sfx.play()
                    Music_Background.stop()
                    return "settings"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_play.is_hover(pygame.mouse.get_pos()):
                    Button_Click_sfx.play()
                    return "play"
                if btn_leader.is_hover(pygame.mouse.get_pos()):
                    Button_Click_sfx.play()
                    Music_Background.stop()
                    return "leaderboard"
                if btn_settings.is_hover(pygame.mouse.get_pos()):
                    Button_Click_sfx.play()
                    Music_Background.stop()
                    return "settings"
                if btn_quit.is_hover(pygame.mouse.get_pos()):
                    Button_Click_sfx.play()
                    Music_Background.stop()
                    return "quit"

        # Draw menu
        screen.fill(WHITE)
        draw_centered(screen, title, y_offset=-180)
        draw_centered(screen, subtitle, y_offset=-130)

        mouse = pygame.mouse.get_pos()
        btn_play.draw(screen, hovered=btn_play.is_hover(mouse))
        btn_leader.draw(screen, hovered=btn_leader.is_hover(mouse))
        btn_settings.draw(screen, hovered=btn_settings.is_hover(mouse))
        btn_quit.draw(screen, hovered=btn_quit.is_hover(mouse))

        hint = FONT.render("ENTER/SPACE = Play   •   L = Leaderboard   •   S = Settings   •   ESC = Quit", True, DARK)
        draw_centered(screen, hint, y_offset=360)

        pygame.display.flip()
        clock.tick(60)

# -------------------- Running Loop ------------------------
def main():
    while True:
        choice = main_menu()
        if choice == "quit":
            break
        elif choice == "leaderboard":
            leaderboard_screen()
            continue
        elif choice == "settings":
            settings_screen()
            continue
        elif choice == "play":
            run_game()
            continue

    pygame.quit()

if __name__ == "__main__":
    main()