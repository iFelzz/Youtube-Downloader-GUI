; Inno Setup script for YouTube Downloader
; Put this file in project\installer and compile with Inno Setup Compiler

[Setup]
AppName=YouTube Downloader
AppVersion=1.0
DefaultDirName={pf}\YouTube Downloader
DefaultGroupName=YouTube Downloader
OutputBaseFilename=YouTubeDownloaderInstaller
Compression=lzma2
SolidCompression=yes
; Require admin to install into Program Files
PrivilegesRequired=admin
; Show license file during install (relative to installer script)
LicenseFile=..\LICENSE

[Files]
; Copy everything from dist\YouTubeDownloader\ into {app}
Source: "..\\dist\\YouTubeDownloader\\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
; Start menu shortcut
Name: "{group}\YouTube Downloader"; Filename: "{app}\YouTubeDownloader.exe"; WorkingDir: "{app}"
; Desktop shortcut
Name: "{autodesktop}\YouTube Downloader"; Filename: "{app}\YouTubeDownloader.exe"; Tasks: desktopicon; WorkingDir: "{app}"
; Uninstall shortcut entry in Start Menu (handled automatically)
[Icons]
[Run]
Name: "{group}\YouTube Downloader"; Filename: "{app}\YouTubeDownloader.exe"
Name: "{group}\Uninstall YouTube Downloader"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\YouTubeDownloader.exe"; Description: "Run YouTube Downloader"; Flags: nowait postinstall skipifsilent

; Notes:
; - Build the project with build.ps1 (PyInstaller) first, then compile this script.
; - If you used a different name or onefile mode, adjust Source and Filename accordingly.
