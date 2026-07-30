# -*- coding: utf-8 -*-
"""Publie le site en une commande : génère (_content -> .qmd) + rend (Quarto)
+ déploie selon `site.config.yml` (cible pluggable : azure | ghpages | zip | none).

Usage :
    python site/publish.py                 # génère + rend + déploie (cible de la config)
    python site/publish.py --no-deploy     # génère + rend seulement
    python site/publish.py --target zip    # forcer une cible pour ce run

Config (`site/site.config.yml`) :
    deploy:
      target: zip            # azure | ghpages | zip | none
      azure: { storage: ..., resource_group: ... }
      ghpages: { branch: gh-pages }
"""
from __future__ import annotations
import argparse, os, shutil, subprocess, sys, pathlib, re

SITE = pathlib.Path(__file__).resolve().parent
BASE = SITE.parent
CONTENT = SITE / "_content"


def run(cmd, **kw):
    print("»", " ".join(cmd))
    return subprocess.run(cmd, check=True, **kw)


def load_cfg():
    try:
        import yaml
    except ImportError:
        sys.exit("PyYAML manquant : `pip install -r site/requirements.txt` (ou /publish-docs setup).")
    cfg = {"title": "Documentation", "deploy": {"target": "none"}}
    p = SITE / "site.config.yml"
    if p.exists():
        d = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        for k, v in d.items():
            if v is not None:
                cfg[k] = v
    return cfg


def prefix(cfg):
    return re.sub(r"[^A-Za-z0-9]+", "_", str(cfg.get("title") or "Doc")).strip("_") or "Doc"


def domains(cfg):
    if cfg.get("domains"):
        return [str(d) for d in cfg["domains"]]
    if not CONTENT.exists():
        return []
    return sorted(d.name for d in CONTENT.iterdir()
                  if d.is_dir() and not d.name.startswith("_") and d.name != "suivi")


def find_quarto():
    q = shutil.which("quarto")
    if q:
        return q
    for c in (r"C:\Program Files\Quarto\bin\quarto.cmd", r"C:\Program Files\Quarto\bin\quarto"):
        if pathlib.Path(c).exists():
            return c
    sys.exit("Quarto introuvable (installe-le ou ajoute-le au PATH — cf. /publish-docs setup).")


# ---------------------------------------------------------------- DÉPLOIEMENT
def deploy_zip(cfg):
    out = shutil.make_archive(str(BASE / f"{prefix(cfg)}_site"), "zip", str(SITE / "_site"))
    print(f"\nOK — archive créée : {out}")


def deploy_azure(cfg):
    az = shutil.which("az") or shutil.which("az.cmd")
    if not az:
        sys.exit("Azure CLI (az) introuvable.")
    acfg = cfg.get("deploy", {}).get("azure", {}) or {}
    storage = acfg.get("storage") or os.environ.get("SITE_AZURE_STORAGE")
    rg = acfg.get("resource_group") or os.environ.get("SITE_AZURE_RG")
    if not storage or not rg:
        sys.exit("deploy.azure.storage / resource_group manquants dans site.config.yml.")
    key = subprocess.run([az, "storage", "account", "keys", "list", "-n", storage, "-g", rg,
                          "--query", "[0].value", "-o", "tsv"],
                         check=True, capture_output=True, text=True).stdout.strip()
    if not key:
        sys.exit("Clé de compte non récupérée (az login actif ? droits listKeys ?).")
    run([az, "storage", "blob", "upload-batch", "--account-name", storage, "--account-key", key,
         "-d", "$web", "-s", str(SITE / "_site"), "--overwrite", "--output", "none"])
    url = subprocess.run([az, "storage", "account", "show", "-n", storage, "-g", rg,
                          "--query", "primaryEndpoints.web", "-o", "tsv"],
                         check=True, capture_output=True, text=True).stdout.strip()
    print(f"\nOK — site déployé : {url}")


def deploy_ghpages(cfg):
    """Pousse `_site` sur la branche gh-pages du dépôt (origin). Nécessite un remote git."""
    branch = (cfg.get("deploy", {}).get("ghpages", {}) or {}).get("branch", "gh-pages")
    try:
        origin = subprocess.run(["git", "-C", str(BASE), "remote", "get-url", "origin"],
                                check=True, capture_output=True, text=True).stdout.strip()
    except subprocess.CalledProcessError:
        sys.exit("Aucun remote git 'origin' — GitHub Pages nécessite un dépôt distant.")
    site = SITE / "_site"
    (site / ".nojekyll").write_text("", encoding="utf-8")
    env = {**os.environ, "GIT_DIR": str(site / ".git"), "GIT_WORK_TREE": str(site)}
    subprocess.run(["git", "init", "-q"], cwd=str(site), check=True)
    subprocess.run(["git", "add", "-A"], cwd=str(site), check=True)
    subprocess.run(["git", "commit", "-qm", "deploy site"], cwd=str(site), check=True)
    run(["git", "push", "-f", origin, f"HEAD:{branch}"], cwd=str(site))
    shutil.rmtree(site / ".git", ignore_errors=True)
    print(f"\nOK — poussé sur {branch} (origin). Activer GitHub Pages sur cette branche si besoin.")


DEPLOYERS = {"zip": deploy_zip, "azure": deploy_azure, "ghpages": deploy_ghpages, "none": lambda c: None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-deploy", action="store_true", help="génère et rend, sans déployer")
    ap.add_argument("--target", choices=list(DEPLOYERS), help="forcer la cible de déploiement")
    args = ap.parse_args()
    cfg = load_cfg()

    # 1. Génération des .qmd depuis _content/
    run([sys.executable, str(SITE / "build_site.py")])

    # 2. Rendu Quarto (fermer Edge d'abord sous Windows : ses handles verrouillent _site)
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/IM", "msedge.exe"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    gv = r"C:\Program Files\Graphviz\bin"
    if os.path.isdir(gv) and gv not in os.environ.get("PATH", ""):
        os.environ["PATH"] = gv + os.pathsep + os.environ["PATH"]
    quarto = find_quarto()
    run([quarto, "render", "--quiet"], cwd=str(SITE))

    # 2b. Dossier complet par domaine (PDF via Typst + Word) — exclu du rendu website.
    pre = prefix(cfg)
    for dom in domains(cfg):
        if (SITE / dom / "dossier.qmd").exists():
            run([quarto, "render", f"{dom}/dossier.qmd", "--to", "typst,docx", "--quiet"], cwd=str(SITE))
            for ext in ("pdf", "docx"):
                out = SITE / dom / f"dossier.{ext}"
                if out.exists():
                    dest = SITE / "_site" / dom / f"{pre}_{dom}_Dossier-technique.{ext}"
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(out), str(dest))

    if args.no_deploy:
        print("\nOK (généré + rendu). Déploiement ignoré (--no-deploy).")
        return

    # 3. Déploiement (cible de la config ou --target)
    target = args.target or (cfg.get("deploy", {}) or {}).get("target", "none")
    print(f"\nDéploiement : cible = {target}")
    DEPLOYERS.get(target, DEPLOYERS["none"])(cfg)


if __name__ == "__main__":
    main()
