#define MyAppName "Laftel Post"
#define MyAppVersion "1.0.0"
[Setup]
AppId={{A19D5D3B-7F6C-4B2A-9C51-8A0D1F8B2C11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\Laftel Post
DefaultGroupName=Laftel Post
OutputDir=dist
OutputBaseFilename=LaftelPost_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\LaftelPost.exe
[Files]
Source: "dist\LaftelPost.exe"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{group}\Laftel Post"; Filename: "{app}\LaftelPost.exe"
Name: "{autodesktop}\Laftel Post"; Filename: "{app}\LaftelPost.exe"
[Run]
Filename: "{app}\LaftelPost.exe"; Description: "เปิด Laftel Post"; Flags: postinstall nowait skipifsilent
