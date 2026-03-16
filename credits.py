import pygame
import math


def show_credits(screen, WIDTH, HEIGHT, font_big, font_small, font_sub,
                 GREEN_LIGHT, GREEN_MID, GREEN_TEXT, GREEN_SUB):
    """Affiche l'écran des crédits — appelez cette fonction dans votre boucle principale."""

    # ── Noms de l'équipe (modifiez ici) ──
    noms = [
        "Lucas Faux",
        "Maxime Oudin",
        "Hugo Marot",
        "Remy Devillers",
        "Hugo Hendrickx",
        "Ahmad Fadel",
    ]

    # Titre
    msg = font_big.render("Crédits", True, GREEN_LIGHT)
    screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, 60))

    # Rectangle fond
    rect_w, rect_h = 400, 320
    rect_x = WIDTH  // 2 - rect_w // 2
    rect_y = 130
    pygame.draw.rect(screen, (15, 40, 20),
                     pygame.Rect(rect_x, rect_y, rect_w, rect_h), border_radius=16)
    pygame.draw.rect(screen, GREEN_MID,
                     pygame.Rect(rect_x, rect_y, rect_w, rect_h), width=3, border_radius=16)

    # Noms
    for i, nom in enumerate(noms):
        label = font_small.render(nom, True, GREEN_TEXT)
        screen.blit(label, (WIDTH // 2 - label.get_width() // 2,
                            rect_y + 30 + i * 46))

    # Retour
    esc = font_sub.render("Appuyez sur Échap pour revenir", True, (74, 122, 80))
    screen.blit(esc, (WIDTH // 2 - esc.get_width() // 2, rect_y + rect_h + 20))