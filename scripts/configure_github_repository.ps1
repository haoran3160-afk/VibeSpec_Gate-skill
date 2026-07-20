param(
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$repository = "haoran3160-afk/VibeSpec_Gate-skill"
$description = "Launch-blocking security review Skill for vibe-coded apps, AI agents, MCP tools, and Electron products."
$homepage = "https://github.com/haoran3160-afk/VibeSpec_Gate-skill#readme"
$topics = @(
    "agent-security",
    "ai-security",
    "application-security",
    "codex-skill",
    "electron-security",
    "mcp-security",
    "security-review",
    "supabase",
    "vibe-coding"
)

if (-not $Apply) {
    Write-Output "Dry run. Re-run with -Apply after reviewing these settings."
    Write-Output "Repository: $repository"
    Write-Output "Description: $description"
    Write-Output "Homepage: $homepage"
    Write-Output "Topics: $($topics -join ', ')"
    exit 0
}

& gh auth status | Out-Null
if ($LASTEXITCODE -ne 0) { throw "GitHub CLI authentication failed" }

& gh repo edit $repository --description $description --homepage $homepage
if ($LASTEXITCODE -ne 0) { throw "Failed to update GitHub repository description or homepage" }

$topicPayload = @{ names = $topics } | ConvertTo-Json -Compress
$topicPayload | & gh api --method PUT -H "Accept: application/vnd.github+json" "repos/$repository/topics" --input - | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Failed to replace GitHub repository topics" }

Write-Output "PASS GitHub repository metadata configured for $repository"
