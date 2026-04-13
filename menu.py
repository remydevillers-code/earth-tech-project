import pygame
import sys
import random
import math
from credits import show_credits
from game import run_game

GREEN_LIGHT = (165, 245, 112)
GREEN_MID   = (76, 175, 80)
GREEN_BTN   = (26, 107, 46)
GREEN_HOVER = (46, 158, 74)
GREEN_TEXT  = (200, 240, 176)
GREEN_SUB   = (126, 207, 136)
MOON_COLOR  = (245, 208, 96)
MOON_INNER  = (255, 245, 200)


def draw_bg(surface, width, height):
    for y in range(height):
        t = y / height
        r = int(3  + (10 - 3)  * t)
        g = int(8  + (25 - 8)  * t)
        b = int(15 + (16 - 15) * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))


def draw_stars(surface, stars, tick):
    for (x, y, size, offset) in stars:
        brightness = int(180 + 75 * math.sin(tick * 0.04 + offset))
        brightness = max(60, min(255, brightness))
        pygame.draw.circle(surface, (brightness, brightness, brightness), (x, y), size)


def draw_moon(surface, width):
    cx = width - 120
    pygame.draw.circle(surface, MOON_COLOR, (cx, 55), 28)
    pygame.draw.circle(surface, MOON_INNER, (cx - 8, 48), 20)


def draw_ground(surface, width, height):
    for y in range(height - 58, height):
        t = (y - (height - 58)) / 58
        r = int(13 + (6  - 13) * t)
        g = int(61 + (20 - 61) * t)
        b = int(26 + (8  - 26) * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))


def draw_button(surface, rect, text, font, hovered, big=False):
    color  = GREEN_HOVER if hovered else GREEN_BTN
    border = GREEN_LIGHT if hovered else GREEN_MID
    pygame.draw.rect(surface, (2, 14, 5), rect.move(4, 4), border_radius=16)
    pygame.draw.rect(surface, color,  rect, border_radius=16)
    pygame.draw.rect(surface, border, rect, width=3, border_radius=16)
    txt_color = GREEN_LIGHT if hovered else GREEN_TEXT
    label = font.render(text, True, txt_color)
    surface.blit(label, (rect.centerx - label.get_width()  // 2,
                         rect.centery - label.get_height() // 2))


# ── MENU PRINCIPAL ────────────────────────────────────────────
# ── MENU PRINCIPAL ────────────────────────────────────────────
def main_menu():
    # Résolution réelle de l'écran → plein écran
    info = pygame.display.Info()
    WIDTH = info.current_w
    HEIGHT = info.current_h
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption("La Maison Verte")

    # Taille des polices proportionnelle à la hauteur d'écran
    scale = HEIGHT / 600
    font_title = pygame.font.SysFont("Georgia", int(62 * scale), bold=True)
    font_big = pygame.font.SysFont("Georgia", int(36 * scale), bold=True)
    font_small = pygame.font.SysFont("Georgia", int(22 * scale))
    font_sub = pygame.font.SysFont("Georgia", int(15 * scale))

    stars = [
        (random.randint(0, WIDTH),
         random.randint(0, int(HEIGHT * 0.72)),
         random.randint(1, 2),
         random.uniform(0, 6.28))
        for _ in range(150)
    ]

    clock = pygame.time.Clock()
    tick = 0

    # Nouveaux placements des boutons (remontés pour faire de la place)
    btn_play = pygame.Rect(WIDTH // 2 - int(170 * scale), int(270 * scale), int(340 * scale), int(86 * scale))
    btn_credit = pygame.Rect(WIDTH // 2 - int(94 * scale), int(380 * scale), int(188 * scale), int(58 * scale))

    # 1. Création du nouveau bouton Quitter
    btn_quit = pygame.Rect(WIDTH // 2 - int(94 * scale), int(460 * scale), int(188 * scale), int(58 * scale))

    current_screen = "menu"

    while True:
        tick += 1
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if current_screen == "credits":
                    current_screen = "menu"
                else:
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if current_screen == "menu":
                    if btn_play.collidepoint(mouse):
                        from game import run_game  # Import ici pour éviter les bugs circulaires
                        run_game(screen, WIDTH, HEIGHT)
                    elif btn_credit.collidepoint(mouse):
                        current_screen = "credits"

                    # 2. Gestion du clic sur Quitter
                    elif btn_quit.collidepoint(mouse):
                        pygame.quit()
                        sys.exit()

                elif current_screen == "credits":
                    from credits import back_button_rect
                    if back_button_rect(WIDTH, HEIGHT, scale).collidepoint(mouse):
                        current_screen = "menu"

        # ── Dessin ──
        draw_bg(screen, WIDTH, HEIGHT)
        draw_stars(screen, stars, tick)
        draw_moon(screen, WIDTH)
        draw_ground(screen, WIDTH, HEIGHT)

        if current_screen == "menu":
            title = font_title.render("LA MAISON VERTE", True, GREEN_LIGHT)
            title_shadow = font_title.render("LA MAISON VERTE", True, (0, 30, 0))
            tx = WIDTH // 2 - title.get_width() // 2
            ty = int(160 * scale)
            screen.blit(title_shadow, (tx + 3, ty + 3))
            screen.blit(title, (tx, ty))

            sub = font_sub.render(
                "La planète a besoin de vous… commencez chez vous !",
                True, GREEN_SUB)
            screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, int(230 * scale)))  # Sous-titre légèrement remonté

            draw_button(screen, btn_play, "▶  JOUER", font_big, btn_play.collidepoint(mouse), big=True)
            draw_button(screen, btn_credit, "Crédits", font_small, btn_credit.collidepoint(mouse))

            # 3. Affichage du bouton Quitter
            draw_button(screen, btn_quit, "Quitter", font_small, btn_quit.collidepoint(mouse))

        elif current_screen == "credits":
            show_credits(screen, WIDTH, HEIGHT, font_big, font_small, font_sub,
                         GREEN_LIGHT, GREEN_MID, GREEN_TEXT, GREEN_SUB)

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    pygame.init()
    main_menu()
    pygame.quit()