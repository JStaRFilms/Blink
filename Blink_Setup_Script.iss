; -- Blink Setup Script for Inno Setup --
; This is the VibeCode for your installer.

[Setup]
; --- CORE APP INFO ---
AppName=Blink AI Assistant
AppVersion=1.0.0
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
OutputDir=userdocs:Blink Installer
OutputBaseFilename=Blink-Setup-v1.0.0
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
; Add any other necessary files here if you weren't using --onefile

[Icons]
; --- Create shortcuts based on user's choice in [Tasks] ---
Name: "{group}\Blink AI Assistant"; Filename: "{app}\Blink.exe"
Name: "{autodesktop}\Blink AI Assistant"; Filename: "{app}\Blink.exe"; Tasks: desktopicon

[Run]
; --- Run Blink at the end of the installation ---
Filename: "{app}\Blink.exe"; Description: "{cm:LaunchProgram,Blink AI Assistant}"; Flags: nowait postinstall skipifsilent

; ===================================================================================
;  -- THE MAGIC SECTION (Pascal Scripting) --
;  This handles Tesseract and the custom first-run setup.
; ===================================================================================
[Code]
var
  ModelsPage: TInputOptionWizardPage;
  TesseractInstalled: Boolean;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigPath, ConfigJson: String;
begin
  if CurStep = ssPostInstall then
  begin
    Log('Post-install step: Writing initial config...');

    // Create the initial config.json in the user's AppData folder with default Ollama
    ConfigPath := ExpandConstant('{userappdata}\Blink');
    CreateDir(ConfigPath);

    // Super simple default config
    ConfigJson := '{' +
                  ' "selected_model": "ollama:default",' +
                  ' "output_mode": "popup",' +
                  ' "memory_enabled": true,' +
                  ' "system_prompt": "You are a helpful and concise AI assistant."' +
                  '}';

    SaveStringToFile(ConfigPath + '\config.json', ConfigJson, False);
    Log('Initial config.json created with default Ollama provider');
  end;
end;

function InitializeSetup(): Boolean;
begin
  // Check if Tesseract is already installed before we try to download it
  TesseractInstalled := RegKeyExists(HKLM, 'Software\Tesseract-OCR') or RegKeyExists(HKCU, 'Software\Tesseract-OCR');
  if TesseractInstalled then
    Log('Tesseract is already installed. Skipping download.')
  else
    Log('Tesseract not found. Will be installed.');
  Result := True;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  // Custom page commented out for now - can be added later
end;

procedure InitializeWizard();
begin
  // Custom page commented out for now - can be added later

  // --- Handle Tesseract Installation ---
  // Commented out for now - requires InnoCallback.dll
  // if not TesseractInstalled then
  // begin
  //   // This is the "silent install" step. Inno Setup will download and run this for the user.
  //   // NOTE: This URL points to a specific version. Check for the latest stable version.
  //   AddPerlIcoDll; // Required for downloading
  //   Download(
  //     wpReady,
  //     'https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-v5.3.3.20231005.exe',
  //     'tesseract-setup.exe',
  //     'Installing Tesseract OCR...',
  //     'Tesseract is a free OCR engine that allows Blink to read text from images for text-only AI models.',
  //     @InstallTesseract,
  //     False,
  //     True
  //   );
  // end;
end;
