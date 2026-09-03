#!/usr/bin/env python3
"""Monte un ATELIER agentique sur une machine neuve — pas un projet, la couche
au-dessus.

Le starter sait monter **un projet**. Ce script monte ce qui l'entoure :

    <racine>/CLAUDE.md      la MÉTHODE, héritée par tout agent d'un sous-dossier
    <racine>/<cto>/         le poste du CTO, harnais complet, dépôt git

C'est cette couche du milieu qui **se transporte**. La couche du poste
(`~/.claude/CLAUDE.md` : comptes, sessions, réseau) se refait sur chaque machine,
et la couche projet est propre à chaque projet. Le socle, lui, part tel quel.

POURQUOI LE SOCLE NE « PRÉVAUT » PAS. Un `CLAUDE.md` parent n'écrase pas celui
d'un projet : les deux sont lus, et le plus spécifique l'emporte en cas de
conflit. Le socle porte donc l'**invariant** — mémoire, hooks, skills,
frontières — et le projet ajoute son rôle et ses règles métier par-dessus.
Chercher à écraser depuis le parent produit deux textes qui se contredisent.

**Dry-run par défaut.** `--apply` pour écrire. Rien n'est jamais écrasé.
"""
import argparse, os, pathlib, shutil, subprocess, sys

GABARITS = pathlib.Path(__file__).resolve().parent.parent / "gabarits"


class Rapport:
    def __init__(self):
        self.faits, self.ignores, self.manuel = [], [], []
    def fait(self, m): self.faits.append(m)
    def ignore(self, m): self.ignores.append(m)
    def main_humaine(self, m): self.manuel.append(m)


def racine_starter() -> pathlib.Path:
    """Le dépôt qui nous contient — celui d'où l'on copie le harnais."""
    c = pathlib.Path(__file__).resolve().parent
    for _ in range(8):
        if (c / ".claude").is_dir() and (c / "CLAUDE.md").is_file() and (c / ".mind").is_dir():
            return c
        if c.parent == c:
            break
        c = c.parent
    raise SystemExit("Ce script doit vivre dans un clone du starter "
                     "(.claude/ + CLAUDE.md + .mind/ à la racine).")


def pose(src: pathlib.Path, dst: pathlib.Path, rap: Rapport, appliquer: bool,
         remplacements=None) -> bool:
    """Copie un gabarit, jamais par-dessus un fichier existant."""
    if dst.exists():
        rap.ignore("Existe déjà, non écrasé : %s" % dst)
        return False
    rap.fait("Créer %s" % dst)
    if appliquer:
        texte = src.read_text(encoding="utf-8")
        for vieux, neuf in (remplacements or {}).items():
            texte = texte.replace(vieux, neuf)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(texte, encoding="utf-8")
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--racine", default=str(pathlib.Path.home() / "Agentic"),
                    help="le dossier qui contiendra les projets (défaut : ~/Agentic)")
    ap.add_argument("--cto", default="cto",
                    help="nom du dossier du CTO (défaut : cto)")
    ap.add_argument("--utilisateur", default="",
                    help="prénom à écrire dans le rôle du CTO")
    ap.add_argument("--apply", action="store_true",
                    help="écrire réellement (sinon : dry-run)")
    a = ap.parse_args()

    starter = racine_starter()
    racine = pathlib.Path(os.path.expanduser(a.racine)).resolve()
    cto = racine / a.cto
    rap = Rapport()

    print("Atelier init")
    print("Racine      : %s" % racine)
    print("CTO         : %s" % cto)
    print("Starter     : %s" % starter)
    print("Mode        : %s" % ("APPLY" if a.apply else "DRY-RUN"))
    print()

    if starter == cto or starter.parent == cto:
        raise SystemExit("Le dossier du CTO ne peut pas être le clone du starter.")
    if not racine.exists():
        rap.fait("Créer la racine %s" % racine)
        if a.apply:
            racine.mkdir(parents=True)

    # 1. La MÉTHODE, à la racine. C'est l'artefact portable.
    pose(GABARITS / "socle-CLAUDE.md", racine / "CLAUDE.md", rap, a.apply)

    # 2. Le poste du CTO. Son rôle seulement — la méthode, il l'hérite.
    qui = a.utilisateur.strip() or "l'utilisateur"
    pose(GABARITS / "cto-CLAUDE.md", cto / "CLAUDE.md", rap, a.apply,
         {"[UTILISATEUR]": qui})

    # 3. Le harnais dans le dossier du CTO : c'est un projet comme un autre,
    #    dont le produit se trouve être l'atelier lui-même. On délègue à
    #    agentic-upgrade, qui est additif et déjà éprouvé, plutôt que de
    #    réécrire une seconde copie de la même logique.
    upgrade = starter / ".claude/skills/agentic-upgrade/scripts/agentic-upgrade.py"
    if not upgrade.is_file():
        raise SystemExit("Introuvable : %s" % upgrade)
    if a.apply:
        cto.mkdir(parents=True, exist_ok=True)
    if cto.is_dir():
        cmd = [sys.executable, str(upgrade), "--project-root", str(cto),
               "--template-root", str(starter)]
        if a.apply:
            cmd.append("--apply")
        r = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        print("── harnais du CTO (agentic-upgrade) " + "─" * 30)
        print(r.stdout.rstrip() or r.stderr.rstrip())
        print("─" * 65)
        print()
    else:
        rap.fait("Poser le harnais dans %s (agentic-upgrade)" % cto)

    # 4. Un dépôt git. Les deux hooks se déclenchent au `commit` : sans dépôt,
    #    ils sont inertes — et un hook inerte ne signale pas qu'il l'est.
    if (cto / ".git").is_dir():
        rap.ignore("Dépôt git déjà présent dans %s" % cto)
    else:
        rap.fait("git init dans %s (sans lui, les deux hooks sont inertes)" % cto)
        if a.apply:
            subprocess.run(["git", "init", "-q", str(cto)], check=False)

    rap.main_humaine(
        "CÂBLAGE : vérifier que settings.json du CTO déclare mind-guard "
        "(PreToolUse) et journal (PostToolUse), chacun DEUX fois — `python` et "
        "`python3`. Le harnais copie les hooks, il ne touche pas au câblage.")
    rap.main_humaine(
        "PREUVE : faire un commit d'essai de code sans toucher .mind/, et voir "
        "mind-guard refuser ; puis vérifier que .logs/<jour>.md s'écrit. Un hook "
        "qu'on n'a pas vu se déclencher n'est pas un hook vérifié.")
    rap.main_humaine(
        "SOCLE : le CLAUDE.md de la racine ne porte QUE la méthode. Le poste "
        "(comptes, sessions, réseau, RAM) va dans ~/.claude/CLAUDE.md ; le rôle "
        "et les règles métier vont dans le CLAUDE.md de chaque projet.")
    rap.main_humaine(
        "SUITE : pour chaque projet existant, /agentic-upgrade puis le tri de "
        "mémoire ; pour un projet neuf, cloner le starter puis /project-init.")

    print("Fait :")
    print("\n".join("- %s" % m for m in rap.faits) or "- Rien")
    print()
    print("Ignorés (non écrasés) :")
    print("\n".join("- %s" % m for m in rap.ignores) or "- Aucun")
    print()
    print("À faire ensuite (voir le SKILL atelier-init) :")
    print("\n".join("- %s" % m for m in rap.manuel))

    if not a.apply:
        print("\nDry-run seulement. Relancer avec --apply pour appliquer.")


if __name__ == "__main__":
    main()
