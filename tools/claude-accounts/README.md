# claude-accounts

> Plusieurs comptes Claude Code sur une machine, sans jamais casser les agents en cours.

Outillage **machine**, pas projet : il s'installe une fois par poste. Il ne
dépend d'aucun autre morceau du starter et ne touche que le home de
l'utilisateur.

Conçu pour un poste qui fait tourner plusieurs agents Claude Code en continu
(sessions tmux, accès SSH, pilotage depuis l'app mobile) et dispose de deux
abonnements ou plus, chacun avec sa limite d'usage.

---

## Installation

```sh
sh tools/claude-accounts/install.sh
source ~/.zshrc
```

Puis adapter `~/.config/claude-accounts/accounts.json` :

```json
{
  "accounts": {
    "perso": { "profile": "default" },
    "pro":   { "profile": "~/.claude-pro" }
  }
}
```

**Un seul compte doit porter `"profile": "default"`** — voir le piège n° 2.

Connecter le second compte, puis partager le travail entre les profils :

```sh
pro            # lance Claude Code sur ce profil
/login         # dans Claude
cacc link      # symlinks des ressources partagées
cwho           # vérification
```

---

## Commandes

| Commande | Rôle |
|---|---|
| `<compte>` | lance Claude Code sur ce compte, quel que soit le défaut |
| `cwho` (`cacc status`) | quotas réels des comptes + agents en cours |
| `cwho --watch` | idem, rafraîchi en continu |
| `tls` (`cacc sessions`) | sessions tmux, **tous sockets**, et leur contenu |
| `cacc switch <compte>` | plan de déplacement des agents — rien n'est touché |
| `cacc switch <compte> --go` | déplace, attend le redémarrage, rétablit les ponts |
| `cacc switch --ponts` | renvoie `/remote-control` aux agents sans pont |
| `cacc auto [--go] [--watch]` | bascule automatique au seuil de quota |
| `cacc default <compte>` | choisit le compte que donne `claude` seul |
| `cacc link` | (re)crée les ressources partagées entre profils |
| `pilote` | rejoint (ou crée) la session tmux servant de poste de commande |

---

## Le principe

`CLAUDE_CONFIG_DIR` est une variable **d'environnement** : donc par processus,
donc par panneau tmux. Chaque compte a son propre `.credentials.json`, et un
panneau ne peut ni voler le compte d'un autre, ni écraser ses jetons.

```
SÉPARÉ (l'identité)              PARTAGÉ (le travail, par symlink)
  .credentials.json                projects/   ← transcripts + mémoire
  .claude.json                     settings.json · settings.local.json
  sessions/                        plugins/ · skills/ · agents/ · history.jsonl
```

Une conversation n'est pas stockée dans le compte : c'est un fichier
`projects/<projet>/<sessionId>.jsonl` sur le disque. Comme `projects/` est
partagé entre les profils, `--resume` retrouve le **même fil** depuis n'importe
quel compte. C'est ce qui rend la bascule indolore.

**On ne « swappe » donc jamais de credentials.** Un compte est fixé au lancement
d'un processus : réécrire le fichier sous des agents vivants les ferait changer
de compte au premier renouvellement de jeton, et un agent qui renouvelle le sien
écraserait les jetons fraîchement installés. `cacc switch` redémarre chaque
agent proprement, avec `--resume` sur son fil exact.

---

## Bascule automatique

`cacc auto` compare la **fenêtre contraignante** de chaque compte — la plus
haute de ses utilisations 5 h et 7 j, lue sur `/api/oauth/usage`. Au-delà du
seuil, il bascule vers le compte qui a le plus de marge. Quatre refus, tous
journalisés dans `~/.config/claude-accounts/auto.log` :

| Refus | Raison |
|---|---|
| candidat au-dessus de `seuil - hysteresis` | pas assez de marge — anti-oscillation |
| usage illisible | on ne saute pas dans le noir |
| bascule récente | `cooldown` |
| **un agent travaille** | il perdrait son tour en cours |

Le dernier est le plus important : `auto` ne coupe **jamais** un agent en plein
travail, il reporte au tour suivant.

En continu :

```sh
tmux new -s pilote 'cacc auto --watch --go; exec zsh'
```

Réglages dans `accounts.json` : `seuil`, `hysteresis`, `cooldown`, `intervalle`.

---

## Les pièges

Tous rencontrés en conditions réelles. Ils expliquent pourquoi le code fait ce
qu'il fait — ne pas les « simplifier ».

### 1. En SSH, les credentials ne sont pas dans le trousseau

Sans session graphique, Claude Code ne peut pas déverrouiller le trousseau macOS
et retombe sur `<profil>/.credentials.json`, en clair. C'est ce qui rend
l'isolation par profil possible — et ce qui déconseille un jeton longue durée
sur une machine joignable à distance.

### 2. Le profil « default » range son `.claude.json` ailleurs

Le profil par défaut le met dans `$HOME/.claude.json`, **à côté** du dossier
`~/.claude`. Un profil nommé le met **dans** son dossier. Donc :

```sh
CLAUDE_CONFIG_DIR=~/.claude claude    # ne redonne PAS le profil par défaut :
                                      # crée une config vierge, 0 dossier de confiance
```

Le compte `default` doit **retirer** la variable (`env -u`), jamais la définir.

### 3. Deux jetons, un seul compte

`expiresAt` (l'access token) ne vit que quelques heures et Claude Code le
renouvelle seul : l'afficher n'apporte que de l'inquiétude. Le chiffre utile est
`refreshTokenExpiresAt`, de l'ordre de 30 jours — c'est lui qui impose un
nouveau `/login` si un profil reste inutilisé.

### 4. `tmux ls` ne montre qu'un socket

Les identifiants de panneau (`%0`, `%1`…) sont propres à **chaque** socket. Le
`%0` d'un socket désigne un tout autre panneau que le `%0` d'un autre — une
première version ciblait le panneau par son `%n` et aurait relancé le mauvais
agent avec la conversation d'un troisième. Le rattachement se fait donc par la
**parenté des process**, jamais par l'identifiant seul.

```sh
for s in $(ls /private/tmp/tmux-$(id -u)); do echo "-- $s"; tmux -L "$s" ls; done
```

### 5. `respawn-pane` repart du dossier de création du panneau

Sans `-c`, un agent relancé démarre là où le panneau a été **créé**, pas là où
il travaillait — il perd le `CLAUDE.md` et le `.claude/settings.json` de son
projet. Le dossier est relu dans `sessions/<pid>.json`.

### 6. Le pont cloud appartient au compte qui fait tourner l'agent

Un agent n'apparaît dans l'app mobile ou sur le web que s'il a un pont Remote
Control **actif**, ouvert sous le compte courant. Changer de compte sous des
agents déjà lancés casse leurs ponts (`organization changed on this machine`) :
ils deviennent invisibles des deux côtés. Les transcripts, eux, ne risquent rien.

Le cloud n'héberge jamais l'historique — seulement un lien vivant vers un
processus. Après une bascule, l'app repart donc d'une conversation vide alors
que l'agent, lui, garde tout son contexte.

**Corollaire pratique :** garder tous les agents sur le même compte. L'app
mobile n'est connectée qu'à un compte à la fois, et ne sait pas en changer sans
déconnexion complète. Un seul compte à la fois = un seul changement dans l'app
par rotation.

### 7. Ne pas lancer la bascule depuis un agent

Relancer le panneau qui exécute la commande la tuerait en pleine action.
`cacc switch` repère son propre panneau par la parenté des process et l'exclut
(`⛔ C'EST TOI`). D'où l'intérêt de `pilote`, une session tmux sans agent.

### 8. Ne pas se fier à `pane_current_command`

Une relance passée par un `zsh -c` enveloppant fait afficher « zsh » à tmux pour
un panneau qui exécute pourtant un agent. La vérité vient des enregistrements
`sessions/<pid>.json`.

---

## Dépannage

| Symptôme | Cause probable | Remède |
|---|---|---|
| `command not found` sur un raccourci | shell ouvert avant l'installation | `source ~/.zshrc` |
| `Not logged in · Please run /login` | profil jamais connecté | `<compte>` puis `/login` |
| limite hebdomadaire atteinte | quota épuisé | `cacc switch <autre> --go` |
| agent absent de l'app mobile | pont mort ou mauvais compte | `cacc switch --ponts` |
| un agent semble disparu | il est sur un autre socket tmux | `tls` |
| usage `429` | budget de sondage dépassé | rien à faire, le cache prend le relais |

Depuis un agent Claude Code, préférer le nom complet `claude-accounts …` : les
raccourcis courts dépendent de l'instantané de shell pris au démarrage de
l'agent, et peuvent manquer.
