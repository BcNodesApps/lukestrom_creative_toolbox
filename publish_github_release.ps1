$ErrorActionPreference = "Stop"

$Repo = "BcNodesApps/lukestrom_creative_toolbox"
$ProjectDir = "C:\appdevelopment\toolbox\codex"
$SourceFile = Join-Path $ProjectDir "creative_toolbox.py"
$DistDir = Join-Path $ProjectDir "dist"
$ExeFile = Join-Path $DistDir "Creative Toolbox.exe"

Write-Host ""
Write-Host "LukeStrom Creative Tool release publisher"
Write-Host "-----------------------------------------"

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI is not available. Install it with: winget install --id GitHub.cli"
}

if (-not (Test-Path -LiteralPath $SourceFile)) {
    throw "Could not find source file: $SourceFile"
}

if (-not (Test-Path -LiteralPath $ExeFile)) {
    throw "Could not find EXE. Build it first: $ExeFile"
}

$Source = Get-Content -LiteralPath $SourceFile -Raw
$VersionMatch = [regex]::Match($Source, 'APP_VERSION\s*=\s*"([^"]+)"')
if (-not $VersionMatch.Success) {
    throw "Could not read APP_VERSION from creative_toolbox.py"
}

$Version = $VersionMatch.Groups[1].Value.Trim()
$DateStamp = Get-Date -Format "yyyy-MM-dd HH:mm"
$ReleaseTitle = "LukeStrom Creative Tool $Version"
$SafeVersion = $Version -replace '[^\w\.-]', '_'
$AssetName = "Creative.Toolbox.$SafeVersion.exe"
$ReleaseNotesPath = Join-Path $env:TEMP "lukestrom_release_notes_$Version.md"
$UploadExe = Join-Path $DistDir $AssetName

$CurrentHeader = "## $Version"
$Notes = "LukeStrom Creative Tool $Version`r`n`r`nAutomated release created on $DateStamp.`r`n"
$HeaderIndex = $Source.IndexOf($CurrentHeader)
if ($HeaderIndex -ge 0) {
    $Rest = $Source.Substring($HeaderIndex)
    $NextHeaderMatch = [regex]::Match($Rest.Substring($CurrentHeader.Length), '(?m)^##\s+V\d')
    if ($NextHeaderMatch.Success) {
        $Notes = $Rest.Substring(0, $CurrentHeader.Length + $NextHeaderMatch.Index).Trim()
    } else {
        $Notes = $Rest.Trim()
    }
}
$Notes | Set-Content -LiteralPath $ReleaseNotesPath -Encoding UTF8

Copy-Item -LiteralPath $ExeFile -Destination $UploadExe -Force

Write-Host "Version: $Version"
Write-Host "Repository: $Repo"
Write-Host "Asset: $UploadExe"
Write-Host ""

$ExistingRelease = $null
try {
    $ExistingRelease = gh release view $Version --repo $Repo --json tagName 2>$null
} catch {
    $ExistingRelease = $null
}

if ($ExistingRelease) {
    Write-Host "Release already exists. Updating notes and replacing EXE asset..."
    gh release edit $Version --repo $Repo --title $ReleaseTitle --notes-file $ReleaseNotesPath
    gh release upload $Version $UploadExe --repo $Repo --clobber
} else {
    Write-Host "Creating new GitHub release..."
    gh release create $Version $UploadExe --repo $Repo --title $ReleaseTitle --notes-file $ReleaseNotesPath
}

Write-Host ""
Write-Host "Done."
Write-Host "Release page:"
Write-Host "https://github.com/$Repo/releases/tag/$Version"
