# Idempotent: skips files that already start with frontmatter.
# Covers journals/vawn/{briefings,health,discovery} with appropriate type values.
$specs = @(
    @{ Dir = 'C:\Users\rdyal\Apulu Universe\journals\vawn\briefings'; Pattern = '^(\d{4}-\d{2}-\d{2})-daily-briefing\.md$'; Type = 'daily-briefing' },
    @{ Dir = 'C:\Users\rdyal\Apulu Universe\journals\vawn\health'; Pattern = '^(\d{4}-\d{2}-\d{2})-health\.md$'; Type = 'health' },
    @{ Dir = 'C:\Users\rdyal\Apulu Universe\journals\vawn\discovery'; Pattern = '^(\d{4}-\d{2}-\d{2})-discovery-brief\.md$'; Type = 'discovery' }
)
foreach ($spec in $specs) {
    if (-not (Test-Path $spec.Dir)) { continue }
    Get-ChildItem -Path $spec.Dir -Filter '*.md' | ForEach-Object {
        $content = Get-Content -Path $_.FullName -Raw
        if ($content -match '^---\s*\r?\n') {
            Write-Host ("Skip (already has frontmatter): " + $_.Name)
            return
        }
        if ($_.Name -match $spec.Pattern) {
            $date = $matches[1]
            $fm = "---`ndate: $date`ntype: $($spec.Type)`nbriefing-for: vawn`n---`n`n"
            Set-Content -Path $_.FullName -Value ($fm + $content) -NoNewline
            Write-Host ("Added FM [" + $spec.Type + "]: " + $_.Name)
        } else {
            Write-Host ("Pattern mismatch (not touching): " + $_.Name)
        }
    }
}
