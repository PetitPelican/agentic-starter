# -*- coding: utf-8 -*-
"""Générateur du site de doc Quarto — ASSEMBLEUR générique (piloté par config).

Le CONTENU des pages vit dans `site/_content/**/*.qmd` (markdown éditable, généré
depuis la mémoire par `/publish-docs refresh`). Ce script :
  1. lit `site/site.config.yml` (titre, tagline, logo, preset, domaines, déploiement) ;
  2. écrit la config Quarto (`_quarto.yml`) + le thème (`theme.scss`) — sidebar dérivée
     des domaines/sections présents dans `_content/` ;
  3. pré-rend les schémas `_content/<domaine>/_diagrams/*.dot` en SVG (web) + PNG (export) ;
  4. développe les jetons d'injection et écrit les `.qmd` rendus par Quarto ;
  5. assemble un « dossier complet » (PDF Typst + Word) par domaine.

Jetons d'injection (gardent code/SQL DRY, lus depuis les vrais fichiers du dépôt) :
  @@SQL:chemin.sql@@       -> bloc « ### `chemin` » + ```sql <contenu> ```
  @@CODE:chemin:langage@@  -> ```langage <contenu brut> ```
  @@EXPORT:<DOMAINE>@@     -> barre de boutons PDF/Word du dossier complet

Régénérer : `python site/build_site.py` puis `quarto render` (ou `python site/publish.py`).
Portable (chemins déduits de __file__)."""
import pathlib, re, subprocess, os, sys

SITE = pathlib.Path(__file__).resolve().parent
BASE = SITE.parent
CONTENT = SITE / "_content"
SITE.mkdir(exist_ok=True)

# Graphviz requis pour pré-rendre les `.dot`. Ajout du chemin Windows courant si présent ;
# sinon on suppose `dot` sur le PATH (brew/apt/winget).
for _gv in (r"C:\Program Files\Graphviz\bin",):
    if os.path.isdir(_gv) and _gv not in os.environ.get("PATH", ""):
        os.environ["PATH"] = _gv + os.pathsep + os.environ["PATH"]

# ------------------------------------------------------------------ CONFIG
try:
    import yaml
except ImportError:
    sys.exit("PyYAML manquant : `pip install -r site/requirements.txt` (ou lance /publish-docs setup).")

def _load_config():
    defaults = {"title": "Documentation", "tagline": "", "logo_letter": "",
                "preset": "generic", "domains": None, "deploy": {"target": "none"}}
    p = SITE / "site.config.yml"
    if p.exists():
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        for k, v in data.items():
            if v is not None:
                defaults[k] = v
    return defaults

CFG = _load_config()
TITLE = str(CFG.get("title") or "Documentation")
TAGLINE = str(CFG.get("tagline") or "")
LOGO = (str(CFG.get("logo_letter") or TITLE[:1] or "D"))[:1].upper()
PRESET = str(CFG.get("preset") or "generic")
# Préfixe des fichiers d'export (URL + téléchargement) : slug du titre.
PREFIX = re.sub(r"[^A-Za-z0-9]+", "_", TITLE).strip("_") or "Doc"

PRESET_SECTIONS = {
    "data":    ["objectifs-perimetre", "architecture", "regles-gestion", "recette", "points-ouverts"],
    "web":     ["objectifs-perimetre", "architecture", "stack-conventions", "fonctionnalites", "points-ouverts"],
    "api":     ["objectifs-perimetre", "architecture", "endpoints", "auth-securite", "points-ouverts"],
    "generic": ["objectifs-perimetre", "architecture", "points-ouverts"],
}

def w(rel, content):
    p = SITE / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print("  ", rel)

def read(rel):
    return (BASE / rel).read_text(encoding="utf-8")

def domains():
    """Domaines = liste explicite de la config, sinon sous-dossiers de `_content/`
    (hors `suivi` et dossiers `_*`)."""
    if CFG.get("domains"):
        return [str(d) for d in CFG["domains"]]
    if not CONTENT.exists():
        return []
    return sorted(d.name for d in CONTENT.iterdir()
                  if d.is_dir() and not d.name.startswith("_") and d.name != "suivi")

def domain_sections(dom):
    """Sections d'un domaine, ordonnées selon le preset puis les extras (alpha)."""
    order = PRESET_SECTIONS.get(PRESET, PRESET_SECTIONS["generic"])
    files = [p.stem for p in (CONTENT / dom).glob("*.qmd")]
    return [s for s in order if s in files] + [f for f in sorted(files) if f not in order]

# ------------------------------------------------------------------ INJECTION
def _sql_sub(m):
    rel = m.group(1)
    return f"### `{rel}`\n\n```sql\n" + read(rel).strip() + "\n```\n"

def _code_sub(m):
    rel, lang = m.group(1), m.group(2)
    return f"```{lang}\n" + read(rel) + "\n```"

def _export_sub(m):
    """Barre de boutons (HTML brut) : exporte TOUT le dossier du domaine en PDF / Word.
    Fichiers servis : <PREFIX>_<DOMAINE>_Dossier-technique.{pdf,docx} (renommés par publish.py)."""
    dom = m.group(1)
    base = f"{PREFIX}_{dom}_Dossier-technique"
    return (
        '```{=html}\n'
        '<div class="export-bar">\n'
        f'  <span class="export-label">Dossier <b>{dom}</b> complet&nbsp;:</span>\n'
        f'  <a class="btn-export pdf" href="{base}.pdf" download="{base}.pdf">'
        '<i class="bi bi-file-earmark-pdf"></i> PDF</a>\n'
        f'  <a class="btn-export docx" href="{base}.docx" download="{base}.docx">'
        '<i class="bi bi-file-earmark-word"></i> Word</a>\n'
        '</div>\n'
        '```'
    )

def _cards(_m=None):
    """@@CARDS@@ -> grille de cartes vers chaque domaine (page d'accueil générique)."""
    out = ['::: {.grid-cards}']
    for dom in domains():
        secs = domain_sections(dom)
        if not secs:
            continue
        out += [f'<a class="domain-card" href="{dom}/{secs[0]}.html">',
                '  <div class="ico">📁</div>',
                f'  <h4>{dom}</h4>',
                f'  <p>Documentation du domaine {dom}.</p>',
                '  <div class="more">Ouvrir →</div>', '</a>']
    out.append(':::')
    return "\n".join(out)

def expand(text):
    text = text.replace("@@TITLE@@", TITLE).replace("@@TAGLINE@@", TAGLINE)
    text = re.sub(r"@@CARDS@@", _cards, text)
    text = re.sub(r"@@SQL:([^@]+)@@", _sql_sub, text)
    text = re.sub(r"@@CODE:([^:@]+):([a-z0-9]+)@@", _code_sub, text)
    text = re.sub(r"@@EXPORT:([A-Za-z0-9_-]+)@@", _export_sub, text)
    return text

# ------------------------------------------------------------------ SIDEBAR (dynamique)
def _sidebar_yaml():
    out = []
    for dom in domains():
        secs = domain_sections(dom)
        if not secs:
            continue
        out.append(f'      - section: "{dom}"')
        out.append('        contents:')
        out += [f'          - {dom}/{s}.qmd' for s in secs]
    if (CONTENT / "suivi").is_dir():
        subs = [p.stem for p in (CONTENT / "suivi").glob("*.qmd")]
        order = ["journal", "en-cours", "backlog"]
        subs = [s for s in order if s in subs] + [x for x in sorted(subs) if x not in order]
        if subs:
            out.append('      - section: "Suivi"')
            out.append('        contents:')
            out += [f'          - suivi/{s}.qmd' for s in subs]
    return "\n".join(out)

# ------------------------------------------------------------------ CONFIG QUARTO
_QUARTO = '''project:
  type: website
  output-dir: _site
  render:
    - "*.qmd"
    - "!**/dossier.qmd"

website:
  title: "@@TITLE@@"
  description: "@@TAGLINE@@"
  page-navigation: true
  search: false
  page-footer:
    center: "@@TITLE@@"
  sidebar:
    style: docked
    collapse-level: 1
    contents:
@@SIDEBAR@@

lightbox: auto   # clic sur un schéma/graphe -> ouverture zoomable en modale (SVG inclus)

execute:
  echo: false
  warning: false

format:
  html:
    theme: [cosmo, theme.scss]
    fig-format: svg
    toc: true
    toc-title: "Sur cette page"
    number-sections: false
    code-tools: false
    code-copy: true
    highlight-style: github
    fig-cap-location: bottom
    include-in-header:
      text: |
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    include-after-body:
      text: |
        <script>
        // Ouverture locale (file://) : compléter les liens de dossier par index.html.
        document.addEventListener('DOMContentLoaded', function () {
          document.querySelectorAll('a[href]').forEach(function (a) {
            var h = a.getAttribute('href');
            if (!h || h.indexOf('#') === 0 || /^[a-z]+:/i.test(h)) return;
            if (h === '.' || h === './') { a.setAttribute('href', 'index.html'); }
            else if (h.charAt(h.length - 1) === '/') { a.setAttribute('href', h + 'index.html'); }
          });
        });
        </script>
    grid:
      sidebar-width: 270px
      body-width: 1040px
      margin-width: 300px
      gutter-width: 1.5rem
'''
w("_quarto.yml", (_QUARTO
                  .replace("@@TITLE@@", TITLE)
                  .replace("@@TAGLINE@@", TAGLINE)
                  .replace("@@SIDEBAR@@", _sidebar_yaml())))

# ------------------------------------------------------------------ THEME (SaaS)
_THEME = '''/*-- scss:defaults --*/
$primary: #2563EB;
$link-color: #2563EB;
$body-color: #334155;
$font-family-sans-serif: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
$font-size-root: 100%;
$font-size-base: 15px;
$line-height-base: 1.6;
$border-radius: .55rem;
$headings-font-weight: 600;
$headings-color: #0F172A;

/*-- scss:rules --*/
body { -webkit-font-smoothing: antialiased; letter-spacing:-.003em; color:#334155; line-height:1.6; }

/* --- Échelle typographique (em = calée sur la base 15px) --- */
#quarto-document-content h1, .quarto-title h1.title { font-size:1.7em; }
#quarto-document-content h2 { font-size:1.35em; }
#quarto-document-content h3 { font-size:1.15em; }
#quarto-document-content h4 { font-size:1em; }
#quarto-document-content h5 { font-size:.9em; }
#quarto-document-content p,
#quarto-document-content li { font-size:1em; line-height:1.6; }
a { text-decoration: none; }
a:hover { text-decoration: underline; }

/* --- Bandeau d'accueil (hero) --- */
.hero-banner {
  background: linear-gradient(120deg, #1D4ED8 0%, #2563EB 52%, #3B82F6 100%);
  color:#fff; border-radius:16px; padding:2.6rem 2.2rem;
  margin:.4rem 0 1.8rem; box-shadow:0 12px 30px rgba(37,99,235,.22);
}
.hero-banner h1 { color:#fff; font-weight:800; letter-spacing:-.03em; margin:0 0 .4rem; font-size:2.15rem; }
.hero-banner p  { color:#dbe7ff; font-size:1.1rem; margin:0; max-width:62ch; }

/* --- Cartes de projet --- */
.grid-cards { display:grid; grid-template-columns:repeat(auto-fit, minmax(min(250px, 100%), 1fr)); gap:1rem; margin:1.1rem 0 2rem; }

/* --- Garde-fous responsive --- */
html, body { max-width:100%; overflow-x:hidden; }
#quarto-content img, #quarto-content pre, #quarto-content table { max-width:100%; }
.hero-banner { max-width:100%; }
@media (max-width: 767.98px) {
  .hero-banner { padding:1.8rem 1.4rem; }
  .hero-banner h1 { font-size:1.7rem; }
  .hero-banner p { font-size:1rem; }
}
.domain-card {
  display:flex; flex-direction:column; gap:.1rem; background:#fff;
  border:1px solid #E7EBF0; border-radius:14px; padding:1.25rem 1.25rem 1.1rem;
  box-shadow:0 1px 2px rgba(15,23,42,.04);
  transition:transform .15s ease, box-shadow .15s ease, border-color .15s ease;
  text-decoration:none !important; color:inherit;
}
.domain-card:hover { transform:translateY(-4px); box-shadow:0 14px 28px rgba(37,99,235,.14); border-color:#BFD3FB; }
.domain-card .ico { font-size:1.8rem; line-height:1; }
.domain-card h4 { margin:.55rem 0 .2rem; color:#0F172A; font-weight:700; letter-spacing:-.01em; }
.domain-card p  { margin:0; font-size:.9rem; color:#64748B; }
.domain-card .more { margin-top:.75rem; font-size:.82rem; font-weight:600; color:#2563EB; }

/* --- Fil d'Ariane --- */
.breadcrumb { font-size:.84rem; margin:0 0 .4rem; padding:0; background:transparent; }
.breadcrumb .breadcrumb-item a { color:#2563EB !important; font-weight:500; text-decoration:none; }
.breadcrumb .breadcrumb-item a:hover { text-decoration:underline; }
.breadcrumb .breadcrumb-item.active { color:#64748B; }
.breadcrumb .breadcrumb-item + .breadcrumb-item::before { content:"/"; color:#CBD5E1; padding:0 .5rem; }

/* --- Titres & tableaux --- */
h1 { font-weight:600; letter-spacing:-.02em; }
h2 { font-weight:600; letter-spacing:-.01em; border-bottom:1px solid #EEF2F7; padding-bottom:.3rem; margin-top:1.8rem; }
h3 { font-weight:600; }
table { font-size:.92rem; }
thead th { background:#F8FAFC; border-bottom:1px solid #E7EBF0 !important; }
tbody tr:hover { background:#F8FAFC; }

/* --- Code --- */
pre { border-radius:10px; border:1px solid #EEF2F7; }
pre code { font-size:.85rem; }
code:not(pre code) { color:#2563EB; background:#EEF4FE; padding:.05rem .35rem; border-radius:5px; font-size:.88em; }

.callout { border-radius:10px; }

/* --- Barre d'export (PDF / Word) --- */
.export-bar {
  display:flex; align-items:center; gap:.55rem; flex-wrap:wrap;
  background:#F8FAFC; border:1px solid #E7EBF0; border-radius:12px;
  padding:.65rem .9rem; margin:.1rem 0 1.5rem;
}
.export-bar .export-label { font-size:.9rem; color:#475569; margin-right:.15rem; }
.btn-export {
  display:inline-flex; align-items:center; gap:.35rem;
  font-size:.85rem; font-weight:600; text-decoration:none !important;
  padding:.36rem .8rem; border-radius:8px; border:1px solid transparent;
  transition:transform .12s ease, box-shadow .12s ease;
}
.btn-export i.bi { font-size:1.05em; line-height:1; }
.btn-export.pdf  { background:#FEECEC; color:#B91C1C; border-color:#F6C9C9; }
.btn-export.docx { background:#EAF1FE; color:#1D4ED8; border-color:#BFD3FB; }
.btn-export:hover { transform:translateY(-1px); box-shadow:0 4px 12px rgba(15,23,42,.12); text-decoration:none !important; }

/* --- Figures --- */
#quarto-document-content figure.figure { margin:1.6rem 0; }
#quarto-document-content .figure img,
#quarto-document-content figure img { display:block; margin:0 auto; max-width:100%; height:auto; }
#quarto-document-content figure figcaption,
#quarto-document-content .figure-caption { font-size:.82rem; color:#64748B; text-align:center; margin-top:.5rem; }

/* --- Badges de statut --- */
.badge-done  { background:#DCFCE7; color:#166534; padding:2px 9px; border-radius:999px; font-size:.78rem; font-weight:600; white-space:nowrap; }
.badge-wait  { background:#FEF9C3; color:#854D0E; padding:2px 9px; border-radius:999px; font-size:.78rem; font-weight:600; white-space:nowrap; }
.badge-block { background:#FFE4E6; color:#9F1239; padding:2px 9px; border-radius:999px; font-size:.78rem; font-weight:600; white-space:nowrap; }

/* ===================== SIDEBAR (SaaS moderne — façon Linear / Mintlify) ===== */
#quarto-sidebar, .sidebar.sidebar-navigation {
  background:#FCFDFE !important; border-right:1px solid #EAEEF3 !important;
}
#quarto-sidebar .sidebar-menu-container { padding:.35rem .7rem 1rem; }

/* --- Bloc de marque : pastille logo + nom + tagline --- */
#quarto-sidebar .sidebar-header {
  padding:.9rem .55rem .85rem; margin-bottom:.35rem;
  border-bottom:1px solid #EEF1F5;
}
#quarto-sidebar .sidebar-title { margin:0 !important; padding:0 !important; }
#quarto-sidebar .sidebar-title a {
  display:block; position:relative; padding:.05rem 0 .05rem 2.7rem;
  min-height:36px; line-height:1.12;
  color:#0F172A !important; font-weight:800 !important; font-size:1.08rem;
  letter-spacing:-.02em; text-decoration:none !important;
}
#quarto-sidebar .sidebar-title a::before {
  content:"@@LOGO@@"; position:absolute; left:0; top:50%; transform:translateY(-50%);
  width:34px; height:34px; border-radius:10px;
  background:linear-gradient(135deg,#3B82F6 0%,#1D4ED8 100%);
  color:#fff; font-weight:800; font-size:1.15rem;
  display:flex; align-items:center; justify-content:center;
  box-shadow:0 4px 10px rgba(37,99,235,.30);
}
#quarto-sidebar .sidebar-title a::after {
  content:"@@TAGLINE@@"; display:block; margin-top:.12rem;
  font-size:.62rem; font-weight:600; letter-spacing:.13em; text-transform:uppercase;
  color:#9AA6B6;
}

/* --- Étiquettes de section : micro-titres --- */
#quarto-sidebar .sidebar-item-section { margin-top:.85rem; }
#quarto-sidebar .sidebar-item-section:first-child { margin-top:.3rem; }
#quarto-sidebar .sidebar-item-section > .sidebar-item-container .menu-text,
#quarto-sidebar .sidebar-item-section > .sidebar-item-container > .sidebar-item-text {
  text-transform:uppercase; font-size:.67rem !important; letter-spacing:.09em;
  color:#98A4B4 !important; font-weight:700 !important;
}
#quarto-sidebar .sidebar-item-section > .sidebar-item-container:hover .menu-text {
  color:#64748B !important;
}

/* --- Liens --- */
#quarto-sidebar a.sidebar-item-text, #quarto-sidebar a.sidebar-link {
  color:#475569 !important; font-weight:500; font-size:.875rem;
  padding:.36rem .6rem; border-radius:7px; display:block; margin:1px 0;
  transition:background .12s ease, color .12s ease;
}
#quarto-sidebar ul.sidebar-section.depth1 {
  margin:.15rem 0 .1rem .7rem; padding-left:.45rem;
  border-left:1px solid #E9EDF2;
}
#quarto-sidebar ul.sidebar-section.depth1 a.sidebar-link { position:relative; }
#quarto-sidebar a.sidebar-link:hover {
  background:#F3F5F9 !important; color:#0F172A !important; text-decoration:none;
}
#quarto-sidebar ul.sidebar-section.depth1 a.sidebar-link.active {
  background:#EEF4FE !important; color:#1D4ED8 !important; font-weight:600;
}
#quarto-sidebar ul.sidebar-section.depth1 a.sidebar-link.active::before {
  content:""; position:absolute; left:-.46rem; top:.32rem; bottom:.32rem;
  width:2px; border-radius:2px; background:#2563EB;
}
#quarto-sidebar .sidebar-item-toggle i.bi, #quarto-sidebar i.bi {
  color:#B4BECC !important; font-size:.72rem; transition:transform .15s ease;
}
#quarto-sidebar .sidebar-item-toggle[aria-expanded="true"] i.bi { transform:rotate(90deg); }
'''
w("theme.scss", (_THEME.replace("@@LOGO@@", LOGO).replace("@@TAGLINE@@", TAGLINE)))

# ------------------------------------------------------------------ SCHEMAS (Graphviz dot)
# Sources versionnées : `_content/<domaine>/_diagrams/*.dot` -> SVG (web) + PNG (export)
# dans `site/<domaine>/img/<nom>.{svg,png}`. Mécanisme générique, aucun projet en dur.
def _render_dot(dot_path, out_dir, stem):
    out_dir.mkdir(parents=True, exist_ok=True)
    for fmt, extra in (("svg", []), ("png", ["-Gdpi=200"])):
        subprocess.run(["dot", f"-T{fmt}", *extra, str(dot_path),
                        "-o", str(out_dir / f"{stem}.{fmt}")], check=True)
    print("   schéma:", f"{out_dir.name}/{stem}.svg + .png")

for dot_src in sorted(CONTENT.rglob("_diagrams/*.dot")):
    dom = dot_src.relative_to(CONTENT).parts[0]
    _render_dot(dot_src, SITE / dom / "img", dot_src.stem)

# Images statiques éventuelles : `_content/<domaine>/img/*` copiées telles quelles.
for img_src in CONTENT.rglob("img/*"):
    if img_src.is_file():
        dest = SITE / img_src.relative_to(CONTENT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if img_src.resolve() != dest.resolve():
            dest.write_bytes(img_src.read_bytes())
            print("   image:", dest.relative_to(SITE).as_posix())

# ------------------------------------------------------------------ PAGES (depuis _content)
for src in sorted(CONTENT.rglob("*.qmd")):
    rel = src.relative_to(CONTENT).as_posix()
    w(rel, expand(src.read_text(encoding="utf-8")))

# ------------------------------------------------------------------ DOSSIER par domaine (PDF + Word)
# Un export par domaine : concatène ses sections en un document rendu en typst (PDF sans
# LaTeX) + docx. Non listé dans la sidebar (pas de sortie HTML). Rendu par publish.py.
def _strip_fm(s):
    m = re.match(r"^---\n.*?\n---\n?", s, re.S)
    title = ""
    if m:
        tm = re.search(r'^title:\s*"?(.*?)"?\s*$', m.group(0), re.M)
        title = tm.group(1) if tm else ""
        s = s[m.end():]
    return title, s.lstrip("\n")

def _dossier_header(dom):
    sub = TITLE + (f" · {TAGLINE}" if TAGLINE else "")
    return (f'''---
title: "{dom} — Dossier complet"
subtitle: "{sub}"
date: last-modified
date-format: "D MMMM YYYY"
lang: fr
code-overflow: wrap
format:
  typst:
    fig-format: png
    mainfont: "Calibri"
    toc: true
    toc-title: "Sommaire"
    papersize: a4
    margin:
      left: 1.8cm
      right: 1.8cm
      top: 2cm
      bottom: 2cm
    include-in-header:
      text: |
        #show raw: set text(size: 8pt)
  docx:
    fig-format: png
    toc: true
    toc-title: "Sommaire"
    reference-doc: "../_assets/reference.docx"
execute:
  echo: false
  warning: false
---
''')

for dom in domains():
    sections = []
    for sec in domain_sections(dom):
        s = CONTENT / dom / f"{sec}.qmd"
        if not s.exists():
            continue
        raw = re.sub(r"@@EXPORT:[A-Za-z0-9_-]+@@\n?", "", s.read_text(encoding="utf-8"))
        title, body = _strip_fm(raw)
        body = expand(body)
        # export : schémas SVG (web) -> PNG (universel Word/PDF)
        body = re.sub(r"(img/[^)\s]+)\.svg", r"\1.png", body)
        # retirer les conteneurs de débordement web `::: {.column-*}` (texte étroit en typst)
        body = re.sub(r":::\s*\{\.column-[^}]*\}\s*\n(.*?)\n:::[ \t]*\n", r"\1\n", body, flags=re.S)
        # dérouler les callouts repliables (code) : cadre casse mal à la pagination
        body = re.sub(
            r":::\s*\{\.callout-[^}]*collapse=\"true\"[^}]*\}\s*\n(?:#+[^\n]*\n)?\s*(.*?)\n:::[ \t]*\n",
            r"\1\n", body, flags=re.S)
        sections.append(f"# {title}\n\n{body}")
    if sections:
        doc = _dossier_header(dom) + "\n\n{{< pagebreak >}}\n\n".join(sections) + "\n"
        w(f"{dom}/dossier.qmd", doc)

print(f"\nSite « {TITLE} » (preset {PRESET}) généré dans : {SITE}  — domaines : {', '.join(domains()) or '(aucun)'}")
