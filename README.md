Earth-Tech-Project

Eco-Switch : jeu 2D éducatif (Python + Pygame)

Petit jeu inspiré d'Angry Birds : le joueur lance des projectiles pour éteindre des lampes laissées allumées inutilement.

Objectif pédagogique

Le projet couvre :
- trajectoires 2D (angle, vitesse, gravité, temps, masse),
- rétroactions utilisateur (score, feedback, énergie économisée),
- rendu graphique avec Pygame,
- réflexion d'éco-conception (limite FPS, réduction des objets actifs, calcul simple).


Règles de jeu

- Il y a 10 niveaux au total, avec difficulté croissante jusqu'au dernier niveau (très difficile).
- Entre les niveaux, un message de félicitation est affiché **en grand au centre de l'écran**.
- Deux types de lampes existent :
  - lampe inutilisée (`CIBLE`) : il faut l'éteindre avec la balle,
  - lampe utilisée (`UTIL`) : il ne faut pas la toucher, sinon le niveau est perdu.
- Le joueur a un maximum de 10 lancers par niveau.
- En haut à droite, le jeu affiche en gros le nombre de lancers restants.

Sons et mute

- Bruitage de tir quand la balle est lancée.
- Bruitage d'interrupteur quand une lampe cible est touchée.
- Son joyeux quand un niveau est terminé.
- Bouton SON: ON/OFF en haut à droite pour tout couper.
- Touche clavier `M` pour activer/désactiver le son.

Commandes du jeu

- `↑` / `↓` : régler l'angle du tir
- `←` / `→` : régler la puissance
- `Espace` : lancer un projectile
- `Entrée` : passer au niveau suivant (après message de transition)
- `M` : mute / unmute
- `R` : recommencer le niveau (ou rejouer depuis le début après victoire)
- `Échap` : quitter

Structure

- `src/main.py` : code principal (fonctions classées par catégories)
- `data/settings.json` : paramètres globaux + définition des 10 niveaux
- `data/sfx/*.wav` : bruitages générés automatiquement au premier lancement
