; LOL 战绩助手 — Inno Setup 安装脚本
; 用法：先运行 pyinstaller build_config/lol-assistant.spec 生成 dist/LOL战绩助手/
;       再用 Inno Setup 编译此脚本
;
; 前提：iscc.exe 在 PATH 中，或用 Inno Setup GUI 打开此文件编译
; 命令行：iscc build_config\installer.iss

#define MyAppName "LOL战绩助手"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "LOL Assistant"
#define MyAppExeName "LOL战绩助手.exe"

; 项目根目录（installer.iss 在 build_config/ 下）
#define ProjectRoot AddBackslash(ExtractFilePath(SourcePath) + "..")

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir={#ProjectRoot}dist\installer
OutputBaseFilename=LOL战绩助手_Setup_{#MyAppVersion}
SetupIconFile={#ProjectRoot}icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
; 卸载时不删除 data 目录（用户数据）
UninstallFilesDir={app}\uninstall

[Languages]
#ifexist "compiler:Languages\ChineseSimplified.isl"
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
#endif
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加操作:"

[Files]
; PyInstaller ???????? + ???
Source: "{#ProjectRoot}dist\package_staging\app\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; jicheng ???????????????????
Source: "{#ProjectRoot}dist\package_staging\jicheng\LoginLauncher.exe"; DestDir: "{app}\jicheng"; DestName: "???.exe"; Flags: ignoreversion
Source: "{#ProjectRoot}dist\package_staging\jicheng\node.dll"; DestDir: "{app}\jicheng"; Flags: ignoreversion
Source: "{#ProjectRoot}dist\package_staging\jicheng\set.ini"; DestDir: "{app}\jicheng"; Flags: ignoreversion
Source: "{#ProjectRoot}dist\package_staging\jicheng\Plugins\*"; DestDir: "{app}\jicheng\Plugins"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#ProjectRoot}dist\package_staging\jicheng\data\setsoft.ini"; DestDir: "{app}\jicheng\data"; Flags: ignoreversion skipifsourcedoesntexist

; ?????????????????????
Source: "{#ProjectRoot}data\runes.json"; DestDir: "{app}\data"; Flags: ignoreversion skipifsourcedoesntexist onlyifdoesntexist
Source: "{#ProjectRoot}data\augments.json"; DestDir: "{app}\data"; Flags: ignoreversion skipifsourcedoesntexist onlyifdoesntexist
Source: "{#ProjectRoot}data\config.json"; DestDir: "{app}\data"; Flags: onlyifdoesntexist skipifsourcedoesntexist

[Dirs]
; 确保 data 目录存在且卸载时保留
Name: "{app}\data"; Flags: uninsneveruninstall
Name: "{app}\data\logs"; Flags: uninsneveruninstall

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 清理日志和临时文件，但保留用户数据
Type: filesandordirs; Name: "{app}\data\logs"
Type: files; Name: "{app}\data\*.tmp"
