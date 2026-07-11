param(
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
$repository = "haoran3160-afk/VibeSpec_Gate-skill"
$description = "Agent-native launch security review for vibe-coded apps, SaaS, and AI tools."
$homepage = "https://github.com/haoran3160-afk/VibeSpec_Gate-skill#readme"
$topics = @(
    "agent-security",
    "ai-security",
    "appsec",
    "coding-agents",
    "llm-security",
    "security",
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

gh auth status | Out-Null
gh repo edit $repository --description $description --homepage $homepage
foreach ($topic in $topics) {
    gh repo edit $repository --add-topic $topic
}

Write-Output "PASS GitHub repository metadata configured for $repository"
