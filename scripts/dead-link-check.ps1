$root = 'C:\Users\rdyal\Apulu Universe'
$excluded = @('paperclip','node_modules','.git','.claude')
$mdFiles = Get-ChildItem -Path $root -Recurse -Filter '*.md' -File | Where-Object {
    $rel = $_.FullName.Substring($root.Length).TrimStart('\')
    -not ($excluded | Where-Object { $rel.StartsWith($_) })
}

$deadLinks = @()
foreach ($f in $mdFiles) {
    $content = Get-Content -Path $f.FullName -Raw
    $wikilinks = [regex]::Matches($content, '\[\[([^\]\|]+)(?:\|[^\]]*)?\]\]') | ForEach-Object { $_.Groups[1].Value }
    foreach ($link in $wikilinks) {
        $linkFile = if ($link -match '\.md$') { $link } else { "$link.md" }
        $dir = Split-Path -Parent $f.FullName
        $candidate = Join-Path $dir $linkFile
        if (-not (Test-Path $candidate)) {
            $bareName = Split-Path -Leaf $linkFile
            $found = Get-ChildItem -Path $root -Recurse -Filter $bareName -ErrorAction SilentlyContinue | Where-Object {
                $rel = $_.FullName.Substring($root.Length).TrimStart('\')
                -not ($excluded | Where-Object { $rel.StartsWith($_) })
            } | Select-Object -First 1
            if (-not $found) {
                $deadLinks += [PSCustomObject]@{ File = $f.FullName.Substring($root.Length).TrimStart('\'); Link = $link }
            }
        }
    }
}

if ($deadLinks.Count -eq 0) {
    Write-Host "No dead links found."
} else {
    Write-Host ("Dead links: " + $deadLinks.Count)
    $deadLinks | Format-Table -AutoSize
}
