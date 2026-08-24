#!/bin/sh
# Installe claude-accounts pour l'utilisateur courant. Idempotent.
#
#     sh tools/claude-accounts/install.sh
#
# Outillage MACHINE, pas projet : il s'installe une fois par poste, pas une fois
# par dépôt. Rien n'est écrit hors du home de l'utilisateur.
set -eu

ICI=$(cd "$(dirname "$0")" && pwd)
BIN="$HOME/.local/bin"
PART="$HOME/.local/share/claude-accounts"
CONF="$HOME/.config/claude-accounts"
RC="${ZDOTDIR:-$HOME}/.zshrc"
LIGNE="source $PART/accounts.zsh"

mkdir -p "$BIN" "$PART" "$CONF"

cp "$ICI/bin/claude-accounts" "$BIN/claude-accounts"
cp "$ICI/bin/claude-team" "$BIN/claude-team"
cp "$ICI/bin/claude-team.html.in" "$BIN/claude-team.html.in"
chmod +x "$BIN/claude-accounts" "$BIN/claude-team"
cp "$ICI/shell/accounts.zsh" "$PART/accounts.zsh"
echo "installé : $BIN/claude-accounts"
echo "installé : $BIN/claude-team"
echo "installé : $PART/accounts.zsh"

if [ -f "$CONF/accounts.json" ]; then
  echo "conservé : $CONF/accounts.json (déjà présent)"
else
  cp "$ICI/accounts.example.json" "$CONF/accounts.json"
  echo "créé     : $CONF/accounts.json  ← à adapter avec TES noms de comptes"
fi

if [ -f "$RC" ] && grep -qF "$LIGNE" "$RC"; then
  echo "conservé : $RC (déjà branché)"
else
  printf '\n# claude-accounts — plusieurs comptes Claude Code\n%s\n' "$LIGNE" >> "$RC"
  echo "ajouté   : $LIGNE  →  $RC"
fi

cat <<'FIN'

Suite :
  1. adapte ~/.config/claude-accounts/accounts.json (un seul "profile": "default")
  2. source ~/.zshrc
  3. connecte le second compte :   <nom-du-compte>   puis   /login
  4. partage le travail entre profils :   cacc link
  5. vérifie :   cwho
FIN
