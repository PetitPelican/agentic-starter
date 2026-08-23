# claude-accounts — intégration shell (zsh)
#
# À sourcer depuis ~/.zshrc :
#     source ~/.local/share/claude-accounts/accounts.zsh
#
# Définit, d'après ~/.config/claude-accounts/accounts.json :
#   <compte>   lance Claude Code sur ce compte, quel que soit le défaut
#   cacc       la commande complète (status, sessions, switch, auto, link…)
#   cwho       raccourci vers `cacc status`
#   tls        raccourci vers `cacc sessions`
#   pilote     rejoint (ou crée) une session tmux servant de poste de commande
#
# Et positionne CLAUDE_CONFIG_DIR pour que `claude` tout court utilise le compte
# courant. C'est une variable d'ENVIRONNEMENT : elle ne s'applique donc qu'aux
# processus lancés ensuite. Un agent déjà en cours garde son compte — c'est
# précisément ce qui protège les agents d'un changement sous leurs pieds.

_CLAUDE_ACCOUNTS_BIN="${CLAUDE_ACCOUNTS_BIN:-$HOME/.local/bin/claude-accounts}"

_claude_accounts_init() {
  [[ -x $_CLAUDE_ACCOUNTS_BIN ]] || return 0
  /usr/bin/python3 - <<'PY'
import json, os, pathlib, re, sys

home = pathlib.Path.home()
cfg = pathlib.Path(os.environ.get("CLAUDE_ACCOUNTS_CONFIG",
                                  home / ".config" / "claude-accounts" / "accounts.json"))
etat = home / ".config" / "claude-accounts" / "state.json"


def lire(p):
    try:
        return json.loads(pathlib.Path(p).read_text())
    except Exception:
        return {}


comptes = (lire(cfg).get("accounts") or {})
if not comptes:
    sys.exit(0)

# Un nom de compte devient un nom de fonction shell : on refuse tout ce qui
# n'est pas un identifiant simple, plutôt que de laisser injecter du code.
valides = {n: v for n, v in comptes.items() if re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", n)}
defaut_profil = next((n for n, v in valides.items() if v.get("profile") == "default"), None)
actif = lire(etat).get("default")
if actif not in valides:
    actif = defaut_profil

sortie = []
for nom, v in valides.items():
    profil = v.get("profile", "default")
    if profil == "default":
        # Le profil par défaut range son .claude.json dans $HOME, à côté du
        # dossier : pointer CLAUDE_CONFIG_DIR dessus créerait une config vierge.
        lancement = "env -u CLAUDE_CONFIG_DIR command claude"
    else:
        chemin = str(pathlib.Path(profil).expanduser())
        lancement = f'CLAUDE_CONFIG_DIR="{chemin}" command claude'
    sortie.append(
        f'{nom}() {{ [[ -n "${{TMUX:-}}" ]] && tmux select-pane -T "claude:{nom}" 2>/dev/null; '
        f'{lancement} "$@" }}')

if actif and valides.get(actif, {}).get("profile", "default") != "default":
    chemin = str(pathlib.Path(valides[actif]["profile"]).expanduser())
    sortie.append(f'export CLAUDE_CONFIG_DIR="{chemin}"')
else:
    sortie.append("unset CLAUDE_CONFIG_DIR")

print("\n".join(sortie))
PY
}

eval "$(_claude_accounts_init)"

cacc()   { command "$_CLAUDE_ACCOUNTS_BIN" "$@" }
cwho()   { cacc status "$@" }
tls()    { cacc sessions "$@" }

# Poste de commande : une session tmux SANS agent. Y lancer `cacc switch` évite
# que la commande redémarre le panneau qui l'exécute.
pilote() {
  tmux attach -t pilote 2>/dev/null || tmux new -s pilote -c "$HOME"
}
