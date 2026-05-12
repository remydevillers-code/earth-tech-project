"""
Eco-Switch — La Maison Verte
Jeu éducatif 2D : éteins les lampes inutilisées pour sauver la planète !
"""

from __future__ import annotations
import json
import math
import struct
import wave
import random
from pathlib import Path
import pygame


# ─────────────────────────────────────────────
# COULEURS
# ─────────────────────────────────────────────
SKY_TOP    = (180, 220, 255)
SKY_BOT    = (223, 246, 255)
GROUND_TOP = (120, 190,  80)
GROUND_BOT = ( 80, 140,  50)
WHITE      = (255, 255, 255)
GREEN_DARK = ( 26, 107,  46)
GREEN_MID  = ( 76, 175,  80)
GREEN_LITE = (165, 245, 112)
GREEN_TEXT = (200, 240, 176)
RED        = (220,  50,  50)
AIM_COLOR  = ( 42, 157, 143)


# ─────────────────────────────────────────────
# 1) CONFIG
# ─────────────────────────────────────────────

def load_settings(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.loads(f.read())


# ─────────────────────────────────────────────
# 2) PHYSIQUE
# ─────────────────────────────────────────────

def deg_to_rad(d: float) -> float:
    return d * math.pi / 180.0

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def make_projectile(ox, oy, speed, angle_deg, mass):
    rad = deg_to_rad(angle_deg)
    return {"x": ox, "y": oy,
            "vx": speed * math.cos(rad),
            "vy": -speed * math.sin(rad),
            "mass": mass, "alive": True}

def update_projectile(p, dt, gravity):
    p["vy"] += gravity * dt
    p["x"]  += p["vx"] * dt * 10
    p["y"]  += p["vy"] * dt * 10

def out_of_bounds(p, w, h):
    return p["x"] < -50 or p["x"] > w + 50 or p["y"] > h + 50

def circle_hit(ax, ay, ar, bx, by, br):
    dx, dy = ax - bx, ay - by
    return dx*dx + dy*dy <= (ar + br) ** 2

def predict_trajectory(ox, oy, vx, vy, gravity, dt, steps, w, h):
    pts = []
    x, y = ox, oy
    for _ in range(steps):
        vy += gravity * dt
        x  += vx * dt * 10
        y  += vy * dt * 10
        if x < -50 or x > w + 50 or y > h + 50:
            break
        pts.append((int(x), int(y)))
    return pts


# ─────────────────────────────────────────────
# 3) AUDIO
# ─────────────────────────────────────────────

def _sine(hz, t, vol):   return int(32767 * vol * math.sin(2 * math.pi * hz * t))
def _square(hz, t, vol): return int(32767*vol) if math.sin(2*math.pi*hz*t) >= 0 else int(-32767*vol)

def _build_wav(hz, dur, vol, rate, kind):
    raw = bytearray()
    for i in range(int(dur * rate)):
        t = i / rate
        s = _square(hz, t, vol) if kind == "square" else _sine(hz, t, vol)
        raw.extend(struct.pack("<h", s))
    return bytes(raw)

def _save_wav(path, hz, dur, vol, kind):
    path.parent.mkdir(parents=True, exist_ok=True)
    rate = 22050
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2)
        wf.setframerate(rate); wf.writeframes(_build_wav(hz, dur, vol, rate, kind))

def load_sounds(base_dir):
    snd = {"enabled": False, "shoot": None, "switch": None, "win": None, "fail": None}
    try:
        pygame.mixer.init()
        sfx = base_dir / "data" / "sfx"
        for fname, hz, dur, vol, kind in [
            ("shoot.wav",  520, 0.12, 0.45, "square"),
            ("switch.wav", 830, 0.11, 0.40, "sine"),
            ("win.wav",    660, 0.28, 0.42, "sine"),
            ("fail.wav",   220, 0.25, 0.40, "square"),
        ]:
            p = sfx / fname
            if not p.exists(): _save_wav(p, hz, dur, vol, kind)
            snd[fname.replace(".wav","")] = pygame.mixer.Sound(str(p))
        snd["enabled"] = True
    except Exception:
        pass
    return snd

def play_sound(snd, key, muted):
    if muted or not snd.get("enabled"): return
    s = snd.get(key)
    if s: s.play()


# ─────────────────────────────────────────────
# 4) IMAGES (cache)
# ─────────────────────────────────────────────

def load_all_images(base_dir):
    def _load(name):
        try:   return pygame.image.load(str(base_dir / name)).convert_alpha()
        except Exception as e: print(f"[img] {name}: {e}"); return None
    return {
        "lamp_on":    _load("lamp_on.png"),
        "lamp_off":   _load("lamp_off.png"),
        "player":     _load("player.png"),
        "ball":       _load("ball.png"),
        "background": _load("background.png"),
        "_cache":     {},
    }

def _scaled(imgs, key, size):
    src = imgs.get(key)
    if src is None: return None
    ck = (key, size)
    if ck not in imgs["_cache"]:
        imgs["_cache"][ck] = pygame.transform.smoothscale(src, (size, size))
    return imgs["_cache"][ck]


# ─────────────────────────────────────────────
# 5) PARTICULES
# ─────────────────────────────────────────────

def make_particles(x, y, count=14):
    parts = []
    for _ in range(count):
        a = random.uniform(0, 2 * math.pi)
        sp = random.uniform(1.5, 4.5)
        parts.append({
            "x": x, "y": y,
            "vx": math.cos(a)*sp, "vy": math.sin(a)*sp,
            "life": 1.0, "decay": random.uniform(0.04, 0.09),
            "r": random.randint(4, 10),
            "color": random.choice([(255,220,0),(255,180,0),(255,140,0),(180,255,80)]),
        })
    return parts

def update_particles(parts):
    alive = []
    for p in parts:
        p["x"] += p["vx"]; p["y"] += p["vy"]
        p["vy"] += 0.15;   p["life"] -= p["decay"]
        if p["life"] > 0: alive.append(p)
    return alive

def draw_particles(screen, parts):
    for p in parts:
        alpha = int(p["life"] * 255)
        r, g, b = p["color"]
        surf = pygame.Surface((p["r"]*2, p["r"]*2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (r, g, b, alpha), (p["r"], p["r"]), p["r"])
        screen.blit(surf, (int(p["x"]) - p["r"], int(p["y"]) - p["r"]))


# ─────────────────────────────────────────────
# 6) ÉTAT DU JEU
# ─────────────────────────────────────────────

def make_lamps(conf, sx, sy):
    lamps = []
    for lc in conf:
        lamps.append({
            "x": lc["x"]*sx, "y": lc["y"]*sy,
            "radius": int(lc["radius"]*min(sx,sy)),
            "is_on": False if lc["kind"] == "used" else lc["is_on"],
            "waste_watts": lc["waste_watts"],
            "kind": lc["kind"],
        })
    return lamps

def make_game_state(config, real_w=0, real_h=0):
    pc, wc, sc = config["player"], config["window"], config["simulation"]
    bw, bh = wc["width"], wc["height"]
    if not real_w: real_w = bw
    if not real_h: real_h = bh
    sx, sy = real_w/bw, real_h/bh
    s = min(sx, sy)
    lvls = config["levels"]
    return {
        "window_width":        real_w,
        "window_height":       real_h,
        "scale": s, "scale_x": sx, "scale_y": sy,
        "fps_limit":           60,
        "time_step":           sc["time_step"],
        "gravity":             sc["gravity"],
        "projectile_radius":   max(6, int(sc["projectile_radius"]*s)),
        "projectile_mass":     sc["projectile_mass"],
        "max_projectiles":     sc["max_projectiles"],
        "max_shots_per_level": sc.get("max_shots_per_level", 10),
        "player_x":            pc["x"]*sx,
        "player_y":            pc["y"]*sy,
        "power":               24.0,
        "angle":               42.0,
        "power_min":           pc["power_min"],
        "power_max":           pc["power_max"],
        "angle_min":           pc["angle_min"],
        "angle_max":           pc["angle_max"],
        "levels":              lvls,
        "level_index":         0,
        "lamps":               make_lamps(lvls[0]["lamps"], sx, sy),
        "projectiles":         [],
        "particles":           [],
        "energy_saved_wh":     0.0,
        "score":               0,
        "shots":               0,
        "shots_in_level":      0,
        "feedback":            "Éteins les lampes inutilisées !",
        "state":               "playing",
        "running":             True,
        "muted":               False,
        "transition_timer":    0,
    }


# ─────────────────────────────────────────────
# 7) LOGIQUE
# ─────────────────────────────────────────────

def remaining_shots(game): return game["max_shots_per_level"] - game["shots_in_level"]
def all_unused_off(game):  return all(not l["is_on"] for l in game["lamps"] if l["kind"]=="unused")

def load_level(game, idx):
    sx, sy = game["scale_x"], game["scale_y"]
    game.update({
        "level_index":    idx,
        "lamps":          make_lamps(game["levels"][idx]["lamps"], sx, sy),
        "projectiles":    [],
        "particles":      [],
        "shots_in_level": 0,
        "state":          "playing",
        "feedback":       f"Niveau {idx+1}/{len(game['levels'])} — Éteins les lampes inutilisées !",
    })

def spawn_projectile(game, sounds):
    if game["state"] != "playing": return
    if remaining_shots(game) <= 0:
        _fail(game, "Plus de lancers disponibles !")
        return
    if len(game["projectiles"]) >= game["max_projectiles"]:
        game["feedback"] = "Attends qu'un projectile disparaisse."; return
    ox = game["player_x"] + int(20 * game["scale_x"])
    oy = game["player_y"] - int(30 * game["scale_y"])
    game["projectiles"].append(make_projectile(ox, oy, game["power"], game["angle"], game["projectile_mass"]))
    game["shots"]          += 1
    game["shots_in_level"] += 1
    game["feedback"]        = "En vol !"
    play_sound(sounds, "shoot", game["muted"])

def _fail(game, reason):
    game.update({"state": "game_over", "projectiles": [],
                 "feedback": f"{reason}  • appuyez sur le bouton pour reccomencer"})

def _win_level(game, sounds):
    play_sound(sounds, "win", game["muted"])
    nxt   = game["level_index"] + 1
    total = len(game["levels"])
    if nxt >= total:
        game.update({"state": "victory", "projectiles": [],
                     "feedback": f"Bravo ! Tu as terminé les {total} niveaux !"})
    else:
        game.update({"state": "level_transition", "projectiles": [],
                     "transition_timer": 0,
                     "feedback": f"Niveau {game['level_index']+1} terminé !"})

def go_next(game):
    if game["state"] == "level_transition":
        load_level(game, game["level_index"] + 1)

def restart_level(game):
    game["score"] = 0
    game["shots"] = 0
    game["energy_saved_wh"] = 0.0
    load_level(game, game["level_index"])

def restart_game(game):
    game["score"] = game["shots"] = 0
    game["energy_saved_wh"] = 0.0
    load_level(game, 0)

def simulate_step(game, sounds):
    if game["state"] == "level_transition":
        return
    if game["state"] != "playing": return

    w, h, pr = game["window_width"], game["window_height"], game["projectile_radius"]
    for p in game["projectiles"]:
        if not p["alive"]: continue
        update_projectile(p, game["time_step"], game["gravity"])
        if out_of_bounds(p, w, h): p["alive"] = False

    for p in game["projectiles"]:
        if not p["alive"]: continue
        for lamp in game["lamps"]:
            if circle_hit(p["x"], p["y"], pr, lamp["x"], lamp["y"], lamp["radius"]):
                p["alive"] = False
                if lamp["kind"] == "used":
                    _fail(game, "Oups ! Tu as touché une lampe utile.")
                    play_sound(sounds, "fail", game["muted"]); return
                if not lamp["is_on"]:
                    _fail(game, "Cette lampe est déjà éteinte !")
                    play_sound(sounds, "fail", game["muted"]); return
                lamp["is_on"] = False
                game["score"]           += 100
                game["energy_saved_wh"] += lamp["waste_watts"] / 60.0
                game["feedback"]         = f"{lamp['waste_watts']} W économisés !"
                play_sound(sounds, "switch", game["muted"])
                game["particles"] += make_particles(lamp["x"], lamp["y"])
                break

    game["projectiles"] = [p for p in game["projectiles"] if p["alive"]]
    game["particles"]   = update_particles(game["particles"])

    if remaining_shots(game) <= 0 and not game["projectiles"] and not all_unused_off(game):
        _fail(game, "Plus de lancers — des lampes restent allumées !"); return

    if all_unused_off(game): _win_level(game, sounds)


# ─────────────────────────────────────────────
# 8) RENDU
# ─────────────────────────────────────────────

def draw_background(screen, game, imgs):
    w, h = game["window_width"], game["window_height"]
    bg = imgs.get("background")
    if bg is not None:
        ck = ("background", w, h)
        if ck not in imgs["_cache"]:
            imgs["_cache"][ck] = pygame.transform.smoothscale(bg, (w, h))
        screen.blit(imgs["_cache"][ck], (0, 0))
    else:
        # Fallback dégradé
        sy = game["scale_y"]
        for y in range(h):
            t = y / h
            r = int(SKY_TOP[0]+(SKY_BOT[0]-SKY_TOP[0])*t)
            g = int(SKY_TOP[1]+(SKY_BOT[1]-SKY_TOP[1])*t)
            b = int(SKY_TOP[2]+(SKY_BOT[2]-SKY_TOP[2])*t)
            pygame.draw.line(screen, (r,g,b), (0,y), (w,y))
        gh = int(110*sy)
        for y in range(gh):
            t = y/gh
            r = int(GROUND_TOP[0]+(GROUND_BOT[0]-GROUND_TOP[0])*t)
            g = int(GROUND_TOP[1]+(GROUND_BOT[1]-GROUND_TOP[1])*t)
            b = int(GROUND_TOP[2]+(GROUND_BOT[2]-GROUND_TOP[2])*t)
            pygame.draw.line(screen, (r,g,b), (0, h-gh+y), (w, h-gh+y))

def draw_trajectory(screen, game):
    if game["state"] != "playing": return
    rad = deg_to_rad(game["angle"])
    ox  = game["player_x"] + int(20*game["scale_x"])
    oy  = game["player_y"] - int(30*game["scale_y"])
    vx  = game["power"] * math.cos(rad)
    vy  = -game["power"] * math.sin(rad)
    pts = predict_trajectory(ox, oy, vx, vy, game["gravity"], game["time_step"],
                              60, game["window_width"], game["window_height"])
    for i, (px, py) in enumerate(pts):
        if i % 3: continue
        alpha = max(30, 200 - i*3)
        r = max(2, 6 - i//8)
        surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*AIM_COLOR, alpha), (r,r), r)
        screen.blit(surf, (px-r, py-r))

def draw_player(screen, game, imgs):
    x, y = int(game["player_x"]), int(game["player_y"])
    s = min(game["scale_x"], game["scale_y"])
    r = int(25*s)
    size = int(r*5)
    img = _scaled(imgs, "player", size)
    if img: screen.blit(img, (x - size//2, y - size))
    else:   pygame.draw.circle(screen, (255,183,3), (x, y-r), r)
    aim = int(55*s)
    rad = deg_to_rad(game["angle"])
    ex, ey = int(x+aim*math.cos(rad)), int((y-r)-aim*math.sin(rad))
    pygame.draw.line(screen, AIM_COLOR, (x, y-r), (ex, ey), max(2, int(3*s)))
    pygame.draw.circle(screen, (255,255,80), (ex, ey), max(3, int(5*s)))

def draw_power_bar(screen, game):
    s  = game["scale"]
    bw = int(160*s); bh = int(16*s)
    x  = int(game["player_x"]) - bw//2
    y  = int(game["player_y"]) + int(10*s)
    ratio = (game["power"]-game["power_min"]) / (game["power_max"]-game["power_min"])
    pygame.draw.rect(screen, (30,30,30), (x, y, bw, bh), border_radius=6)
    fc = (int(50+200*ratio), int(200-150*ratio), 30)
    pygame.draw.rect(screen, fc, (x, y, int(bw*ratio), bh), border_radius=6)
    pygame.draw.rect(screen, (180,180,180), (x, y, bw, bh), width=1, border_radius=6)

def draw_lamps(screen, game, imgs):
    for lamp in game["lamps"]:
        lx, ly = int(lamp["x"]), int(lamp["y"])
        radius = lamp["radius"]
        key  = "lamp_on" if lamp["is_on"] else "lamp_off"
        size = int(radius * 3.0)
        img  = _scaled(imgs, key, size)
        if img:
            screen.blit(img, (lx - size//2, ly - size//2))
        else:
            color = (255,224,102) if lamp["is_on"] else (141,153,174)
            pygame.draw.circle(screen, color, (lx, ly), radius)
        if lamp["is_on"] and lamp["kind"] == "unused":
            halo = pygame.Surface((radius*6, radius*6), pygame.SRCALPHA)
            pygame.draw.circle(halo, (255,220,60,35), (radius*3,radius*3), radius*3)
            screen.blit(halo, (lx-radius*3, ly-radius*3))

def draw_projectiles(screen, game, imgs):
    r = game["projectile_radius"]
    for p in game["projectiles"]:
        px, py = int(p["x"]), int(p["y"])
        size = r*2
        img = _scaled(imgs, "ball", size)
        if img: screen.blit(img, (px-size//2, py-size//2))
        else:   pygame.draw.circle(screen, (131,56,236), (px,py), r)

def _panel(screen, rect, alpha=200):
    surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    surf.fill((10, 20, 40, alpha))
    screen.blit(surf, rect.topleft)
    pygame.draw.rect(screen, GREEN_MID, rect, width=2, border_radius=10)

def _btn(screen, rect, text, font):
    hov = rect.collidepoint(pygame.mouse.get_pos())
    bg  = (46,158,74) if hov else GREEN_DARK
    _panel(screen, rect, alpha=230)
    pygame.draw.rect(screen, bg, rect, border_radius=8)
    pygame.draw.rect(screen, GREEN_LITE if hov else GREEN_MID, rect, width=2, border_radius=8)
    lbl = font.render(text, True, GREEN_LITE if hov else GREEN_TEXT)
    screen.blit(lbl, (rect.centerx-lbl.get_width()//2, rect.centery-lbl.get_height()//2))

def mute_rect(game):
    s = game["scale"]; w,h = int(150*s), int(40*s)
    return pygame.Rect(game["window_width"]-w-int(12*s), int(12*s), w, h)

def back_rect(game):
    s = game["scale"]; w,h = int(130*s), int(40*s)
    return pygame.Rect(int(12*s), game["window_height"]-h-int(12*s), w, h)

def draw_hud(screen, game, font, large_font):
    s, W, H = game["scale"], game["window_width"], game["window_height"]
    pad = int(10*s)

    # Panneau haut gauche
    panel_w, panel_h = int(540*s), int(68*s)
    _panel(screen, pygame.Rect(pad, pad, panel_w, panel_h))
    lvl   = game["level_index"]+1
    total = len(game["levels"])
    l1 = font.render(f"Niveau {lvl}/{total}   •   Score : {game['score']}   •   Énergie : {game['energy_saved_wh']:.2f} Wh", True, GREEN_TEXT)
    l2 = font.render(f"Angle : {game['angle']:.0f}°   •   Puissance : {game['power']:.0f}", True, GREEN_TEXT)
    screen.blit(l1, (pad+8, pad+5))
    screen.blit(l2, (pad+8, pad+8+l1.get_height()))

    # Lancers restants
    shots_left = remaining_shots(game)
    col = RED if shots_left <= 3 else GREEN_LITE
    ts  = large_font.render(f"Lancers : {shots_left}", True, col)
    screen.blit(ts, (W - ts.get_width() - pad*2, pad+4))

    # Feedback
    fb  = font.render(game["feedback"], True, WHITE)
    fbx = W//2 - fb.get_width()//2
    fby = H - int(58*s)
    _panel(screen, pygame.Rect(fbx-12, fby-6, fb.get_width()+24, fb.get_height()+12))
    screen.blit(fb, (fbx, fby))

    _btn(screen, mute_rect(game), "SON" if not game["muted"] else "MUET", font)
    _btn(screen, back_rect(game), "Menu", font)
    draw_power_bar(screen, game)

def overlay_action_rect(game):
    if game["state"] == "playing": return None
    s = game["scale"]
    cx, cy = game["window_width"]//2, game["window_height"]//2 + int(60*s)
    w, h = int(320*s), int(52*s)
    return pygame.Rect(cx-w//2, cy-h//2, w, h)

def draw_overlay(screen, game, huge_font, font):
    state = game["state"]
    if state == "playing": return
    W, H, s = game["window_width"], game["window_height"], game["scale"]

    surf = pygame.Surface((W, H), pygame.SRCALPHA)
    surf.fill((10, 20, 40, 195))
    screen.blit(surf, (0,0))

    TITLES = {
        "level_transition": ("NIVEAU TERMINÉ !", (100,255,120)),
        "game_over":        ("PERDU...",          (255, 80, 80)),
        "victory":          ("VICTOIRE !",         (100,255,180)),
    }
    title, col = TITLES.get(state, ("", WHITE))
    ts = huge_font.render(title, True, col)
    screen.blit(ts, (W//2-ts.get_width()//2, H//2-int(80*s)))

    sub = font.render(game["feedback"], True, (255,240,200))
    screen.blit(sub, (W//2-sub.get_width()//2, H//2-int(20*s)))

    # Bouton action cliquable
    btn_labels = {
        "level_transition": "Niveau suivant",
        "game_over":        "Réessayer",
        "victory":          "Rejouer depuis le début",
    }
    lbl_text = btn_labels.get(state, "")
    if lbl_text:
        rect = overlay_action_rect(game)
        hov  = rect.collidepoint(pygame.mouse.get_pos())
        bg   = (60,170,90) if hov else GREEN_DARK
        pygame.draw.rect(screen, bg, rect, border_radius=10)
        pygame.draw.rect(screen, GREEN_LITE, rect, width=2, border_radius=10)
        lbl = font.render(lbl_text, True, WHITE)
        screen.blit(lbl, (rect.centerx-lbl.get_width()//2, rect.centery-lbl.get_height()//2))

def render_frame(screen, game, imgs, font, large_font, huge_font):
    draw_background(screen, game, imgs)
    draw_trajectory(screen, game)
    draw_player(screen, game, imgs)
    draw_lamps(screen, game, imgs)
    draw_projectiles(screen, game, imgs)
    draw_particles(screen, game["particles"])
    draw_hud(screen, game, font, large_font)
    draw_overlay(screen, game, huge_font, font)
    pygame.display.flip()


# ─────────────────────────────────────────────
# 9) CONTROLES
# ─────────────────────────────────────────────

def handle_key(key, game, sounds):
    if   key == pygame.K_UP:     game["angle"] = clamp(game["angle"]+2.0, game["angle_min"], game["angle_max"])
    elif key == pygame.K_DOWN:   game["angle"] = clamp(game["angle"]-2.0, game["angle_min"], game["angle_max"])
    elif key == pygame.K_RIGHT:  game["power"] = clamp(game["power"]+1.0, game["power_min"], game["power_max"])
    elif key == pygame.K_LEFT:   game["power"] = clamp(game["power"]-1.0, game["power_min"], game["power_max"])
    elif key == pygame.K_SPACE:  spawn_projectile(game, sounds)
    elif key == pygame.K_RETURN: go_next(game)
    elif key == pygame.K_m:
        game["muted"] = not game["muted"]
        game["feedback"] = "Son coupé." if game["muted"] else "Son activé."
    elif key == pygame.K_r:
        restart_game(game) if game["state"] == "victory" else restart_level(game)
    elif key == pygame.K_ESCAPE: game["running"] = False

def handle_click(pos, game, sounds):
    if mute_rect(game).collidepoint(pos):
        game["muted"] = not game["muted"]
    elif back_rect(game).collidepoint(pos):
        game["running"] = False
    else:
        rect = overlay_action_rect(game)
        if rect and rect.collidepoint(pos):
            state = game["state"]
            if   state == "level_transition": go_next(game)
            elif state == "game_over":        restart_level(game)
            elif state == "victory":          restart_game(game)

def process_events(game, sounds):
    for ev in pygame.event.get():
        if   ev.type == pygame.QUIT:                             game["running"] = False
        elif ev.type == pygame.KEYDOWN:                          handle_key(ev.key, game, sounds)
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button==1: handle_click(ev.pos, game, sounds)


# ─────────────────────────────────────────────
# 10) BOUCLE
# ─────────────────────────────────────────────

def run_game_loop(screen, game, imgs, font, large_font, huge_font, sounds):
    clock = pygame.time.Clock()
    while game["running"]:
        process_events(game, sounds)
        simulate_step(game, sounds)
        render_frame(screen, game, imgs, font, large_font, huge_font)
        clock.tick(game["fps_limit"])


# ─────────────────────────────────────────────
# 11) POINT D'ENTRÉE (appelé par menu.py)
# ─────────────────────────────────────────────

def run_game(screen, real_width=0, real_height=0):
    base_dir = Path(__file__).resolve().parent
    config   = load_settings(base_dir / "data" / "settings.json")

    if not real_width or not real_height:
        info = pygame.display.Info()
        real_width, real_height = info.current_w, info.current_h

    screen = pygame.display.set_mode((real_width, real_height), pygame.FULLSCREEN)
    pygame.display.set_caption("Eco-Switch — La Maison Verte")

    s = min(real_width/config["window"]["width"], real_height/config["window"]["height"])
    font       = pygame.font.SysFont("Arial", max(14, int(18*s)))
    large_font = pygame.font.SysFont("Arial", max(20, int(30*s)), bold=True)
    huge_font  = pygame.font.SysFont("Arial", max(32, int(56*s)), bold=True)

    game   = make_game_state(config, real_width, real_height)
    sounds = load_sounds(base_dir)
    imgs   = load_all_images(base_dir)

    run_game_loop(screen, game, imgs, font, large_font, huge_font, sounds)

    pygame.display.set_mode((real_width, real_height), pygame.FULLSCREEN)
    pygame.display.set_caption("La Maison Verte")