$ErrorActionPreference = 'Stop'
$workspaceRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$workspacePrefix = $workspaceRoot.TrimEnd('\') + '\'
$expected = @('.thumbnails', '.thumbnails\fail', '.thumbnails\large', '.thumbnails\fail\blender')
$removed = @()
$skipped = @()
foreach ($candidate in @(Get-ChildItem -LiteralPath $workspaceRoot -Directory -Force)) {
    if ($candidate.Name -notmatch '[^\x00-\x7F]') { continue }
    $decoded = [Text.Encoding]::ASCII.GetString([Text.Encoding]::Unicode.GetBytes($candidate.Name)).Split([char]0)[0]
    if ($decoded -ne 'blend' -and $decoded -notmatch '[0-9a-f]+\.png$') { continue }
    $target = [IO.Path]::GetFullPath($candidate.FullName)
    if (-not $target.StartsWith($workspacePrefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Target escapes workspace' }
    if ([IO.Path]::GetDirectoryName($target) -ne $workspaceRoot) { throw 'Not a direct workspace child' }
    $queue = [Collections.Generic.Queue[IO.DirectoryInfo]]::new()
    $queue.Enqueue($candidate)
    $nodes = @()
    $valid = $true
    while ($queue.Count -gt 0 -and $valid) {
        $node = $queue.Dequeue()
        if ($node.Attributes -band [IO.FileAttributes]::ReparsePoint) { $valid = $false; break }
        $absolute = [IO.Path]::GetFullPath($node.FullName)
        if ($absolute -ne $target -and -not $absolute.StartsWith($target + '\', [StringComparison]::OrdinalIgnoreCase)) {
            throw 'Child escapes target'
        }
        $nodes += $node
        foreach ($child in @(Get-ChildItem -LiteralPath $absolute -Force)) {
            if (-not $child.PSIsContainer -or ($child.Attributes -band [IO.FileAttributes]::ReparsePoint)) { $valid = $false; break }
            $relative = $child.FullName.Substring($target.Length + 1)
            if ($relative -notin $expected) { $valid = $false; break }
            $queue.Enqueue($child)
        }
    }
    if (-not $valid -or $nodes.Count -ne 5) { $skipped += $candidate.Name; continue }
    try {
        # Nonrecursive deletion is atomic with respect to emptiness: a file
        # created concurrently causes a failure instead of being removed.
        foreach ($node in @($nodes | Sort-Object { $_.FullName.Length } -Descending)) {
            [IO.Directory]::Delete($node.FullName, $false)
        }
        $removed += $candidate.Name
    } catch {
        $skipped += $candidate.Name
    }
}
$report = [ordered]@{removed_top_level_directories=$removed.Count; skipped=$skipped; deleted_files=0}
$report | ConvertTo-Json -Depth 3
