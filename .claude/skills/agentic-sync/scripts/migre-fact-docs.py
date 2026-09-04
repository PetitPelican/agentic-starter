#!/usr/bin/env python3
"""migre-fact-docs — fait passer un projet de l'ANCIENNE forme à la forme MONO.

    .mind/{stack,architecture,rules}.md  ->  .fact/
    .mind/{state,todo}.md               ->  restent
    .memory/                            ->  docs/
    .memory/MEMORY.md                   ->  docs/README.md
    .memory/journal.md                  ->  SIGNALÉ, pas supprimé
    cap: de .mind/state.md              ->  .fact/base.md (créé)

CE QU'IL NE FAIT PAS, exprès :

- Il ne convertit PAS en multi-agents. C'est une autre décision, et elle a son
  propre skill : la forme mono est le défaut, et elle suffit à huit projets
  sur dix.
- Il ne supprime RIEN. `journal.md`, les sorties de build tombées dans `docs/`,
  les fichiers de trop : il les nomme, il laisse le projet trancher. Supprimer
  du contenu qu'on n'a pas lu est le geste qu'on ne rattrape pas.
- Il ne réécrit pas le `CLAUDE.md`. Sa section mémoire devient fausse après la
  migration — c'est signalé, et c'est à la main : le texte porte le rôle du
  projet, pas seulement des chemins.

**Dry-run par défaut.** `--apply` pour écrire. Utilise `git mv` quand le dépôt
le permet, pour que l'historique suive les fichiers.
"""
import argparse, pathlib, re, subprocess, sys

FACT = ("architecture.md", "stack.md", "rules.md")
RENOMME = {"MEMORY.md": "README.md"}
BASE = """---
cap: %s
---

# %s — la base

## Nature

%s

## Où on va

[LA_TRAJECTOIRE — les phases, et la borne qui clôt la phase courante. En prose :
aucun programme ne le lit, et un champ de plus serait un formulaire à remplir.]

## Ce que ce projet n'est pas

[LES_HORS-SUJETS — ce qu'on a explicitement décidé de ne pas faire.]
"""


def git(p, *a):
    try:
        return subprocess.run(("git", "-C", str(p)) + a, capture_output=True,
                              text=True, timeout=15).returncode == 0
    except Exception:
        return False


def bouge(projet, src, dst, appliquer, rap):
    if not src.exists():
        return
    if dst.exists():
        rap.append(("⚠", "%s existe déjà — %s laissé en place, à fusionner à la main"
                    % (dst.relative_to(projet), src.relative_to(projet))))
        return
    rap.append(("→", "%s  ->  %s" % (src.relative_to(projet), dst.relative_to(projet))))
    if appliquer:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not git(projet, "mv", str(src.relative_to(projet)), str(dst.relative_to(projet))):
            src.rename(dst)          # pas un dépôt git, ou fichier non suivi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    p = pathlib.Path(a.project_root).resolve()
    rap, reste = [], []

    if (p / ".fact").is_dir():
        print("Déjà migré : %s porte un .fact/. Rien à faire." % p.name)
        return 0
    if not (p / ".mind").is_dir():
        print("Pas de .mind/ : ce projet n'est pas au harnais. Voir /agentic-upgrade.")
        return 1

    # 1. les faits du projet montent dans .fact/
    for n in FACT:
        bouge(p, p / ".mind" / n, p / ".fact" / n, a.apply, rap)

    # 2. .memory/ devient docs/ — le mot « mémoire » ne doit plus désigner deux
    #    choses, la seconde étant celle de l'agent sous ~/.claude/projects/.
    mem = p / ".memory"
    if mem.is_dir():
        for f in sorted(mem.glob("*.md")):
            bouge(p, f, p / "docs" / RENOMME.get(f.name, f.name), a.apply, rap)
        for d in sorted(x for x in mem.iterdir() if x.is_dir()):
            bouge(p, d, p / "docs" / d.name, a.apply, rap)

    # 3. .fact/base.md, avec le cap récupéré dans state.md — il y était jusqu'ici.
    state = p / ".mind" / "state.md"
    cap = ""
    if state.is_file():
        m = re.search(r"^cap:\s*(.+?)\s*$", state.read_text(encoding="utf-8",
                                                            errors="replace"), re.M)
        cap = m.group(1) if m else ""
    base = p / ".fact" / "base.md"
    if base.exists():
        rap.append(("⚠", ".fact/base.md existe déjà — laissé tel quel"))
    else:
        rap.append(("+", ".fact/base.md créé%s" % (" (cap: repris de state.md)" if cap
                                                   else " — SANS cap:, à écrire")))
        if a.apply:
            base.parent.mkdir(parents=True, exist_ok=True)
            base.write_text(BASE % (cap or "[À_ÉCRIRE — le but du projet, en une phrase]",
                                    p.name,
                                    "[CE_QUE_C_EST — le produit, le client, le problème résolu.]"),
                            encoding="utf-8")
    # le cap quitte state.md : deux sources pour un même fait, c'est une qui ment
    if cap and state.is_file():
        rap.append(("−", "cap: retiré de .mind/state.md (il vit maintenant dans .fact/base.md)"))
        if a.apply:
            t = state.read_text(encoding="utf-8")
            state.write_text(re.sub(r"^cap:.*\n", "", t, count=1, flags=re.M), encoding="utf-8")

    # 4. ce qui reste à la main — nommé, jamais supprimé
    if (p / "docs" / "journal.md").exists() or (mem / "journal.md").exists():
        reste.append("docs/journal.md est la génération précédente de .logs/ (écrit par "
                     "le hook `journal` à chaque commit, dédoublonné par empreinte). "
                     "Vérifier qu'il n'apporte plus rien, puis le supprimer À LA MAIN.")
    genere = [f.name for f in (p / "docs").glob("*")
              if f.suffix.lower() in (".pdf", ".html", ".png", ".jpg", ".zip")] \
        if (p / "docs").is_dir() else []
    if genere:
        reste.append("docs/ contient %d fichier(s) qui ressemblent à des sorties de build "
                     "(%s). `docs/` ne contient que de l'écrit à la main : les sortir."
                     % (len(genere), ", ".join(sorted(genere)[:5])))
    reste.append("CLAUDE.md : sa section mémoire parle encore de `.mind/` à cinq fichiers "
                 "et de `.memory/`. La réécrire — trois dossiers, trois natures.")
    reste.append("settings.json : les hooks restent appelés en `.claude/hooks/…` (forme "
                 "MONO, l'agent est à la racine). Ne rien changer ici tant que le projet "
                 "n'est pas converti en multi-agents.")

    print("── Migration .fact / docs — %s%s" % (p.name, "" if a.apply else "  [DRY-RUN]"))
    for signe, ligne in rap:
        print("  %s %s" % (signe, ligne))
    if not rap:
        print("  (rien à déplacer)")
    print("\n── À reprendre à la main")
    for r in reste:
        print("  · %s" % r)
    if not a.apply:
        print("\nDry-run. Relancer avec --apply pour écrire.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
