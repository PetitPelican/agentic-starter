param(
  [string]$ProjectRoot = ".",
  [string]$TemplateRoot = "",
  [string]$TemplateRepo = "https://github.com/PetitPelican/agentic-starter.git",
  [switch]$Apply,
  [switch]$RemoveLegacyMemory
)

$ErrorActionPreference = "Stop"
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$Changes = New-Object System.Collections.Generic.List[string]
$Skipped = New-Object System.Collections.Generic.List[string]
$Conflicts = New-Object System.Collections.Generic.List[string]

function Resolve-FullPath([string]$Path) {
  if (Test-Path -LiteralPath $Path) {
    return (Resolve-Path -LiteralPath $Path).Path
  }
  return [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $Path))
}

function Add-Change([string]$Message) { $script:Changes.Add($Message) | Out-Null }
function Add-Skip([string]$Message) { $script:Skipped.Add($Message) | Out-Null }
function Add-Conflict([string]$Message) { $script:Conflicts.Add($Message) | Out-Null }

function Ensure-Directory([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) {
    Add-Change "Créer dossier $Path"
    if ($Apply) { New-Item -ItemType Directory -Path $Path -Force | Out-Null }
  }
}

function Copy-FileIfMissing([string]$Source, [string]$Destination) {
  if (-not (Test-Path -LiteralPath $Source)) {
    Add-Skip "Template absent: $Source"
    return
  }
  if (Test-Path -LiteralPath $Destination) {
    Add-Skip "Existe déjà, non écrasé: $Destination"
    return
  }
  Add-Change "Copier fichier $Destination"
  if ($Apply) {
    Ensure-Directory (Split-Path -Parent $Destination)
    Copy-Item -LiteralPath $Source -Destination $Destination
  }
}

function Copy-DirectoryIfMissing([string]$Source, [string]$Destination) {
  if (-not (Test-Path -LiteralPath $Source)) {
    Add-Skip "Template absent: $Source"
    return
  }
  if (Test-Path -LiteralPath $Destination) {
    Add-Skip "Existe déjà, non écrasé: $Destination"
    return
  }
  Add-Change "Copier dossier $Destination"
  if ($Apply) {
    Ensure-Directory (Split-Path -Parent $Destination)
    Copy-Item -LiteralPath $Source -Destination $Destination -Recurse
  }
}

function Replace-InFile([string]$Path, [hashtable]$Replacements) {
  if (-not (Test-Path -LiteralPath $Path)) { return }
  $Original = [System.IO.File]::ReadAllText($Path, $Utf8NoBom)
  $Updated = $Original
  foreach ($Key in $Replacements.Keys) {
    $Updated = $Updated.Replace($Key, $Replacements[$Key])
  }
  if ($Updated -ne $Original) {
    Add-Change "Mettre à jour références dans $Path"
    if ($Apply) { [System.IO.File]::WriteAllText($Path, $Updated, $Utf8NoBom) }
  }
}

function Get-TemplateRoot {
  if ($TemplateRoot -ne "") {
    $Resolved = Resolve-FullPath $TemplateRoot
    if (-not (Test-Path -LiteralPath (Join-Path $Resolved ".codex"))) {
      throw "TemplateRoot ne contient pas .codex/: $Resolved"
    }
    return $Resolved
  }

  $ScriptPath = $PSCommandPath
  $Candidate = Split-Path -Parent $ScriptPath
  for ($i = 0; $i -lt 8; $i++) {
    if ((Test-Path -LiteralPath (Join-Path $Candidate ".codex")) -and
        (Test-Path -LiteralPath (Join-Path $Candidate "AGENTS.md"))) {
      return $Candidate
    }
    $Parent = Split-Path -Parent $Candidate
    if ($Parent -eq $Candidate) { break }
    $Candidate = $Parent
  }

  $TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("agentic-starter-" + [guid]::NewGuid().ToString("N"))
  Add-Change "Cloner template agentic-starter vers $TempRoot"
  git clone --depth 1 $TemplateRepo $TempRoot | Out-Null
  return $TempRoot
}

function New-AgentsFromClaude([string]$ClaudePath, [string]$AgentsPath) {
  if (-not (Test-Path -LiteralPath $ClaudePath) -or (Test-Path -LiteralPath $AgentsPath)) { return $false }
  $Text = [System.IO.File]::ReadAllText($ClaudePath, $Utf8NoBom)
  $Text = $Text.Replace("Claude Code Context", "Codex CLI Context")
  $Text = $Text.Replace("Claude doit appliquer", "Codex doit appliquer")
  $Text = $Text.Replace("tu lis `"[PROJECT_NAME]`" dans ce fichier", "tu lis `"[PROJECT_NAME]`" dans ce fichier")
  $Text = $Text.Replace(".claude/memory/", ".memory/")
  $Text = $Text.Replace(".claude/memory", ".memory")
  Add-Change "Créer AGENTS.md depuis CLAUDE.md personnalisé"
  if ($Apply) { [System.IO.File]::WriteAllText($AgentsPath, $Text, $Utf8NoBom) }
  return $true
}

$Project = Resolve-FullPath $ProjectRoot
if (-not (Test-Path -LiteralPath $Project)) {
  throw "ProjectRoot introuvable: $Project"
}

$Template = Get-TemplateRoot

Write-Host "Agentic upgrade"
Write-Host "ProjectRoot : $Project"
Write-Host "TemplateRoot: $Template"
Write-Host "Mode        : $(if ($Apply) { 'APPLY' } else { 'DRY-RUN' })"
Write-Host ""

$ClaudeMemory = Join-Path $Project ".claude\memory"
$SharedMemory = Join-Path $Project ".memory"

if ((Test-Path -LiteralPath $ClaudeMemory) -and -not (Test-Path -LiteralPath $SharedMemory)) {
  Copy-DirectoryIfMissing $ClaudeMemory $SharedMemory
} elseif ((Test-Path -LiteralPath $ClaudeMemory) -and (Test-Path -LiteralPath $SharedMemory)) {
  Add-Conflict ".claude/memory et .memory existent déjà; fusion manuelle requise."
} elseif (-not (Test-Path -LiteralPath $SharedMemory)) {
  Copy-DirectoryIfMissing (Join-Path $Template ".memory") $SharedMemory
}

Copy-DirectoryIfMissing (Join-Path $Template ".codex") (Join-Path $Project ".codex")
Copy-DirectoryIfMissing (Join-Path $Template ".claude\skills\agentic-upgrade") (Join-Path $Project ".claude\skills\agentic-upgrade")
Copy-DirectoryIfMissing (Join-Path $Template ".codex\skills\agentic-upgrade") (Join-Path $Project ".codex\skills\agentic-upgrade")
Copy-FileIfMissing (Join-Path $Template ".mcp.json.example") (Join-Path $Project ".mcp.json.example")

$AgentsPath = Join-Path $Project "AGENTS.md"
if (-not (New-AgentsFromClaude (Join-Path $Project "CLAUDE.md") $AgentsPath)) {
  Copy-FileIfMissing (Join-Path $Template "AGENTS.md") $AgentsPath
}

$Replacements = @{
  "claude-starter" = "agentic-starter"
  ".claude/memory/" = ".memory/"
  ".claude/memory" = ".memory"
  "Claude Code Context" = "Codex CLI Context"
  "Claude doit appliquer" = "Codex doit appliquer"
}

$Targets = @(
  "README.md",
  "AGENTS.md",
  "CLAUDE.md",
  ".claude\skills\memory-update\SKILL.md",
  ".codex\skills\memory-update\SKILL.md",
  ".claude\skills\project-init\SKILL.md",
  ".codex\skills\project-init\SKILL.md"
)

foreach ($Relative in $Targets) {
  $Path = Join-Path $Project $Relative
  if ($Relative -eq "CLAUDE.md") {
    Replace-InFile $Path @{
      "claude-starter" = "agentic-starter"
      ".claude/memory/" = ".memory/"
      ".claude/memory" = ".memory"
    }
  } else {
    Replace-InFile $Path $Replacements
  }
}

$Gitignore = Join-Path $Project ".gitignore"
if (Test-Path -LiteralPath $Gitignore) {
  $Text = [System.IO.File]::ReadAllText($Gitignore, $Utf8NoBom)
  if ($Text -notmatch "(?m)^\.codex/settings\.local\.json$") {
    Add-Change "Ajouter .codex/settings.local.json à .gitignore"
    if ($Apply) {
      $Prefix = if ($Text.EndsWith("`n")) { "" } else { "`n" }
      [System.IO.File]::WriteAllText($Gitignore, $Text + $Prefix + ".codex/settings.local.json`n", $Utf8NoBom)
    }
  }
} else {
  Add-Change "Créer .gitignore"
  if ($Apply) {
    [System.IO.File]::WriteAllText($Gitignore, ".claude/settings.local.json`n.codex/settings.local.json`n", $Utf8NoBom)
  }
}

if ($RemoveLegacyMemory -and (Test-Path -LiteralPath $ClaudeMemory)) {
  if (Test-Path -LiteralPath $SharedMemory) {
    Add-Change "Supprimer ancien dossier .claude/memory"
    if ($Apply) { Remove-Item -LiteralPath $ClaudeMemory -Recurse -Force }
  } else {
    Add-Conflict "Impossible de supprimer .claude/memory: .memory n'existe pas."
  }
} elseif (Test-Path -LiteralPath $ClaudeMemory) {
  Add-Skip "Ancien dossier .claude/memory conservé. Ajouter -RemoveLegacyMemory pour le supprimer après migration."
}

Write-Host "Changements:"
if ($Changes.Count -eq 0) { Write-Host "- Aucun" } else { $Changes | ForEach-Object { Write-Host "- $_" } }
Write-Host ""
Write-Host "Ignorés:"
if ($Skipped.Count -eq 0) { Write-Host "- Aucun" } else { $Skipped | ForEach-Object { Write-Host "- $_" } }
Write-Host ""
Write-Host "Conflits:"
if ($Conflicts.Count -eq 0) { Write-Host "- Aucun" } else { $Conflicts | ForEach-Object { Write-Host "- $_" } }

if (-not $Apply) {
  Write-Host ""
  Write-Host "Dry-run seulement. Relancer avec -Apply pour appliquer."
}
