#!/usr/bin/env python3
"""mind-guard - hook PreToolUse (matcher Bash, sur `git commit`).

Remplace `memory-guard`, qui gardait `.memory/` et se déclenchait au `git push`.
Deux changements, et chacun corrige une panne réelle :

1. LE DÉCLENCHEUR PASSE DE `push` À `commit`. Le tableau de bord
   (`claude-cadrage`, qui importe `claude-projets`) lit les fichiers `.mind/`
   du **disque local**, jamais le dépôt distant. Garder au push ne protégeait
   donc pas ce qu'on croyait protéger : un projet pouvait rester des semaines
   sans pousser, et le tableau de bord affichait sa dernière déclaration comme
   si elle était fraîche.

2. IL NE SUFFIT PLUS DE « TOUCHER » LA MÉMOIRE. `memory-guard` acceptait
   n'importe quel fichier de `.memory/` : un commit qui ne modifiait que
   `decisions.md` le satisfaisait en laissant `state.md` périmé. Ici on exige
   les deux fichiers que le collecteur lit vraiment — `.mind/state.md` et
   `.mind/todo.md` — et on vérifie qu'ils **parsent encore**.

Le second point est le plus important : un en-tête cassé est PIRE qu'un en-tête
vieux. `claude-projets` signale « aucun en-tête dans .mind/state.md — on ne sait
ni où va le projet ni qui doit bouger », et le projet sort du tableau de bord
sans que personne ne s'en aperçoive. Un fichier illisible est un silence, et un
silence se lit comme une absence de problème.

Contrat repris **du parseur**, pas de mémoire (`claude-projets`, v. 03/09/2026) :
  - en-tête : `---\n…\n---` en tête de `.mind/state.md`, YAML plat
  - champs lus : maj, cap, sante, jalon, balle, depuis, attente, suivant
  - une tâche : `- [ ] Libellé`, avec ` |x|X|>|~` comme états
  - marqueurs optionnels : !haut|!moyen|!bas et @<qui>, dont @dehors réservé

Échappatoire : ` # mind-ok` à la fin de la commande.
**fail-open** : toute erreur, ambiguïté ou dépôt non git laisse passer.
"""
import sys, json, subprocess, re, datetime

# --- à ajuster selon le projet -------------------------------------------------
IGNORED_PREFIXES = (".claude/", ".mind/", ".memory/", ".logs/", "docs/")
CODE_EXT = (
    ".py", ".sql", ".qmd", ".ipynb", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".go", ".rs", ".java", ".kt", ".rb", ".php", ".c", ".h", ".hpp", ".cpp", ".cc",
    ".cs", ".swift", ".scala", ".sh", ".ps1", ".r", ".jl", ".vue", ".svelte",
    ".dart", ".ex", ".exs",
)
SRC_DIRS = ("src/", "app/", "lib/", "python/", "sql/", "packages/", "services/", "api/")
# ------------------------------------------------------------------------------

CHAMPS_REQUIS = ("maj", "cap", "jalon")
TACHE = re.compile(r"^\s*[-*]\s*\[( |x|X|>|~)\]\s+(.+?)\s*$")


def _git(args):
    return subprocess.run(["git"] + args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=15)


def allow():
    sys.exit(0)  # pas de sortie = décision par défaut (allow)


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}))
    sys.exit(0)


def is_project_code(f):
    if any(f.startswith(p) for p in IGNORED_PREFIXES):
        return False
    if f.startswith("site/") and not f.startswith("site/_content/"):
        return False  # moteur / rendu généré du site de doc
    return f.endswith(CODE_EXT) or f.startswith(SRC_DIRS)


def stage(chemin):
    """Le contenu tel qu'il sera COMMITÉ, pas celui du disque.

    Lire le disque laisserait passer une correction non indexée : l'agent
    répare `state.md`, oublie de l'ajouter, et commite la version cassée."""
    r = _git(["show", ":" + chemin])
    return r.stdout if r.returncode == 0 else None


def entete(texte):
    """Le même en-tête que celui de `claude-projets`. Renvoie {} si absent."""
    m = re.match(r"\s*---\s*\n(.*?)\n---\s*(\n|$)", texte, re.S)
    if not m:
        return {}
    out = {}
    for ligne in m.group(1).splitlines():
        if ":" in ligne and not ligne.lstrip().startswith("#"):
            cle, _, val = ligne.partition(":")
            out[cle.strip().lower()] = re.sub(r"\s+#.*$", "", val).strip()
    return out


def verifie_state(texte):
    """Reproches, étiquetés par nature.

    La distinction n'est pas cosmétique : un fichier ILLISIBLE fait disparaître
    le projet du tableau de bord sans bruit, un fichier PÉRIMÉ l'y montre avec
    une date fausse. Les deux se corrigent, mais pas pour la même raison, et
    confondre les deux dans un même message apprend à l'agent le mauvais geste."""
    d = entete(texte)
    if not d:
        return [("structure",
                 "il n'a plus d'en-tête `---` en première ligne — le collecteur "
                 "le range en « aucune déclaration » et le projet disparaît du "
                 "tableau de bord")]
    maux = []
    manquants = [c for c in CHAMPS_REQUIS if not d.get(c)]
    if manquants:
        maux.append(("structure",
                     "il lui manque " + ", ".join("`%s:`" % c for c in manquants)))
    maj = d.get("maj", "")
    if maj and not re.match(r"^\d{4}-\d{2}-\d{2}$", maj):
        maux.append(("structure",
                     "`maj:` doit être une date ISO `AAAA-MM-JJ`, pas « %s »" % maj[:20]))
    elif maj and maj != datetime.date.today().isoformat():
        maux.append(("fraicheur",
                     "`maj:` porte %s alors que le commit est d'aujourd'hui (%s) — "
                     "le tableau de bord datera ce projet du mauvais jour"
                     % (maj, datetime.date.today().isoformat())))
    return maux


def verifie_todo(texte):
    if not any(TACHE.match(l) for l in texte.splitlines()):
        return [("structure",
                 "il ne contient plus aucune tâche lisible — une tâche s'écrit "
                 "`- [ ] Libellé`, avec `[>]` en cours et `[x]` fait")]
    return []


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        allow()

    cmd = ((data.get("tool_input") or {}).get("command") or "")
    if not re.search(r"\bgit\b.+\bcommit\b", cmd):
        allow()
    if "mind-ok" in cmd:
        allow()

    r = _git(["diff", "--cached", "--name-only"])
    if r.returncode != 0:
        allow()  # pas un dépôt git, ou git indisponible -> ne bloque pas
    fichiers = [f.strip() for f in r.stdout.splitlines() if f.strip()]
    if not fichiers:
        allow()  # `git commit --amend`, commit vide… : rien à juger

    # 1. LISIBILITÉ — vaut même sans code, un fichier cassé est le pire cas.
    for nom, verif in ((".mind/state.md", verifie_state), (".mind/todo.md", verifie_todo)):
        if nom in fichiers:
            texte = stage(nom)
            if texte is None:
                continue  # suppression ou renommage : ce n'est pas notre sujet
            maux = verif(texte)
            if maux:
                tete = ("ne serait plus lisible par le tableau de bord"
                        if any(k == "structure" for k, _ in maux)
                        else "n'est pas à jour")
                deny("mind-guard : `%s` %s — %s. Corrige, réindexe "
                     "(`git add %s`), puis recommite."
                     % (nom, tete, " ; ".join(m for _, m in maux), nom))

    # 2. FRAÎCHEUR — du code sort, la déclaration doit suivre.
    code = [f for f in fichiers if is_project_code(f)]
    if not code:
        allow()

    absents = [n for n in (".mind/state.md", ".mind/todo.md") if n not in fichiers]
    if absents:
        echantillon = ", ".join(code[:5]) + (", …" if len(code) > 5 else "")
        deny(
            "mind-guard : du code projet est indexé (%s) sans mise à jour de %s. "
            "Ces deux fichiers sont ce que le tableau de bord lit pour savoir où "
            "en est ce projet et ce qui attend une décision — pas poussés, mais lus "
            "sur le disque : un commit qui les laisse en arrière rend le projet muet. "
            "Mets `.mind/state.md` (dont le champ `maj:`) et `.mind/todo.md` à "
            "jour, indexe-les, puis recommite. Si la déclaration n'a vraiment pas "
            "à bouger, ajoute ` # mind-ok` à la fin de la commande."
            % (echantillon, " et ".join("`%s`" % a for a in absents))
        )
    allow()


if __name__ == "__main__":
    main()
