# Resynchronise un projet DÉJÀ agentic sur la dernière version d'agentic-starter.
# Partie MÉCANIQUE seulement (fichiers starter-owned) : mirror des skills, swap du
# moteur de site, suppression de ce que le starter a retiré, nettoyage des renommages.
# La partie JUGEMENT (réconcilier CLAUDE.md/AGENTS.md, migrer la mémoire, générer
# site.config.yml) est pilotée par le SKILL.md, PAS par ce script.
#
# Dry-run par défaut. Ajouter -Apply pour écrire.
param(
  [string]$ProjectRoot = ".",
  [string]$TemplateRoot = "",
  [string]$TemplateRepo = "https://github.com/PetitPelican/agentic-starter.git",
  [switch]$Apply
)

$ErrorActionPreference = "Stop"
$Changes = New-Object System.Collections.Generic.List[string]
$Skipped = New-Object System.Collections.Generic.List[string]
$Manual  = New-Object System.Collections.Generic.List[string]

function Add-Change([string]$m) { $script:Changes.Add($m) | Out-Null }
function Add-Skip([string]$m)   { $script:Skipped.Add($m) | Out-Null }
function Add-Manual([string]$m) { $script:Manual.Add($m)  | Out-Null }

function Resolve-FullPath([string]$Path) {
  if (Test-Path -LiteralPath $Path) { return (Resolve-Path -LiteralPath $Path).Path }
  return [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $Path))
}
function Ensure-Directory([string]$Path) {
  if ($Path -and -not (Test-Path -LiteralPath $Path)) {
    if ($Apply) { New-Item -ItemType Directory -Path $Path -Force | Out-Null }
  }
}
function Files-Differ([string]$a, [string]$b) {
  if (-not (Test-Path -LiteralPath $b)) { return $true }
  $ba = [System.IO.File]::ReadAllBytes($a)
  $bb = [System.IO.File]::ReadAllBytes($b)
  # Binaire (contient un octet nul, ex. reference.docx) -> comparaison brute par hash.
  if (($ba -contains 0) -or ($bb -contains 0)) {
    return (Get-FileHash -LiteralPath $a).Hash -ne (Get-FileHash -LiteralPath $b).Hash
  }
  # Texte -> normaliser BOM + fins de ligne (CRLF/CR -> LF) avant de comparer, pour ne pas
  # signaler comme divergents des fichiers identiques au contenu (Windows CRLF vs starter LF).
  $ta = [System.Text.Encoding]::UTF8.GetString($ba).TrimStart([char]0xFEFF) -replace "`r`n", "`n" -replace "`r", "`n"
  $tb = [System.Text.Encoding]::UTF8.GetString($bb).TrimStart([char]0xFEFF) -replace "`r`n", "`n" -replace "`r", "`n"
  return $ta -ne $tb
}

# --- ownership manifest -------------------------------------------------------
# Fichiers 100% starter-owned : écrasés vers la version du template.
# Moteur / assets de site (starter-owned) : NON écrasés par la passe mécanique.
# Contrairement aux skills, écraser le moteur seul casse le build tant que
# site.config.yml n'est pas généré -> on se contente de SIGNALER la divergence,
# la mise à jour se fait dans le bloc « site » guidé (swap + config + vérif build).
$SiteEngine = @(
  "site/build_site.py",
  "site/publish.py",
  "site/requirements.txt",
  "site/.gitignore",
  "site/_assets/reference.docx"
)
# Chemins retirés ou renommés en amont : supprimés du projet s'ils existent.
$RemovePaths = @(
  ".claude/agents", ".codex/agents",
  ".claude/skills/agent-init", ".codex/skills/agent-init",
  ".claude/skills/doc-site", ".codex/skills/doc-site",
  ".claude/skills/project-upgrade", ".codex/skills/project-upgrade"
)
# Fichiers project-owned rappelés à l'utilisateur : jamais touchés par ce script.
$ProjectOwned = @(
  "CLAUDE.md / AGENTS.md (rôle, règles) -> section Mémoire + règles à réconcilier à la main",
  ".memory/** (contenu) -> migration de taxonomie via le SKILL, pas ce script",
  "site/site.config.yml, site/_content/** -> conservés ; générer la config si absente",
  ".env*, .mcp.json, settings.local.json -> conservés"
)

function Get-TemplateRoot {
  if ($TemplateRoot -ne "") {
    $r = Resolve-FullPath $TemplateRoot
    if (-not (Test-Path -LiteralPath (Join-Path $r ".codex"))) { throw "TemplateRoot sans .codex/: $r" }
    return $r
  }
  $c = Split-Path -Parent $PSCommandPath
  for ($i = 0; $i -lt 8; $i++) {
    if ((Test-Path -LiteralPath (Join-Path $c ".codex")) -and (Test-Path -LiteralPath (Join-Path $c "AGENTS.md"))) { return $c }
    $p = Split-Path -Parent $c
    if ($p -eq $c) { break }
    $c = $p
  }
  $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("agentic-starter-" + [guid]::NewGuid().ToString("N"))
  Add-Change "Cloner template vers $tmp"
  git clone --depth 1 $TemplateRepo $tmp | Out-Null
  return $tmp
}

# Mirror d'un dossier 100% starter-owned : ajoute/écrase les fichiers du template,
# supprime dans le projet ceux qui n'existent plus en amont. N'affecte que ce dossier.
function Mirror-Dir([string]$Source, [string]$Destination) {
  if (-not (Test-Path -LiteralPath $Source)) { return }
  # Base via Get-Item : même forme canonique que le FullName de Get-ChildItem
  # (8.3 détendu). Resolve-Path garderait la forme courte -> Substring décalé.
  $src = (Get-Item -LiteralPath $Source).FullName.TrimEnd('\','/')
  # État de la destination AVANT copie (on ne supprimera jamais un fichier fraîchement copié).
  $destBefore = @{}
  if (Test-Path -LiteralPath $Destination) {
    $dst = (Get-Item -LiteralPath $Destination).FullName.TrimEnd('\','/')
    foreach ($f in Get-ChildItem -Recurse -File -LiteralPath $dst) {
      $rel = $f.FullName.Substring($dst.Length).TrimStart('\','/')
      $destBefore[$rel.ToLowerInvariant()] = $f.FullName
    }
  }
  # Copie / mise à jour depuis la source ; mémorise les rel présents en source.
  $srcRel = @{}
  foreach ($f in Get-ChildItem -Recurse -File -LiteralPath $src) {
    $rel = $f.FullName.Substring($src.Length).TrimStart('\','/')
    $srcRel[$rel.ToLowerInvariant()] = $true
    $dest = Join-Path $Destination $rel
    if (Files-Differ $f.FullName $dest) {
      Add-Change "Sync $dest"
      if ($Apply) { Ensure-Directory (Split-Path -Parent $dest); Copy-Item -LiteralPath $f.FullName -Destination $dest -Force }
    }
  }
  # Supprime uniquement ce qui existait AVANT et n'est plus dans la source.
  foreach ($rel in $destBefore.Keys) {
    if (-not $srcRel.ContainsKey($rel)) {
      Add-Change "Supprimer obsolète $($destBefore[$rel])"
      if ($Apply) { Remove-Item -LiteralPath $destBefore[$rel] -Force }
    }
  }
}

$Project  = Resolve-FullPath $ProjectRoot
if (-not (Test-Path -LiteralPath $Project)) { throw "ProjectRoot introuvable: $Project" }
$Template = Get-TemplateRoot

Write-Host "Agentic sync"
Write-Host "ProjectRoot : $Project"
Write-Host "TemplateRoot: $Template"
Write-Host "Mode        : $(if ($Apply) { 'APPLY' } else { 'DRY-RUN' })"
Write-Host ""

# 1. Mirror des skills, skill par skill (préserve d'éventuels skills propres au projet).
foreach ($harness in @(".claude", ".codex")) {
  $tplSkills = Join-Path $Template "$harness/skills"
  if (-not (Test-Path -LiteralPath $tplSkills)) { continue }
  foreach ($skill in Get-ChildItem -Directory -LiteralPath $tplSkills) {
    Mirror-Dir $skill.FullName (Join-Path $Project "$harness/skills/$($skill.Name)")
  }
}

# 2. Moteur de site : jamais écrasé ici. On signale seulement s'il diffère du template,
#    pour le traiter dans le bloc « site » guidé (swap moteur + site.config.yml + vérif build).
foreach ($rel in $SiteEngine) {
  $src = Join-Path $Template $rel
  $dst = Join-Path $Project $rel
  if (-not (Test-Path -LiteralPath $src)) { continue }
  if (-not (Test-Path -LiteralPath $dst)) { continue }   # absent -> pas de site, /publish-docs init
  if (Files-Differ $src $dst) { Add-Manual "site: $rel diffère du template -> migration guidée (bloc site du SKILL), NON écrasé automatiquement" }
}

# 3. Suppression de ce que le starter a retiré / renommé.
foreach ($rel in $RemovePaths) {
  $p = Join-Path $Project $rel
  if (Test-Path -LiteralPath $p) {
    Add-Change "Supprimer $rel (retiré/renommé en amont)"
    if ($Apply) { Remove-Item -LiteralPath $p -Recurse -Force }
  }
}

# 4. Détection (read-only) d'une taxonomie mémoire ancienne -> remonte le CHOIX à faire.
#    Ne lit que les NOMS de fichiers, ne touche à rien.
$LegacyMem = @("business","clients","overview","hosting","todo","troubleshooting",
               "db_architecture","ingestion_plan","lineage_old_db","pbi_measures","pbi_reports_specs")
$MemDir = Join-Path $Project ".memory"
if (Test-Path -LiteralPath $MemDir) {
  $found = @()
  foreach ($f in Get-ChildItem -Recurse -File -LiteralPath $MemDir -Filter *.md) {
    $stem = [System.IO.Path]::GetFileNameWithoutExtension($f.Name).ToLowerInvariant()
    if ($LegacyMem -contains $stem) { $found += $f.Name }
  }
  if ($found.Count -gt 0) {
    Add-Manual ("MÉMOIRE : taxonomie ancienne détectée (" + (($found | Select-Object -Unique) -join ", ") +
                ") -> CHOIX requis : (A) garder telle quelle, ou (B) migrer vers charter/architecture/rules/" +
                "decisions/state/operations (celle du site). Voir étape 4 du SKILL. Rien migré d'office.")
  }
}

# 5. Rappels : zones à réconcilier à la main (pilotées par le SKILL, hors script).
foreach ($m in $ProjectOwned) { Add-Manual $m }

Write-Host "Changements (mécaniques):"
if ($Changes.Count -eq 0) { Write-Host "- Aucun" } else { $Changes | ForEach-Object { Write-Host "- $_" } }
Write-Host ""
Write-Host "Ignorés:"
if ($Skipped.Count -eq 0) { Write-Host "- Aucun" } else { $Skipped | ForEach-Object { Write-Host "- $_" } }
Write-Host ""
Write-Host "À réconcilier à la main (project-owned - voir le SKILL agentic-sync):"
$Manual | ForEach-Object { Write-Host "- $_" }

if (-not $Apply) {
  Write-Host ""
  Write-Host "Dry-run seulement. Relancer avec -Apply pour appliquer la partie mécanique."
}
