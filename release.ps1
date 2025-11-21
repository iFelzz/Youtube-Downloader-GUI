<#
Release helper script
- Zips the dist\YouTubeDownloader folder into releases\YouTubeDownloader-<version>.zip
Usage: .\release.ps1 -Version 1.0.0
#>

param(
    [string]$Version
)

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$distFolder = Join-Path $projectRoot 'dist\YouTubeDownloader'
$distExe = Join-Path $projectRoot 'dist\YouTubeDownloader.exe'

if (-not $Version) {
    $Version = (Get-Date -Format yyyyMMddHHmmss)
}

$releasesDir = Join-Path $projectRoot 'releases'
if (-not (Test-Path $releasesDir)) { New-Item -ItemType Directory -Path $releasesDir | Out-Null }

$zipName = "YouTubeDownloader-$Version.zip"
$zipPath = Join-Path $releasesDir $zipName

if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

if (Test-Path $distFolder) {
    Write-Host "Creating release zip from folder: $distFolder -> $zipPath"
    Compress-Archive -Path (Join-Path $distFolder '*') -DestinationPath $zipPath -Force
    Write-Host "Release created: $zipPath" -ForegroundColor Green
} elseif (Test-Path $distExe) {
    Write-Host "Creating release zip from single-file exe: $distExe -> $zipPath"
    Compress-Archive -Path $distExe -DestinationPath $zipPath -Force
    Write-Host "Release created: $zipPath" -ForegroundColor Green
} else {
    Write-Host "Dist not found: neither folder '$distFolder' nor exe '$distExe' exist. Build first." -ForegroundColor Red
    exit 1
}

# Optionally copy the installer if present
$installer = Join-Path $projectRoot 'installer\Output\YouTubeDownloaderInstaller.exe'
if (Test-Path $installer) {
    Copy-Item $installer -Destination $releasesDir -Force
    Write-Host "Copied installer to releases folder." -ForegroundColor Green
}

Write-Host "Done."
