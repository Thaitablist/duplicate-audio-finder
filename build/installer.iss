; Inno Setup script — wraps the PyInstaller output into a Windows installer.
; Build the app first:  pyinstaller build\dupaudio.spec
; Then compile this with the Inno Setup Compiler (ISCC.exe installer.iss).

[Setup]
AppName=Duplicate Audio Finder
AppVersion=0.1.0
DefaultDirName={autopf}\Duplicate Audio Finder
DefaultGroupName=Duplicate Audio Finder
UninstallDisplayIcon={app}\DuplicateAudioFinder.exe
SetupIconFile=..\src\dupaudio\assets\icon.ico
OutputDir=..\dist
OutputBaseFilename=DuplicateAudioFinder-Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
; Copy the one-folder PyInstaller output produced under dist\DuplicateAudioFinder.
Source: "..\dist\DuplicateAudioFinder\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Duplicate Audio Finder"; Filename: "{app}\DuplicateAudioFinder.exe"
Name: "{autodesktop}\Duplicate Audio Finder"; Filename: "{app}\DuplicateAudioFinder.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\DuplicateAudioFinder.exe"; Description: "Launch Duplicate Audio Finder"; Flags: nowait postinstall skipifsilent
