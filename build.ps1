# PowerShell build script for YouTube-Downloader-GUI
# Usage: run from project root (where main.py resides)
# ./build.ps1 [-OneFile]

param(
    [switch]$OneFile,
    [string]$Icon
)

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Write-Host "Project root: $projectRoot"

# Activate venv if present
$venvActivate = Join-Path $projectRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    Write-Host "Activating virtualenv..."
    . $venvActivate
} else {
    Write-Host "No virtualenv activation found. Make sure dependencies are installed globally or create .venv." -ForegroundColor Yellow
}

# Ensure pyinstaller is available
try {
    pyinstaller --version | Out-Null
} catch {
    Write-Host "PyInstaller not found. Installing..." -ForegroundColor Yellow
    pip install pyinstaller
}

# Try to locate packaged ffmpeg and yt-dlp in ./packages
$packagesDir = Join-Path $projectRoot 'packages'
$addBinaries = @()
if (Test-Path $packagesDir) {
    # ffmpeg
    $ffCandidate = Get-ChildItem -Path $packagesDir -Filter 'ffmpeg.exe' -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($ffCandidate) {
        $ffPath = $ffCandidate.FullName
        Write-Host "Found ffmpeg at: $ffPath"
        $addBinaries += "`"$ffPath`";.`"
    } else {
        Write-Host "No ffmpeg found under ./packages. PyInstaller will rely on system ffmpeg if available." -ForegroundColor Yellow
    }

    # yt-dlp executable (optional, used for subprocess fallback)
    $ytdlpCandidate = Get-ChildItem -Path $packagesDir -Filter 'yt-dlp.exe' -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($ytdlpCandidate) {
        $ytdlpPath = $ytdlpCandidate.FullName
        Write-Host "Found yt-dlp executable at: $ytdlpPath"
        $addBinaries += "`"$ytdlpPath`";.`"
    } else {
        Write-Host "No yt-dlp executable found under ./packages. The packaged Python module will be used if available." -ForegroundColor Yellow
    }
} else {
    Write-Host "No ./packages directory found." -ForegroundColor Yellow
}

$iconArg = $null
if ($Icon) {
    if (-not (Test-Path $Icon)) {
        Write-Host "Icon file '$Icon' not found; continuing without icon." -ForegroundColor Yellow
    } else {
        Write-Host "Using icon: $Icon"
        $iconArg = $Icon
    }
}

# Build pyinstaller command
$baseName = 'YouTubeDownloader'
$pyArgs = @()
if ($OneFile) {
    $pyArgs += '--onefile'
} else {
    $pyArgs += '--onedir'
}
$pyArgs += '--noconsole'
$pyArgs += "--name $baseName"

if ($iconArg) {
    $pyArgs += "--icon $iconArg"
}

foreach ($b in $addBinaries) {
    $pyArgs += "--add-binary"
    $pyArgs += $b
}
# Ensure yt_dlp import is included
$pyArgs += '--hidden-import'
$pyArgs += 'yt_dlp'

$pyArgs += 'main.py'

$cmd = "pyinstaller " + ($pyArgs -join ' ')
Write-Host "Running: $cmd"

# Execute
Invoke-Expression $cmd

Write-Host "Build finished. See dist\$baseName for the output." -ForegroundColor Green
# If an icon was provided, copy it into the dist folder for the installer to use
if ($iconArg) {
    $distIconDest = Join-Path -Path (Join-Path $projectRoot "dist\$baseName") -ChildPath (Split-Path $iconArg -Leaf)
    if (Test-Path $distIconDest) { Remove-Item $distIconDest -Force }
    try {
        Copy-Item -Path $iconArg -Destination $distIconDest -ErrorAction Stop
        Write-Host "Copied icon to: $distIconDest" -ForegroundColor Green
    } catch {
        Write-Host "Failed to copy icon into dist folder: $_" -ForegroundColor Yellow
    }
}
