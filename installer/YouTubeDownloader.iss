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
; Optional installer icon (place a .ico at ..\resources\app.ico to use)
SetupIconFile=..\resources\app.ico

[Files]
; Copy everything from dist\YouTubeDownloader\ into {app}
Source: "..\\dist\\YouTubeDownloader\\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

; If you have an app icon placed under resources, include it so the installer can reference it.
Source: "..\\resources\\app.ico"; DestDir: "{tmp}"; Flags: ignoreversion

[Tasks]
; Let the user choose whether to create a Desktop icon during install
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Icons]
; Start menu shortcut
Name: "{group}\YouTube Downloader"; Filename: "{app}\YouTubeDownloader.exe"; WorkingDir: "{app}"
; Desktop shortcut (created only if the user selected the task)
Name: "{autodesktop}\YouTube Downloader"; Filename: "{app}\YouTubeDownloader.exe"; Tasks: desktopicon; WorkingDir: "{app}"

[Run]
; Run the app after install (postinstall)
Filename: "{app}\YouTubeDownloader.exe"; Description: "Run YouTube Downloader"; Flags: nowait postinstall skipifsilent

; Notes:
; - Build the project with build.ps1 (PyInstaller) first, then compile this script with Inno Setup.
; - If you used a different name or onefile mode, adjust Source and Filename accordingly.
