"""Eco-Switch (version pygame)

Jeu 2D éducatif inspiré d'Angry Birds :
- Trajectoire de projectile (angle, vitesse, temps, masse)
- Sensibilisation environnementale (éteindre les lampes inutilisées)
- Eco-conception (FPS limité, objets actifs limités, calculs simples)
"""

from __future__ import annotations

import json
import math
import struct
import wave
from pathlib import Path

import pygame


# ==============================
# 1) CHARGEMENT / CONFIGURATION
# ==============================

def read_text_file(path: Path) -> str:
    with path.open("r", encoding="utf-8") as file:
        return file.read()


def parse_json(content: str) -> dict:
    return json.loads(content)


def load_settings(path: Path) -> dict:
    return parse_json(read_text_file(path))


# =========================
# 2) OUTILS MATH / PHYSIQUE
# =========================

def deg_to_rad(value_deg: float) -> float:
    return value_deg * math.pi / 180.0


def make_velocity_components(speed: float, angle_deg: float) -> tuple[float, float]:
    angle_rad = deg_to_rad(angle_deg)
    vx = speed * math.cos(angle_rad)
    vy = -speed * math.sin(angle_rad)
    return vx, vy


def make_projectile(origin_x: float, origin_y: float, speed: float, angle_deg: float, mass: float) -> dict:
    vx, vy = make_velocity_components(speed, angle_deg)
    return {
        "x": origin_x,
        "y": origin_y,
        "vx": vx,
        "vy": vy,
        "mass": mass,
        "alive": True,
    }


def update_projectile(projectile: dict, dt: float, gravity: float) -> None:
    projectile["vy"] = projectile["vy"] + gravity * dt
    projectile["x"] = projectile["x"] + projectile["vx"] * dt * 10
    projectile["y"] = projectile["y"] + projectile["vy"] * dt * 10


def out_of_bounds(projectile: dict, width: int, height: int) -> bool:
    return projectile["x"] < -30 or projectile["x"] > width + 30 or projectile["y"] > height + 30


def squared_distance(ax: float, ay: float, bx: float, by: float) -> float:
    dx = ax - bx
    dy = ay - by
    return dx * dx + dy * dy


def has_collision_circle(ax: float, ay: float, ar: float, bx: float, by: float, br: float) -> bool:
    return squared_distance(ax, ay, bx, by) <= (ar + br) * (ar + br)


# ==============================
# 2-bis) OUTILS AUDIO (SFX)
# ==============================

def make_sine_sample(frequency_hz: float, t: float, volume: float) -> int:
    value = math.sin(2.0 * math.pi * frequency_hz * t)
    return int(32767 * volume * value)


def make_square_sample(frequency_hz: float, t: float, volume: float) -> int:
    cycle_value = math.sin(2.0 * math.pi * frequency_hz * t)
    if cycle_value >= 0:
        return int(32767 * volume)
    return int(-32767 * volume)


def build_wave_samples(frequency_hz: float, duration_s: float, volume: float, sample_rate: int, wave_kind: str) -> bytes:
    sample_count = int(duration_s * sample_rate)
    raw = bytearray()
    index = 0
    while index < sample_count:
        t = index / sample_rate
        if wave_kind == "square":
            sample = make_square_sample(frequency_hz, t, volume)
        else:
            sample = make_sine_sample(frequency_hz, t, volume)
        raw.extend(struct.pack("<h", sample))
        index = index + 1
    return bytes(raw)


def create_wav_file(path: Path, frequency_hz: float, duration_s: float, volume: float, wave_kind: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 22050
    data = build_wave_samples(frequency_hz, duration_s, volume, sample_rate, wave_kind)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(data)


def ensure_sfx_files(base_dir: Path) -> dict:
    sfx_dir = base_dir / "data" / "sfx"
    sfx_shoot = sfx_dir / "shoot.wav"
    sfx_switch = sfx_dir / "switch.wav"
    sfx_win = sfx_dir / "win.wav"

    if not sfx_shoot.exists():
        create_wav_file(sfx_shoot, 520.0, 0.12, 0.45, "square")
    if not sfx_switch.exists():
        create_wav_file(sfx_switch, 830.0, 0.11, 0.40, "sine")
    if not sfx_win.exists():
        create_wav_file(sfx_win, 660.0, 0.28, 0.42, "sine")

    return {
        "shoot": sfx_shoot,
        "switch": sfx_switch,
        "win": sfx_win,
    }


def load_sounds(base_dir: Path) -> dict:
    sounds = {"enabled": False, "shoot": None, "switch": None, "win": None}
    try:
        pygame.mixer.init()
        sfx_paths = ensure_sfx_files(base_dir)
        sounds["shoot"] = pygame.mixer.Sound(str(sfx_paths["shoot"]))
        sounds["switch"] = pygame.mixer.Sound(str(sfx_paths["switch"]))
        sounds["win"] = pygame.mixer.Sound(str(sfx_paths["win"]))
        sounds["enabled"] = True
    except pygame.error:
        sounds["enabled"] = False
    return sounds


def play_sound(sounds: dict, key: str, muted: bool) -> None:
    if muted:
        return
    if not sounds.get("enabled", False):
        return
    sound_obj = sounds.get(key)
    if sound_obj is not None:
        sound_obj.play()


# =====================
# 3) ETAT ET GAMEPLAY
# =====================

def make_lamps(lamps_conf: list[dict]) -> list[dict]:
    lamps = []
    for lamp_conf in lamps_conf:
        lamps.append(
            {
                "x": lamp_conf["x"],
                "y": lamp_conf["y"],
                "radius": lamp_conf["radius"],
                "is_on": lamp_conf["is_on"],
                "waste_watts": lamp_conf["waste_watts"],
                "kind": lamp_conf["kind"],
            }
        )
    return lamps


def make_game_state(config: dict) -> dict:
    player_conf = config["player"]
    window_conf = config["window"]
    sim_conf = config["simulation"]

    level_index = 0
    levels = config["levels"]

    return {
        "window_width": window_conf["width"],
        "window_height": window_conf["height"],
        "window_title": window_conf["title"],
        "fps_limit": sim_conf["fps_limit"],
        "time_step": sim_conf["time_step"],
        "gravity": sim_conf["gravity"],
        "projectile_radius": sim_conf["projectile_radius"],
        "projectile_mass": sim_conf["projectile_mass"],
        "max_projectiles": sim_conf["max_projectiles"],
        "max_shots_per_level": sim_conf.get("max_shots_per_level", 10),
        "player_x": player_conf["x"],
        "player_y": player_conf["y"],
        "power": 24.0,
        "angle": 42.0,
        "power_min": player_conf["power_min"],
        "power_max": player_conf["power_max"],
        "angle_min": player_conf["angle_min"],
        "angle_max": player_conf["angle_max"],
        "levels": levels,
        "level_index": level_index,
        "lamps": make_lamps(levels[level_index]["lamps"]),
        "projectiles": [],
        "energy_saved_wh": 0.0,
        "score": 0,
        "shots": 0,
        "shots_in_level": 0,
        "feedback": "Niveau 1 : eteins les lampes INUTILISEES.",
        "state": "playing",
        "running": True,
        "muted": False,
    }


def clamp(value: float, low: float, high: float) -> float:
    if value < low:
        return low
    if value > high:
        return high
    return value


def all_unused_lamps_off(game: dict) -> bool:
    for lamp in game["lamps"]:
        if lamp["kind"] == "unused" and lamp["is_on"]:
            return False
    return True


def remaining_shots(game: dict) -> int:
    return game["max_shots_per_level"] - game["shots_in_level"]


def spawn_projectile(game: dict, sounds: dict) -> None:
    if game["state"] != "playing":
        return

    if remaining_shots(game) <= 0:
        fail_level(game, "tu n'as plus de lancers")
        return

    if len(game["projectiles"]) >= game["max_projectiles"]:
        game["feedback"] = "Trop d'objets en vol : attends un peu."
        return

    projectile = make_projectile(
        game["player_x"] + 20,
        game["player_y"] - 30,
        game["power"],
        game["angle"],
        game["projectile_mass"],
    )
    game["projectiles"].append(projectile)
    game["shots"] = game["shots"] + 1
    game["shots_in_level"] = game["shots_in_level"] + 1
    game["feedback"] = "Lancer effectue !"
    play_sound(sounds, "shoot", game["muted"])


def fail_level(game: dict, reason: str) -> None:
    game["state"] = "game_over"
    game["projectiles"] = []
    game["feedback"] = f"Perdu : {reason} (R pour recommencer le niveau)"


def prepare_next_level(game: dict, sounds: dict) -> None:
    current_level = game["level_index"] + 1
    next_index = game["level_index"] + 1
    total_levels = len(game["levels"])

    play_sound(sounds, "win", game["muted"])

    if next_index >= total_levels:
        game["state"] = "victory"
        game["projectiles"] = []
        game["feedback"] = f"Bravo ! Tu as termine les {total_levels} niveaux ! (R pour rejouer)"
        return

    next_level = next_index + 1
    game["state"] = "level_transition"
    game["projectiles"] = []
    game["feedback"] = f"Bravo pour le niveau {current_level} ! Prochain: niveau {next_level} (Entree)"


def load_level(game: dict, level_index: int) -> None:
    game["level_index"] = level_index
    game["lamps"] = make_lamps(game["levels"][level_index]["lamps"])
    game["projectiles"] = []
    game["shots_in_level"] = 0
    game["state"] = "playing"
    game["feedback"] = f"Niveau {level_index + 1} : cible les lampes INUTILISEES."


def go_to_next_level(game: dict) -> None:
    if game["state"] != "level_transition":
        return
    load_level(game, game["level_index"] + 1)


def restart_level(game: dict) -> None:
    load_level(game, game["level_index"])


def restart_full_game(game: dict) -> None:
    game["score"] = 0
    game["shots"] = 0
    game["energy_saved_wh"] = 0.0
    load_level(game, 0)


def apply_projectile_lamp_interactions(game: dict, sounds: dict) -> None:
    projectile_radius = game["projectile_radius"]

    for projectile in game["projectiles"]:
        if not projectile["alive"]:
            continue

        for lamp in game["lamps"]:
            if not lamp["is_on"]:
                continue

            hit = has_collision_circle(
                projectile["x"],
                projectile["y"],
                projectile_radius,
                lamp["x"],
                lamp["y"],
                lamp["radius"],
            )
            if not hit:
                continue

            projectile["alive"] = False

            if lamp["kind"] == "used":
                fail_level(game, "tu as touche une lampe UTILISEE")
                return

            lamp["is_on"] = False
            game["score"] = game["score"] + 100
            game["energy_saved_wh"] = game["energy_saved_wh"] + lamp["waste_watts"] / 60.0
            game["feedback"] = f"Bien joue ! {lamp['waste_watts']}W economises."
            play_sound(sounds, "switch", game["muted"])
            break


def cleanup_projectiles(game: dict) -> None:
    living = []
    for projectile in game["projectiles"]:
        if projectile["alive"]:
            living.append(projectile)
    game["projectiles"] = living


def check_shot_limit_loss(game: dict) -> None:
    if game["state"] != "playing":
        return
    if remaining_shots(game) > 0:
        return
    if len(game["projectiles"]) > 0:
        return
    if all_unused_lamps_off(game):
        return
    fail_level(game, "plus de lancers restants")


def simulate_step(game: dict, sounds: dict) -> None:
    if game["state"] != "playing":
        return

    for projectile in game["projectiles"]:
        if projectile["alive"]:
            update_projectile(projectile, game["time_step"], game["gravity"])
            if out_of_bounds(projectile, game["window_width"], game["window_height"]):
                projectile["alive"] = False

    apply_projectile_lamp_interactions(game, sounds)
    cleanup_projectiles(game)
    check_shot_limit_loss(game)

    if game["state"] == "playing" and all_unused_lamps_off(game):
        prepare_next_level(game, sounds)


# ========================
# 4) RENDU GRAPHIQUE 2D
# ========================

def make_color(red: int, green: int, blue: int) -> tuple[int, int, int]:
    return red, green, blue


def draw_background(screen, game: dict) -> None:
    width = game["window_width"]
    height = game["window_height"]
    pygame.draw.rect(screen, make_color(223, 246, 255), (0, 0, width, height))
    pygame.draw.rect(screen, make_color(183, 228, 165), (0, height - 100, width, 100))


def draw_player(screen, game: dict) -> None:
    x = int(game["player_x"])
    y = int(game["player_y"])
    pygame.draw.circle(screen, make_color(255, 183, 3), (x, y - 25), 25)

    aim_len = 45
    angle_rad = deg_to_rad(game["angle"])
    end_x = int(x + aim_len * math.cos(angle_rad))
    end_y = int((y - 25) - aim_len * math.sin(angle_rad))
    pygame.draw.line(screen, make_color(42, 157, 143), (x, y - 25), (end_x, end_y), 4)


def lamp_color(lamp: dict) -> tuple[int, int, int]:
    if lamp["kind"] == "used":
        return make_color(239, 71, 111) if lamp["is_on"] else make_color(180, 180, 180)
    return make_color(255, 224, 102) if lamp["is_on"] else make_color(141, 153, 174)


def lamp_label(lamp: dict) -> str:
    if lamp["kind"] == "used":
        return "UTIL"
    if lamp["is_on"]:
        return "CIBLE"
    return "OFF"


def draw_lamps(screen, game: dict, font) -> None:
    for lamp in game["lamps"]:
        x = int(lamp["x"])
        y = int(lamp["y"])
        radius = int(lamp["radius"])

        pygame.draw.circle(screen, lamp_color(lamp), (x, y), radius)
        pygame.draw.circle(screen, make_color(51, 51, 51), (x, y), radius, 2)
        text_surface = font.render(lamp_label(lamp), True, make_color(20, 20, 20))
        screen.blit(text_surface, (x - 20, y - 8))


def draw_projectiles(screen, game: dict) -> None:
    radius = game["projectile_radius"]
    for projectile in game["projectiles"]:
        pygame.draw.circle(
            screen,
            make_color(131, 56, 236),
            (int(projectile["x"]), int(projectile["y"])),
            radius,
        )


def make_hud_text(game: dict) -> list[str]:
    level_number = game["level_index"] + 1
    total_levels = len(game["levels"])
    line1 = f"Niveau: {level_number}/{total_levels} | Score: {game['score']} | Lancers: {game['shots']}"
    line2 = (
        f"Angle: {game['angle']:.1f} deg | Puissance: {game['power']:.1f} | "
        f"Objets: {len(game['projectiles'])}/{game['max_projectiles']} | Energie: {game['energy_saved_wh']:.2f} Wh"
    )
    line3 = f"Feedback: {game['feedback']}"
    return [line1, line2, line3]


def draw_remaining_shots(screen, game: dict, large_font) -> None:
    count = remaining_shots(game)
    text = f"Lancers restants: {count}"
    color = make_color(200, 30, 30) if count <= 3 else make_color(10, 90, 10)
    text_surface = large_font.render(text, True, color)
    x = game["window_width"] - text_surface.get_width() - 20
    screen.blit(text_surface, (x, 16))


def mute_button_rect(game: dict) -> pygame.Rect:
    return pygame.Rect(game["window_width"] - 180, 58, 160, 42)


def draw_mute_button(screen, game: dict, font) -> None:
    rect = mute_button_rect(game)
    if game["muted"]:
        bg = make_color(120, 120, 120)
        text = "SON: OFF"
    else:
        bg = make_color(70, 180, 90)
        text = "SON: ON"

    pygame.draw.rect(screen, bg, rect, border_radius=8)
    pygame.draw.rect(screen, make_color(20, 20, 20), rect, 2, border_radius=8)
    text_surface = font.render(text, True, make_color(255, 255, 255))
    tx = rect.x + (rect.width - text_surface.get_width()) // 2
    ty = rect.y + (rect.height - text_surface.get_height()) // 2
    screen.blit(text_surface, (tx, ty))


def draw_hud(screen, game: dict, font, large_font) -> None:
    lines = make_hud_text(game)
    y = 10
    for line in lines:
        text_surface = font.render(line, True, make_color(29, 53, 87))
        screen.blit(text_surface, (10, y))
        y = y + 22
    draw_remaining_shots(screen, game, large_font)
    draw_mute_button(screen, game, font)


def center_text_position(screen_width: int, screen_height: int, text_width: int, text_height: int) -> tuple[int, int]:
    x = (screen_width - text_width) // 2
    y = (screen_height - text_height) // 2
    return x, y


def draw_center_message(screen, game: dict, huge_font, font) -> None:
    if game["state"] == "playing":
        return

    overlay = pygame.Surface((game["window_width"], game["window_height"]))
    overlay.set_alpha(170)
    overlay.fill(make_color(10, 20, 40))
    screen.blit(overlay, (0, 0))

    title = ""
    subtitle = game["feedback"]

    if game["state"] == "level_transition":
        title = "NIVEAU TERMINE !"
    elif game["state"] == "game_over":
        title = "PERDU"
    elif game["state"] == "victory":
        title = "VICTOIRE FINALE"

    title_surface = huge_font.render(title, True, make_color(255, 255, 255))
    subtitle_surface = font.render(subtitle, True, make_color(255, 240, 200))

    tx, ty = center_text_position(
        game["window_width"],
        game["window_height"],
        title_surface.get_width(),
        title_surface.get_height(),
    )
    sx, sy = center_text_position(
        game["window_width"],
        game["window_height"],
        subtitle_surface.get_width(),
        subtitle_surface.get_height(),
    )

    screen.blit(title_surface, (tx, ty - 35))
    screen.blit(subtitle_surface, (sx, sy + 30))


def render_frame(screen, game: dict, font, large_font, huge_font) -> None:
    draw_background(screen, game)
    draw_player(screen, game)
    draw_lamps(screen, game, font)
    draw_projectiles(screen, game)
    draw_hud(screen, game, font, large_font)
    draw_center_message(screen, game, huge_font, font)
    pygame.display.flip()


# ==========================
# 5) CONTROLES / GAME LOOP
# ==========================

def toggle_mute(game: dict) -> None:
    game["muted"] = not game["muted"]
    if game["muted"]:
        game["feedback"] = "Son coupe (mute actif)."
    else:
        game["feedback"] = "Son active."


def apply_keydown_action(key: int, game: dict, sounds: dict) -> None:
    if key == pygame.K_UP:
        game["angle"] = clamp(game["angle"] + 2.0, game["angle_min"], game["angle_max"])
    elif key == pygame.K_DOWN:
        game["angle"] = clamp(game["angle"] - 2.0, game["angle_min"], game["angle_max"])
    elif key == pygame.K_RIGHT:
        game["power"] = clamp(game["power"] + 1.0, game["power_min"], game["power_max"])
    elif key == pygame.K_LEFT:
        game["power"] = clamp(game["power"] - 1.0, game["power_min"], game["power_max"])
    elif key == pygame.K_SPACE:
        spawn_projectile(game, sounds)
    elif key == pygame.K_RETURN:
        go_to_next_level(game)
    elif key == pygame.K_m:
        toggle_mute(game)
    elif key == pygame.K_r:
        if game["state"] == "victory":
            restart_full_game(game)
        else:
            restart_level(game)
    elif key == pygame.K_ESCAPE:
        # Retour au menu principal
        game["running"] = False


def handle_mouse_click(game: dict, pos: tuple[int, int]) -> None:
    if mute_button_rect(game).collidepoint(pos):
        toggle_mute(game)


def process_events(game: dict, sounds: dict) -> None:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game["running"] = False
        elif event.type == pygame.KEYDOWN:
            apply_keydown_action(event.key, game, sounds)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            handle_mouse_click(game, event.pos)


def run_game_loop(screen, game: dict, font, large_font, huge_font, sounds: dict) -> None:
    clock = pygame.time.Clock()

    while game["running"]:
        process_events(game, sounds)
        simulate_step(game, sounds)
        render_frame(screen, game, font, large_font, huge_font)

        used_ms = clock.tick(game["fps_limit"])
        budget_ms = 1000.0 / game["fps_limit"]
        if used_ms > budget_ms and game["state"] == "playing":
            game["feedback"] = "Calcul lourd: optimise le code pour eco-concevoir."


# ===================
# 6) FONCTION PUBLIQUE : appelée depuis menu.py
# ===================

def run_game(screen) -> None:
    """Lance une partie complète depuis l'écran pygame existant et revient quand le joueur appuie sur ECHAP."""
    base_dir = Path(__file__).resolve().parents[0]
    config = load_settings(base_dir / "data" / "settings.json")

    # Redimensionner la fenêtre aux dimensions définies dans settings.json
    width = config["window"]["width"]
    height = config["window"]["height"]
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption(config["window"]["title"])

    font = pygame.font.SysFont("arial", 20)
    large_font = pygame.font.SysFont("arial", 34, bold=True)
    huge_font = pygame.font.SysFont("arial", 58, bold=True)

    game = make_game_state(config)
    sounds = load_sounds(base_dir)

    run_game_loop(screen, game, font, large_font, huge_font, sounds)

    # Remettre la fenêtre aux dimensions du menu (800x600) avant de revenir
    pygame.display.set_mode((800, 600))
    pygame.display.set_caption("La Maison Verte")