<#
Release helper script
- Zips the dist\YouTubeDownloader folder into releases\YouTubeDownloader-<version>.zip
Usage: .\release.ps1 -Version 1.0.0
#>

param(
    [string]$Version
)

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$distDir = Join-Path $projectRoot 'dist\YouTubeDownloader'
if (-not (Test-Path $distDir)) {
    Write-Host "Dist folder not found: $distDir. Build the project first with build.ps1." -ForegroundColor Red
    exit 1
}

if (-not $Version) {
    $Version = (Get-Date -Format yyyyMMddHHmmss)
}

$releasesDir = Join-Path $projectRoot 'releases'
if (-not (Test-Path $releasesDir)) { New-Item -ItemType Directory -Path $releasesDir | Out-Null }

$zipName = "YouTubeDownloader-$Version.zip"
$zipPath = Join-Path $releasesDir $zipName

if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

Write-Host "Creating release zip: $zipPath"
Compress-Archive -Path (Join-Path $distDir '*') -DestinationPath $zipPath -Force

Write-Host "Release created: $zipPath" -ForegroundColor Green

# Optionally copy the installer if present
$installer = Join-Path $projectRoot 'installer\Output\YouTubeDownloaderInstaller.exe'
if (Test-Path $installer) {
    Copy-Item $installer -Destination $releasesDir -Force
    Write-Host "Copied installer to releases folder." -ForegroundColor Green
}

Write-Host "Done."
