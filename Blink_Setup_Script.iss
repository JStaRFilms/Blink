; -- Blink Setup Script for Inno Setup --
; This is the VibeCode for your installer.

[Setup]
; --- CORE APP INFO ---
AppName=Blink AI Assistant
AppVersion=1.0.3
AppPublisher=JStaRFilms
AppPublisherURL=https://github.com/JStaRFilms/Blink
DefaultDirName={autopf}\Blink
DefaultGroupName=Blink AI Assistant
AllowNoIcons=yes
PrivilegesRequired=lowest

; --- BRANDING & AESTHETICS ---
; Use the assets we generated!
SetupIconFile=assets\icon.ico
WizardImageFile=assets\installer_banner.bmp
WizardSmallImageFile=assets\wizard_icon.bmp
WizardStyle=modern

; --- OUTPUT ---
OutputDir=dist
OutputBaseFilename=Blink-Setup-v1.0.3
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
; --- Let the user choose what they want ---
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}";
Name: "launchonstartup"; Description: "Launch Blink when Windows starts"; GroupDescription: "Startup Options:";

[Files]
; --- This is your main payload ---
Source: "dist\Blink.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: isreadme
; Add any other necessary files here if you weren't using --onefile

[Icons]
; --- Create shortcuts based on user's choice in [Tasks] ---
Name: "{group}\Blink AI Assistant"; Filename: "{app}\Blink.exe"
Name: "{autodesktop}\Blink AI Assistant"; Filename: "{app}\Blink.exe"; Tasks: desktopicon

[Run]
; --- Run Blink at the end of the installation ---
Filename: "{app}\Blink.exe"; Description: "{cm:LaunchProgram,Blink AI Assistant}"; Flags: nowait postinstall skipifsilent

; ===================================================================================
;  -- REGISTRY ENTRIES --
;  Set the first-run flag so the app knows to show the wizard
; ===================================================================================
[Registry]
Root: HKCU; Subkey: "Software\Blink"; ValueType: dword; ValueName: "FirstRun"; ValueData: "1"; Flags: uninsdeletekey

; ===================================================================================
;  -- SIMPLE SCRIPT SECTION --
;  Just sets up basic config and first-run flag.
; ===================================================================================
[Code]

procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigPath: String;
begin
  if CurStep = ssPostInstall then
  begin
    Log('Post-install step: Writing basic config...');

    // Create the initial config.json in the user's AppData folder
    ConfigPath := ExpandConstant('{userappdata}\Blink');
    CreateDir(ConfigPath);

    // Write minimal default config - the first-run wizard will handle the rest
    SaveStringToFile(ConfigPath + '\config.json',
      '{' + #13#10 +
      '  "selected_model": "ollama:llama3.2:latest",' + #13#10 +
      '  "output_mode": "popup",' + #13#10 +
      '  "memory_enabled": true' + #13#10 +
      '}', False);

    Log('Basic config saved. First-run wizard will handle detailed setup.');
  end;
end;
