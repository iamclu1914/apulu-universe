function Prepend-Frontmatter($path, $fmLines) {
    if (-not (Test-Path $path)) {
        Write-Host ("MISSING: " + $path)
        return
    }
    $content = Get-Content -Path $path -Raw
    if ($null -eq $content) { $content = '' }
    if ($content -match '^---\s*\r?\n') {
        Write-Host ("Skip (already has frontmatter): " + (Split-Path -Leaf $path))
        return
    }
    $fm = "---`n" + ($fmLines -join "`n") + "`n---`n`n"
    Set-Content -Path $path -Value ($fm + $content) -NoNewline
    Write-Host ("Added FM: " + (Split-Path -Leaf $path))
}

# Research tickets
Prepend-Frontmatter 'C:\Users\rdyal\Apulu Universe\research\vawn\APU-107-mix-engine-enhancement-research.md' @('ticket: APU-107','type: research','status: closed','updated: 2026-04-14')
Prepend-Frontmatter 'C:\Users\rdyal\Apulu Universe\research\vawn\APU-108-hip-hop-mix-ai-prompting-research.md' @('ticket: APU-108','type: research','status: closed','updated: 2026-04-14')
Prepend-Frontmatter 'C:\Users\rdyal\Apulu Universe\research\vawn\2026-04-12-mix-engine-pro-alignment.md' @('type: research','status: closed','updated: 2026-04-12')
Prepend-Frontmatter 'C:\Users\rdyal\Apulu Universe\research\vawn\2026-04-10-higgsfield-seedance-best-practices.md' @('type: research','status: closed','updated: 2026-04-10')

# Topic hubs
function Prepend-HubFrontmatter($path, $topic) {
    if (-not (Test-Path $path)) {
        Write-Host ("MISSING: " + $path)
        return
    }
    $content = Get-Content -Path $path -Raw
    if ($null -eq $content) { $content = '' }
    if ($content -match '^---\s*\r?\n') {
        Write-Host ("Skip (already has frontmatter): " + (Split-Path -Leaf $path))
        return
    }
    $fm = "---`ntype: hub`ntopic: $topic`n---`n`n"
    Set-Content -Path $path -Value ($fm + $content) -NoNewline
    Write-Host ("Added FM [hub/" + $topic + "]: " + (Split-Path -Leaf $path))
}

Prepend-HubFrontmatter 'C:\Users\rdyal\Apulu Universe\wiki\_master-index.md' 'wiki-root'
Prepend-HubFrontmatter 'C:\Users\rdyal\Apulu Universe\wiki\ai-filmmaking\_index.md' 'ai-filmmaking'
Prepend-HubFrontmatter 'C:\Users\rdyal\Apulu Universe\wiki\apulu-prompt-generator\_index.md' 'apulu-prompt-generator'
Prepend-HubFrontmatter 'C:\Users\rdyal\Apulu Universe\wiki\cross-topic\_index.md' 'cross-topic'
Prepend-HubFrontmatter 'C:\Users\rdyal\Apulu Universe\wiki\design-engineering\_index.md' 'design-engineering'
Prepend-HubFrontmatter 'C:\Users\rdyal\Apulu Universe\wiki\vawn-mix-engine\_index.md' 'vawn-mix-engine'
Prepend-HubFrontmatter 'C:\Users\rdyal\Apulu Universe\wiki\vawn-project\_index.md' 'vawn-project'
