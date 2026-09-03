#!/usr/bin/env python3
"""briefing — hook SessionStart + UserPromptSubmit.

Le pendant de `mind-guard`. Celui-là force à **écrire** la mémoire au commit ;
celui-ci force à la **lire** au démarrage. Ensemble ils ferment la boucle : un
projet dont la mémoire est à jour mais que l'agent n'ouvre jamais est aussi
inutile qu'un projet sans mémoire.

LA PANNE QU'IL CORRIGE, mesurée le 03/09/2026. Interrogé sur les outils
auxquels il avait accès, un agent a répondu de travers alors que la réponse
tenait dans son `.mind/stack.md` — 173 lignes, à jour du jour même. Il n'avait
pas négligé de lire : **rien dans son contexte de démarrage ne nommait ce
fichier**. Son `CLAUDE.md` faisait une ligne. Sur huit projets de l'atelier,
sept nommaient `.mind/` et un seul ne le faisait pas : c'était celui-là.

CE QU'IL N'EST PAS. Il ne recopie pas la mémoire dans le contexte — ce serait
la faute que `.mind/` existe pour éviter, une copie qui se périme en silence.
Il injecte **ce qui ne tient pas dans un pointeur** (le cap, la fraîcheur, le
nombre de décisions en attente, les droits réellement appliqués) et, pour tout
le reste, **les titres de section de chaque fichier** : de quoi savoir quelle
question va trouver sa réponse où, sans en lire le contenu.

CE QU'IL AFFIRME EST TOUJOURS RELU. Chaque déclenchement rouvre les fichiers.
Rien n'est mis en cache d'une session à l'autre, donc rien ne peut vieillir.

QUAND IL PARLE.
  - `SessionStart` : à chaque fois. Ses quatre sources — startup, resume,
    clear, compact — couvrent le cas qui compte le plus, la **compaction** :
    c'est l'instant précis où l'agent perd du contexte, donc celui où le
    briefing vaut le plus cher.
  - `UserPromptSubmit` : **silencieux par défaut**. Il ne parle que si rien n'a
    encore été injecté, ou si un fichier de `.mind/` ou `settings.json` a
    changé depuis. Coût nul en régime établi, et c'est ce qui permet de poser
    le hook sur une **session déjà ouverte** : vérifié le 03/09/2026, un
    `settings.json` de projet ajouté à chaud est relu sans redémarrage, et le
    premier message qui suit reçoit le briefing.

LE VERROU. Le harnais déclare chaque hook deux fois, `python` et `python3`,
pour couvrir Windows et macOS. `mind-guard` s'en moque : deux refus valent un
refus. Un injecteur, lui, injecterait **deux fois** sur une machine où les deux
interpréteurs répondent. D'où le verrou atomique : le premier des deux prend le
tour, l'autre se tait.

**fail-open** : toute erreur, tout fichier absent, tout dépôt sans `.mind/`
laisse passer sans rien injecter. Un briefing n'a jamais à empêcher un tour de
parole.
"""
import datetime, errno, json, os, pathlib, re, sys, time

FENETRE_VERROU = 5          # s — au-delà, un verrou est considéré abandonné
MIND = ("state.md", "todo.md", "stack.md", "architecture.md", "rules.md")
CHAMPS = ("maj", "cap", "sante", "jalon")
ENTETE = re.compile(r"\s*---\s*\n(.*?)\n---\s*(\n|$)", re.S)
TACHE = re.compile(r"^\s*[-*]\s*\[( |x|X|>|~)\]\s+(.+?)\s*$")
PRIO = re.compile(r"!(haut|moyen|bas)\b")
# Même dialecte que `.mind/todo.md` et le tableau de bord : tout `@nom`, et
# `@dehors` seul réservé. Le `@` doit ouvrir un mot, sinon `root@serveur`
# passerait pour un destinataire.
QUI = re.compile(r"(?:^|(?<=\s))@([A-Za-zÀ-ÿ][\w-]*)\b")
DEHORS = "dehors"
TITRE = re.compile(r"^##\s+(.+?)\s*$", re.M)


def rien():
    """Sortie muette. Pas de JSON = pas d'injection, et surtout pas d'erreur."""
    sys.exit(0)


def lis(p):
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _remonte(depart):
    """Le premier ancêtre qui porte un `.mind/`, `depart` compris."""
    try:
        p = pathlib.Path(depart).resolve()
    except (OSError, ValueError):
        return None
    while True:
        if (p / ".mind").is_dir():
            return p
        if p.parent == p:
            return None
        p = p.parent


def racine(charge):
    """Le dossier du projet.

    `CLAUDE_PROJECT_DIR` fait AUTORITÉ quand il est posé : s'il ne mène à aucun
    `.mind/`, on se tait. Repli interdit — mesuré le 03/09/2026, une chaîne de
    repli qui finissait sur `os.getcwd()` briefait le projet du **répertoire
    courant du processus** au lieu de celui demandé, c'est-à-dire injectait le
    cap, les décisions en attente et les droits d'un projet étranger."""
    declare = os.environ.get("CLAUDE_PROJECT_DIR") or charge.get("cwd")
    if declare:
        return _remonte(declare)
    return _remonte(os.getcwd())


def entete(texte):
    m = ENTETE.match(texte or "")
    if not m:
        return {}
    d = {}
    for ligne in m.group(1).splitlines():
        if ":" in ligne and not ligne.lstrip().startswith("#"):
            k, _, v = ligne.partition(":")
            k = k.strip().lower()
            if k in CHAMPS:
                d[k] = v.strip()
    return d


def jours(iso):
    try:
        d = datetime.date.fromisoformat((iso or "").strip()[:10])
    except ValueError:
        return None
    return (datetime.date.today() - d).days


def attentes(texte):
    """Les tâches ouvertes qui portent un destinataire nommé, `@dehors` exclu."""
    out = []
    for ligne in (texte or "").splitlines():
        m = TACHE.match(ligne)
        if not m or m.group(1) in ("x", "X"):
            continue
        libelle = m.group(2)
        q = QUI.search(libelle)
        if not q or q.group(1).lower() == DEHORS:
            continue
        p = PRIO.search(libelle)
        out.append((p.group(1) if p else "moyen",
                    PRIO.sub("", QUI.sub("", libelle)).replace("**", "").strip(" -—·")))
    out.sort(key=lambda t: {"haut": 0, "moyen": 1, "bas": 2}.get(t[0], 1))
    return out


def sommaire(p, combien=7):
    """Les titres `##` d'un fichier — de quoi savoir ce qu'il répond, sans le
    lire. C'est le cœur du dispositif : un pointeur nu (« voir stack.md ») ne
    dit pas quelle question y trouve sa réponse, donc ne déclenche pas
    l'ouverture."""
    t = lis(p)
    if not t:
        return None
    titres = [x.strip() for x in TITRE.findall(t)][:combien]
    return len(t.splitlines()), titres


def droits(r):
    """Ce qui est **appliqué**, pas ce qui est écrit. Un droit en prose est un
    espoir ; une règle `deny` est un fait."""
    for nom in ("settings.json", "settings.local.json"):
        p = r / ".claude" / nom
        if not p.exists():
            continue
        try:
            j = json.loads(lis(p) or "{}")
        except ValueError:
            return nom, None
        perm = j.get("permissions", {}) or {}
        return nom, (perm.get("defaultMode", "—"),
                     perm.get("allow", []) or [], perm.get("deny", []) or [])
    return None, None


def a_change(r, depuis):
    """Un fichier surveillé est-il plus récent que la dernière injection ?"""
    for p in [r / ".mind" / n for n in MIND] + \
             [r / ".claude" / "settings.json", r / "CLAUDE.md"]:
        try:
            if p.stat().st_mtime > depuis:
                return True
        except OSError:
            continue
    return False


def prends_le_tour(r):
    """Un seul des deux interpréteurs déclarés injecte. Création atomique :
    celui qui obtient le fichier parle, l'autre se tait."""
    v = r / ".claude" / ".briefing.lock"
    try:
        v.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(v), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        os.write(fd, str(time.time()).encode())
        os.close(fd)
        return True
    except OSError as e:
        if e.errno != errno.EEXIST:
            return False
        try:                      # verrou abandonné (interpréteur mort) : on reprend
            if time.time() - v.stat().st_mtime > FENETRE_VERROU:
                v.unlink()
                return prends_le_tour(r)
        except OSError:
            pass
        return False


def rends_le_tour(r):
    try:
        (r / ".claude" / ".briefing.lock").unlink()
    except OSError:
        pass


def compose(r):
    l = []
    a = l.append
    e = entete(lis(r / ".mind" / "state.md"))
    j = jours(e.get("maj", ""))
    frais = ("à jour" if j is not None and j <= 7 else
             "TIÈDE" if j is not None and j <= 28 else
             "PÉRIMÉ" if j is not None else "EN-TÊTE ILLISIBLE")

    a("── Briefing d'entrée · %s ─ relu à l'instant, jamais recopié ──" % r.name)
    a("cap    : %s" % (e.get("cap") or "AUCUN `cap:` déclaré dans .mind/state.md"))
    a("état   : %s%s · santé %s · jalon : %s"
      % (frais, "" if j is None else " (%d j)" % j,
         e.get("sante") or "—", e.get("jalon") or "—"))

    att = attentes(lis(r / ".mind" / "todo.md"))
    if att:
        a("attente: %d décision(s) humaine(s) — la première : [%s] %s"
          % (len(att), att[0][0], att[0][1][:70]))
        a("         Ça passe avant tout le reste dans un point d'avancement.")
    else:
        a("attente: aucune tâche `@<qui>` ouverte dans .mind/todo.md")

    a("")
    a("Avant toute affirmation sur ce projet, ouvrir le fichier qui porte la")
    a("réponse — ces titres disent lequel :")
    for nom, quoi in (("stack.md", "outils, comptes, accès, versions"),
                      ("rules.md", "ce qu'on ne franchit pas"),
                      ("architecture.md", "comment c'est agencé, les frontières")):
        s = sommaire(r / ".mind" / nom)
        if not s:
            a("  .mind/%-16s ABSENT — %s : personne ne le sait." % (nom, quoi))
            continue
        n, titres = s
        a("  .mind/%-16s %3d l. · %s" % (nom, n, quoi))
        if titres:
            a("      %s" % " · ".join(titres))
    a("  .memory/decisions.md   le pourquoi de chaque choix, daté")

    fichier, d = droits(r)
    a("")
    if d is None:
        a("Droits : %s — rien n'est mécaniquement interdit dans ce projet."
          % ("`%s` illisible" % fichier if fichier else
             "aucun settings.json"))
        a("         Tout ce qui a été dit à l'oral n'est retenu par rien.")
    else:
        mode, allow, deny = d
        a("Droits appliqués (%s) : mode %s · %d allow · %d deny"
          % (fichier, mode, len(allow), len(deny)))
        for rg in deny[:6]:
            a("    refusé : %s" % rg)
        if not deny:
            a("    ⚠ aucun `deny` : ce qui doit être interdit ici ne l'est que")
            a("      par la prose. Un droit en prose est un espoir.")
    return "\n".join(l)


def main():
    try:
        charge = json.loads(sys.stdin.read() or "{}")
    except (ValueError, OSError):
        charge = {}
    evenement = charge.get("hook_event_name") or "SessionStart"

    r = racine(charge)
    if r is None:                       # pas de `.mind/` : rien à briefer
        rien()

    etat = r / ".claude" / ".briefing.json"
    if evenement == "UserPromptSubmit":
        # Silencieux, sauf si jamais injecté ou si la mémoire a bougé depuis.
        try:
            depuis = float(json.loads(lis(etat) or "{}").get("derniere", 0))
        except (ValueError, TypeError):
            depuis = 0
        if depuis and not a_change(r, depuis):
            rien()

    if not prends_le_tour(r):           # l'autre interpréteur s'en charge
        rien()
    try:
        texte = compose(r)
        etat.parent.mkdir(parents=True, exist_ok=True)
        etat.write_text(json.dumps({"derniere": time.time(),
                                    "evenement": evenement}), encoding="utf-8")
    except Exception:
        rends_le_tour(r)
        rien()
    rends_le_tour(r)

    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": evenement,
        "additionalContext": texte,
    }}))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:                   # fail-open, sans exception
        rien()
