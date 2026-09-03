#!/usr/bin/env python3
"""mind-guard (relais) - pour un sous-périmètre d'un dépôt multi-agents.

Un dépôt comme AMARENCO porte un agent par périmètre, chacun avec son
`.claude/hooks/`. Plutôt que dupliquer la logique — quatre variantes du même
fichier ont déjà divergé dans la nature — chaque périmètre relaie vers le hook
unique de la racine.

CE QUI CHANGE PAR RAPPORT AU RELAIS PRÉCÉDENT : il remontait à la racine par
`Path(__file__).parents[4]`, c'est-à-dire en comptant les dossiers. Ça marche
tant que personne ne déplace ni ne renivelle rien — et ça casse **en silence**
à la première réorganisation, parce qu'un chemin faux mène à un fichier absent,
donc à un fail-open, donc à un hook qui ne garde plus rien sans le dire.

Ici la racine est demandée à git, qui la connaît quelle que soit la profondeur.
"""
import os, pathlib, runpy, subprocess, sys

ICI = pathlib.Path(__file__).resolve()


def racine():
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                           cwd=ICI.parent, capture_output=True, text=True, timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            return pathlib.Path(r.stdout.strip())
    except Exception:
        pass
    # Repli sans git : on remonte jusqu'au dossier qui porte un .git
    for p in ICI.parents:
        if (p / ".git").exists():
            return p
    return None


def main():
    r = racine()
    if r is None:
        sys.exit(0)  # fail-open, comme le hook lui-même
    cible = r / ".claude" / "hooks" / "mind-guard.py"
    if cible.resolve() == ICI.resolve() or not cible.is_file():
        sys.exit(0)
    runpy.run_path(str(cible), run_name="__main__")


if __name__ == "__main__":
    main()
