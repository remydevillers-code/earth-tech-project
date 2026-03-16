import pygame
import sys
import random
import math

pygame.init()

# --- Configuration ---
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("La Maison Verte")

# --- Couleurs ---
GREEN_LIGHT = (165, 245, 112)
GREEN_MID   = (76, 175, 80)
GREEN_BTN   = (26, 107, 46)
GREEN_HOVER = (46, 158, 74)
GREEN_TEXT  = (200, 240, 176)
GREEN_SUB   = (126, 207, 136)
MOON_COLOR  = (245, 208, 96)
MOON_INNER  = (255, 245, 200)

# --- Polices ---
font_title = pygame.font.SysFont("Georgia", 62, bold=True)
font_big   = pygame.font.SysFont("Georgia", 36, bold=True)
font_small = pygame.font.SysFont("Georgia", 22)
font_sub   = pygame.font.SysFont("Georgia", 15)

# --- Étoiles ---
stars = [
    (random.randint(0, WIDTH),
     random.randint(0, int(HEIGHT * 0.72)),
     random.randint(1, 2),
     random.uniform(0, 6.28))
    for _ in range(150)
]


# ── Fond dégradé nuit ──────────────────────────────────────────
def draw_bg(surface):
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(3  + (10 - 3)  * t)
        g = int(8  + (25 - 8)  * t)
        b = int(15 + (16 - 15) * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))


# ── Étoiles scintillantes ─────────────────────────────────────
def draw_stars(surface, tick):
    for (x, y, size, offset) in stars:
        brightness = int(180 + 75 * math.sin(tick * 0.04 + offset))
        brightness = max(60, min(255, brightness))
        pygame.draw.circle(surface, (brightness, brightness, brightness), (x, y), size)


# ── Lune ──────────────────────────────────────────────────────
def draw_moon(surface):
    pygame.draw.circle(surface, MOON_COLOR, (680, 55), 28)
    pygame.draw.circle(surface, MOON_INNER, (672, 48), 20)


# ── Sol / herbe ───────────────────────────────────────────────
def draw_ground(surface):
    for y in range(HEIGHT - 58, HEIGHT):
        t = (y - (HEIGHT - 58)) / 58
        r = int(13 + (6  - 13) * t)
        g = int(61 + (20 - 61) * t)
        b = int(26 + (8  - 26) * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))


# ── Bouton ────────────────────────────────────────────────────
def draw_button(surface, rect, text, font, hovered, big=False):
    color  = GREEN_HOVER if hovered else GREEN_BTN
    border = GREEN_LIGHT if hovered else GREEN_MID
    # Ombre
    pygame.draw.rect(surface, (2, 14, 5), rect.move(4, 4), border_radius=16)
    pygame.draw.rect(surface, color, rect, border_radius=16)
    pygame.draw.rect(surface, border, rect, width=3, border_radius=16)
    txt_color = GREEN_LIGHT if hovered else GREEN_TEXT
    label = font.render(text, True, txt_color)
    surface.blit(label, (rect.centerx - label.get_width() // 2,
                          rect.centery - label.get_height() // 2))


# ── MENU PRINCIPAL ────────────────────────────────────────────
def main_menu():
    clock = pygame.time.Clock()
    tick  = 0

    btn_play   = pygame.Rect(WIDTH // 2 - 170, 290, 340, 86)
    btn_char   = pygame.Rect(WIDTH // 2 - 202, 400, 188, 58)
    btn_credit = pygame.Rect(WIDTH // 2 + 14,  400, 188, 58)

    current_screen = "menu"

    while True:
        tick += 1
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                current_screen = "menu"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if current_screen == "menu":
                    if btn_play.collidepoint(mouse):
                        print("Lancement du jeu !")  # ← remplacer par appel jeu
                    elif btn_char.collidepoint(mouse):
                        current_screen = "character"
                    elif btn_credit.collidepoint(mouse):
                        current_screen = "credits"
                else:
                    current_screen = "menu"

        # ── Dessin ──
        draw_bg(screen)
        draw_stars(screen, tick)
        draw_moon(screen)
        draw_ground(screen)

        if current_screen == "menu":

            # Titre + ombre
            title        = font_title.render("LA MAISON VERTE", True, GREEN_LIGHT)
            title_shadow = font_title.render("LA MAISON VERTE", True, (0, 30, 0))
            tx = WIDTH // 2 - title.get_width() // 2
            screen.blit(title_shadow, (tx + 3, 163))
            screen.blit(title, (tx, 160))

            # Sous-titre
            sub = font_sub.render(
                "La planète a besoin de vous… commencez chez vous !",
                True, GREEN_SUB)
            screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 248))

            # Boutons
            draw_button(screen, btn_play,   "▶  JOUER",   font_big,   btn_play.collidepoint(mouse), big=True)
            draw_button(screen, btn_char,   "Personnage", font_small, btn_char.collidepoint(mouse))
            draw_button(screen, btn_credit, "Crédits",    font_small, btn_credit.collidepoint(mouse))

        elif current_screen == "character":
            msg  = font_big.render("Choix du Personnage", True, GREEN_LIGHT)
            info = font_small.render("(à implémenter)  —  Échap pour revenir", True, GREEN_SUB)
            screen.blit(msg,  (WIDTH // 2 - msg.get_width()  // 2, HEIGHT // 2 - 40))
            screen.blit(info, (WIDTH // 2 - info.get_width() // 2, HEIGHT // 2 + 20))

        elif current_screen == "credits":
            msg  = font_big.render("Crédits", True, GREEN_LIGHT)
            info = font_small.render("Développé par votre équipe  —  2025", True, GREEN_SUB)
            esc  = font_sub.render("Appuyez sur Échap pour revenir", True, (74, 122, 80))
            screen.blit(msg,  (WIDTH // 2 - msg.get_width()  // 2, HEIGHT // 2 - 60))
            screen.blit(info, (WIDTH // 2 - info.get_width() // 2, HEIGHT // 2))
            screen.blit(esc,  (WIDTH // 2 - esc.get_width()  // 2, HEIGHT // 2 + 50))

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main_menu()