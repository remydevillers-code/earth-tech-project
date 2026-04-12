import pygame


def back_button_rect(WIDTH, HEIGHT, scale):
    """Retourne le rect du bouton retour, centré en bas."""
    w = int(180 * scale)
    h = int(52  * scale)
    x = WIDTH // 2 - w // 2
    y = HEIGHT - int(80 * scale)
    return pygame.Rect(x, y, w, h)


def show_credits(screen, WIDTH, HEIGHT, font_big, font_small, font_sub,
                 GREEN_LIGHT, GREEN_MID, GREEN_TEXT, GREEN_SUB):
    """Affiche l'écran des crédits. Retourne True si le bouton retour est cliqué."""

    scale = HEIGHT / 600

    # ── Noms de l'équipe ──
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
    screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, int(60 * scale)))

    # Rectangle fond noms
    rect_w = int(400 * scale)
    rect_h = int(320 * scale)
    rect_x = WIDTH  // 2 - rect_w // 2
    rect_y = int(130 * scale)
    pygame.draw.rect(screen, (15, 40, 20),
                     pygame.Rect(rect_x, rect_y, rect_w, rect_h), border_radius=16)
    pygame.draw.rect(screen, GREEN_MID,
                     pygame.Rect(rect_x, rect_y, rect_w, rect_h), width=3, border_radius=16)

    # Noms
    spacing = int(46 * scale)
    for i, nom in enumerate(noms):
        label = font_small.render(nom, True, GREEN_TEXT)
        screen.blit(label, (WIDTH // 2 - label.get_width() // 2,
                            rect_y + int(30 * scale) + i * spacing))

    # ── Bouton retour ──
    mouse = pygame.mouse.get_pos()
    btn = back_button_rect(WIDTH, HEIGHT, scale)
    hovered = btn.collidepoint(mouse)

    GREEN_BTN   = (26, 107, 46)
    GREEN_HOVER = (46, 158, 74)
    color  = GREEN_HOVER if hovered else GREEN_BTN
    border = GREEN_LIGHT if hovered else GREEN_MID
    pygame.draw.rect(screen, (2, 14, 5), btn.move(4, 4), border_radius=14)
    pygame.draw.rect(screen, color,  btn, border_radius=14)
    pygame.draw.rect(screen, border, btn, width=3, border_radius=14)
    txt_color = GREEN_LIGHT if hovered else GREEN_TEXT
    label = font_small.render("← Retour", True, txt_color)
    screen.blit(label, (btn.centerx - label.get_width() // 2,
                        btn.centery - label.get_height() // 2))

    # Renvoie le rect pour que menu.py puisse tester le clic
    return btn