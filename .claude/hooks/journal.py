#!/usr/bin/env python3
"""journal - hook PostToolUse (matcher Bash, sur `git commit`).

Écrit ce qui a été commité dans `.logs/<AAAA-MM-JJ>.md`, un fichier par jour.
Le journal répond à une question que `.mind/state.md` ne sait pas traiter :
**qu'est-ce qui a été fait, jour par jour ?**

La séparation des rôles est nette, et c'est elle qui justifie deux mécanismes :

    .mind/state.md   un INSTANTANÉ borné — le texte périmé s'y remplace
    .logs/<jour>.md  un HISTORIQUE append-only — rien ne s'y réécrit

Un instantané ne peut pas répondre à « qu'a-t-on fait mardi ? », et un
historique ne peut pas répondre à « où en est-on ? ». D'où les deux.

POURQUOI UN HOOK ET PLUS UN SKILL. Ce travail était celui de `/memory-update`,
qu'il fallait penser à lancer. Un journal qu'on tient quand on y pense a des
trous exactement les jours chargés — ceux qu'on aurait le plus besoin de
relire. Écrit par la machine à chaque commit, il n'en a aucun.

COMMENT IL SAIT QU'UN COMMIT A EU LIEU. Il ne lit pas le résultat de la
commande : il regarde `HEAD`. Si le commit a échoué, `HEAD` n'a pas bougé, son
empreinte est déjà dans le journal, et rien n'est écrit. Aucune connaissance de
la forme de `tool_response` n'est nécessaire, et un double appel du hook ne
produit pas deux entrées.

**fail-open, et silencieux** : un journal est un confort, il ne doit jamais
empêcher de travailler. Toute erreur sort en code 0 sans message.
"""
import sys, json, subprocess, re, pathlib

DOSSIER = ".logs"
MAX_FICHIERS = 40  # nombre de fichiers listés dans une entrée, avant « … »


def _git(args):
    r = subprocess.run(["git"] + args, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=15)
    return r.stdout.strip() if r.returncode == 0 else None


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    cmd = ((data.get("tool_input") or {}).get("command") or "")
    if not re.search(r"\bgit\b.+\bcommit\b", cmd):
        sys.exit(0)

    racine = _git(["rev-parse", "--show-toplevel"])
    if not racine:
        sys.exit(0)

    # `%x09` = tabulation : un séparateur qu'un sujet de commit ne contient pas.
    tete = _git(["log", "-1", "--date=short",
                 "--format=%h%x09%ad%x09%cI%x09%s%x09%an"])
    if not tete or tete.count("\t") != 4:
        sys.exit(0)
    court, jour, iso, sujet, auteur = tete.split("\t")

    fichier = pathlib.Path(racine) / DOSSIER / ("%s.md" % jour)
    deja = fichier.read_text(encoding="utf-8") if fichier.is_file() else ""

    # Le garde-fou contre les doublons : l'empreinte du commit. Un commit
    # échoué laisse HEAD en place, donc son empreinte est déjà là.
    if re.search(r"\b%s\b" % re.escape(court), deja):
        sys.exit(0)

    touches = _git(["show", "--name-only", "--format=", "HEAD"]) or ""
    # Le journal ne se journalise pas : l'entrée de la veille est commitée
    # avec le travail du jour, et se retrouverait dans la liste.
    touches = [f for f in touches.splitlines()
               if f.strip() and not f.startswith(DOSSIER + "/")]

    heure = iso[11:16] if len(iso) >= 16 else "??:??"
    branche = _git(["rev-parse", "--abbrev-ref", "HEAD"]) or "?"
    amend = " · réécriture (`--amend`)" if "--amend" in cmd else ""

    bloc = ["", "## %s · `%s` · %s%s" % (heure, court, branche, amend),
            "", "**%s**" % sujet, ""]
    for f in touches[:MAX_FICHIERS]:
        bloc.append("- `%s`" % f)
    if len(touches) > MAX_FICHIERS:
        bloc.append("- … et %d autres fichiers" % (len(touches) - MAX_FICHIERS))
    bloc.append("")
    bloc.append("<!-- %s -->" % auteur)

    try:
        fichier.parent.mkdir(parents=True, exist_ok=True)
        if not deja:
            entete = ("# Journal — %s\n\n"
                      "Écrit par le hook `journal` à chaque commit. "
                      "**Append-only** : on n'y réécrit rien, on n'y compresse "
                      "rien.\n" % jour)
            fichier.write_text(entete + "\n".join(bloc) + "\n", encoding="utf-8")
        else:
            with fichier.open("a", encoding="utf-8") as fh:
                fh.write("\n".join(bloc) + "\n")
    except Exception:
        pass  # un journal ne bloque jamais

    sys.exit(0)


if __name__ == "__main__":
    main()
