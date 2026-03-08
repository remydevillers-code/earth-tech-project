"""Eco-Switch (version pygame)

Jeu 2D éducatif inspiré d'Angry Birds :
- Trajectoire de projectile (angle, vitesse, temps, masse)
- Sensibilisation environnementale (éteindre des lumières inutiles)
- Eco-conception (FPS limité, objets actifs limités, calculs simples)
"""

from __future__ import annotations

import json
import math
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


# =====================
# 3) ETAT ET GAMEPLAY
# =====================

def make_switches(switches_conf: list[dict]) -> list[dict]:
    switches = []
    for switch_conf in switches_conf:
        switches.append(
            {
                "x": switch_conf["x"],
                "y": switch_conf["y"],
                "radius": switch_conf["radius"],
                "is_on": switch_conf["is_on"],
                "waste_watts": switch_conf["waste_watts"],
            }
        )
    return switches


def make_game_state(config: dict) -> dict:
    player_conf = config["player"]
    window_conf = config["window"]
    sim_conf = config["simulation"]

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
        "player_x": player_conf["x"],
        "player_y": player_conf["y"],
        "power": 24.0,
        "angle": 42.0,
        "power_min": player_conf["power_min"],
        "power_max": player_conf["power_max"],
        "angle_min": player_conf["angle_min"],
        "angle_max": player_conf["angle_max"],
        "projectiles": [],
        "switches": make_switches(config["switches"]),
        "energy_saved_wh": 0.0,
        "score": 0,
        "shots": 0,
        "feedback": "Eteins les lumieres inutiles !",
        "running": True,
    }


def clamp(value: float, low: float, high: float) -> float:
    if value < low:
        return low
    if value > high:
        return high
    return value


def all_switches_off(game: dict) -> bool:
    for switch_data in game["switches"]:
        if switch_data["is_on"]:
            return False
    return True


def spawn_projectile(game: dict) -> None:
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
    game["feedback"] = "Lancer effectue !"


def apply_projectile_switch_interactions(game: dict) -> None:
    projectile_radius = game["projectile_radius"]

    for projectile in game["projectiles"]:
        if not projectile["alive"]:
            continue

        for switch_data in game["switches"]:
            if not switch_data["is_on"]:
                continue

            hit = has_collision_circle(
                projectile["x"],
                projectile["y"],
                projectile_radius,
                switch_data["x"],
                switch_data["y"],
                switch_data["radius"],
            )
            if hit:
                switch_data["is_on"] = False
                projectile["alive"] = False
                game["score"] = game["score"] + 100
                game["energy_saved_wh"] = game["energy_saved_wh"] + switch_data["waste_watts"] / 60.0
                game["feedback"] = f"Bravo ! {switch_data['waste_watts']}W inutiles economises."
                break


def cleanup_projectiles(game: dict) -> None:
    living = []
    for projectile in game["projectiles"]:
        if projectile["alive"]:
            living.append(projectile)
    game["projectiles"] = living


def simulate_step(game: dict) -> None:
    for projectile in game["projectiles"]:
        if projectile["alive"]:
            update_projectile(projectile, game["time_step"], game["gravity"])
            if out_of_bounds(projectile, game["window_width"], game["window_height"]):
                projectile["alive"] = False

    apply_projectile_switch_interactions(game)
    cleanup_projectiles(game)

    if all_switches_off(game):
        game["feedback"] = "Mission reussie : toutes les lumieres inutiles sont eteintes !"


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


def draw_switches(screen, game: dict, font) -> None:
    for switch_data in game["switches"]:
        x = int(switch_data["x"])
        y = int(switch_data["y"])
        radius = int(switch_data["radius"])

        if switch_data["is_on"]:
            color = make_color(255, 224, 102)
            label = "ON"
        else:
            color = make_color(141, 153, 174)
            label = "OFF"

        pygame.draw.circle(screen, color, (x, y), radius)
        pygame.draw.circle(screen, make_color(51, 51, 51), (x, y), radius, 2)
        text_surface = font.render(label, True, make_color(20, 20, 20))
        screen.blit(text_surface, (x - 14, y - 8))


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
    line1 = f"Score: {game['score']} | Lancers: {game['shots']} | Energie: {game['energy_saved_wh']:.2f} Wh"
    line2 = (
        f"Angle: {game['angle']:.1f} deg | Puissance: {game['power']:.1f} | "
        f"Objets actifs: {len(game['projectiles'])}/{game['max_projectiles']}"
    )
    line3 = f"Feedback: {game['feedback']}"
    return [line1, line2, line3]


def draw_hud(screen, game: dict, font) -> None:
    lines = make_hud_text(game)
    y = 10
    for line in lines:
        text_surface = font.render(line, True, make_color(29, 53, 87))
        screen.blit(text_surface, (10, y))
        y = y + 22


def render_frame(screen, game: dict, font) -> None:
    draw_background(screen, game)
    draw_player(screen, game)
    draw_switches(screen, game, font)
    draw_projectiles(screen, game)
    draw_hud(screen, game, font)
    pygame.display.flip()


# ==========================
# 5) CONTROLES / GAME LOOP
# ==========================

def restart_game(game: dict) -> None:
    for switch_data in game["switches"]:
        switch_data["is_on"] = True
    game["projectiles"] = []
    game["score"] = 0
    game["shots"] = 0
    game["energy_saved_wh"] = 0.0
    game["feedback"] = "Nouvelle partie !"


def apply_keydown_action(key: int, game: dict) -> None:
    if key == pygame.K_UP:
        game["angle"] = clamp(game["angle"] + 2.0, game["angle_min"], game["angle_max"])
    elif key == pygame.K_DOWN:
        game["angle"] = clamp(game["angle"] - 2.0, game["angle_min"], game["angle_max"])
    elif key == pygame.K_RIGHT:
        game["power"] = clamp(game["power"] + 1.0, game["power_min"], game["power_max"])
    elif key == pygame.K_LEFT:
        game["power"] = clamp(game["power"] - 1.0, game["power_min"], game["power_max"])
    elif key == pygame.K_SPACE:
        spawn_projectile(game)
    elif key == pygame.K_r:
        restart_game(game)
    elif key == pygame.K_ESCAPE:
        game["running"] = False


def process_events(game: dict) -> None:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game["running"] = False
        elif event.type == pygame.KEYDOWN:
            apply_keydown_action(event.key, game)


def run_game_loop(screen, game: dict, font) -> None:
    clock = pygame.time.Clock()

    while game["running"]:
        process_events(game)
        simulate_step(game)
        render_frame(screen, game, font)

        used_ms = clock.tick(game["fps_limit"])
        budget_ms = 1000.0 / game["fps_limit"]
        if used_ms > budget_ms:
            game["feedback"] = "Calcul lourd: optimise le code pour eco-concevoir."


# ===================
# 6) ENTREE PRINCIPALE
# ===================

def setup_pygame(config: dict):
    pygame.init()
    width = config["window"]["width"]
    height = config["window"]["height"]
    title = config["window"]["title"]
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption(title)
    font = pygame.font.SysFont("arial", 20)
    return screen, font


def main() -> None:
    #config_path = Path(__file__).resolve().parents[1] / "data" / "settings.json"
    config_path = Path(__file__).resolve().parents[0] / "data" / "settings.json"

    print(config_path)

    config = load_settings(config_path)
    game = make_game_state(config)
    screen, font = setup_pygame(config)

    run_game_loop(screen, game, font)
    pygame.quit()


if __name__ == "__main__":
    main()