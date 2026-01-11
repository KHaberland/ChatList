; Inno Setup Script для ChatList
; Скрипт создаёт инсталлятор с полной поддержкой удаления программы

#define MyAppName "ChatList"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "KHaberland"
#define MyAppURL "https://github.com/KHaberland/ChatList"
#define MyAppExeName "ChatList.exe"

[Setup]
; Уникальный идентификатор приложения
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE
OutputDir=installer
OutputBaseFilename=ChatList-{#MyAppVersion}-Setup
SetupIconFile=app.ico
Compression=lzma2/max
SolidCompression=yes
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Uninstallable=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
PrivilegesRequired=lowest
WizardStyle=modern

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkablealone

[Files]
; Основной исполняемый файл
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Лицензия
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Ярлык в меню Пуск
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
; Ярлык для удаления в меню Пуск
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; Ярлык на рабочем столе (опционально)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Запустить приложение после установки (опционально)
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Удаление папки с логами (если есть)
Type: filesandordirs; Name: "{app}\logs"
; Удаление кэша (если есть)
Type: filesandordirs; Name: "{app}\cache"
; Удаление базы данных
Type: files; Name: "{app}\chatlist.db"

[Code]
// Спрашивать пользователя об удалении данных при деинсталляции
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DatabasePath: string;
begin
  if CurUninstallStep = usUninstall then
  begin
    DatabasePath := ExpandConstant('{app}\chatlist.db');
    if FileExists(DatabasePath) then
    begin
      if MsgBox('Сохранить базу данных чатов для будущего использования?', mbConfirmation, MB_YESNO) = IDYES then
      begin
        // Копируем базу в документы пользователя
        CopyFile(DatabasePath, ExpandConstant('{userdocs}\chatlist_backup.db'), False);
      end;
    end;
  end;
end;
