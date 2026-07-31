#!/usr/bin/env python3
"""memory-guard - hook PreToolUse (matcher Bash, if Bash(git push*)).

Bloque un `git push` quand des commits de code projet vont être poussés SANS aucune
mise à jour de `.memory/`, pour forcer /memory-update (règle du starter : « avant tout
commit+push, mettre à jour la mémoire »). memory-update écrit aussi le journal `logs/`.

- N'agit que sur `git push` (double garde en plus du `if` de settings.json).
- Inspecte les commits non poussés (`@{u}..HEAD`).
- « code projet » = fichiers source hors outillage (`.claude/`, `.codex/`, `.memory/`,
  `logs/`, `docs/`, moteur de site généré). Ajuste les listes ci-dessous par projet.
- Échappatoire explicite : ajouter ` # memory-ok` à la fin de la commande git push.
- **fail-open** : toute erreur/ambiguïté (pas d'upstream, git indispo…) laisse passer.
"""
import sys, json, subprocess, re

# --- à ajuster selon le projet -------------------------------------------------
IGNORED_PREFIXES = (".claude/", ".codex/", ".memory/", "logs/", "docs/")
CODE_EXT = (
    ".py", ".sql", ".qmd", ".ipynb", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".go", ".rs", ".java", ".kt", ".rb", ".php", ".c", ".h", ".hpp", ".cpp", ".cc",
    ".cs", ".swift", ".scala", ".sh", ".ps1", ".r", ".jl", ".vue", ".svelte",
    ".dart", ".ex", ".exs",
)
SRC_DIRS = ("src/", "app/", "lib/", "python/", "sql/", "packages/", "services/", "api/")
# ------------------------------------------------------------------------------


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


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        allow()

    cmd = ((data.get("tool_input") or {}).get("command") or "")
    if not re.search(r"\bgit\b.+\bpush\b", cmd):
        allow()
    if "memory-ok" in cmd:
        allow()

    r = _git(["diff", "--name-only", "@{u}..HEAD"])
    if r.returncode != 0:
        allow()  # pas d'upstream configuré / ambigu -> ne bloque pas
    files = [f.strip() for f in r.stdout.splitlines() if f.strip()]
    if not files:
        allow()

    code = [f for f in files if is_project_code(f)]
    memory = [f for f in files if f.startswith(".memory/")]

    if code and not memory:
        sample = ", ".join(code[:5]) + (", …" if len(code) > 5 else "")
        deny(
            "Garde-fou mémoire : des changements de code projet vont être poussés sans mise à jour "
            f"de .memory/ ({sample}). Lance /memory-update (met aussi à jour le journal logs/), "
            "commite les fichiers .memory/ concernés, puis relance le push. Si la mémoire n'a "
            "vraiment pas à évoluer, ajoute ' # memory-ok' à la fin de la commande git push."
        )
    allow()


if __name__ == "__main__":
    main()
