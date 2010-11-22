;--------------------------------
;Include Modern UI

  !include "MUI2.nsh"

;--------------------------------
;General

  ;Name and file
  Name "flingo"
  OutFile "setup.exe"

  ;Default installation folder
  InstallDir “$PROGRAMFILES\flingo”
  
  ;Get installation folder from registry if available
  InstallDirRegKey HKCU "Software\flingo" ""

  ;Request application privileges for Windows Vista
  RequestExecutionLevel admin

;--------------------------------
;Interface Settings

  !define MUI_ABORTWARNING

;--------------------------------
;Pages

  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES
  
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES
  
;--------------------------------
;Languages
 
  !insertmacro MUI_LANGUAGE "English"

;--------------------------------
;Installer Sections

Section

  SetOutPath "$INSTDIR"
  
  ;ADD YOUR OWN FILES HERE...
  File "dist\*"
  
  ;Store installation folder
  WriteRegStr HKCU "Software\flingo" "" $INSTDIR
  
  ;Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  ;start menu shortcut
  CreateDirectory "$SMPROGRAMS\flingo"
  CreateShortCut "$SMPROGRAMS\flingo\flingo.lnk" "$INSTDIR\uninstaller.exe"
  CreateShortCut "$SMPROGRAMS\flingo\flingo.lnk" "$INSTDIR\flingo.exe"

SectionEnd

;--------------------------------
;Uninstaller Section

Section "Uninstall"

  ;ADD YOUR OWN FILES HERE...
  Delete "$INSTDIR\*"
  RMDir "$INSTDIR"

  DeleteRegKey /ifempty HKCU "Software\flingo"

  Delete "$SMPROGRAMS\fling\*"
  RMDir "$SMPROGRAMS\fling"

SectionEnd