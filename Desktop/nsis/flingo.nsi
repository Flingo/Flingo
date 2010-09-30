; FLING install test.
; This script uses MUI.  Docs for MUI can be found at 
;  http://nsis.sourceforge.net/Docs/Modern%20UI/Readme.html
;
; Copyright(C) 2008. David Harrison. Released under the terms of GPL v2.0.
; Copyright(C) 2009. 2010. Freestream Media Corp.  Released under the
; terms of GPL v2.0.
;
; Author: David Harrison

!define TEMP1 $R0 ;Temp variable
 
; HM NIS Edit Wizard helper defines
!define PRODUCT_NAME "Flingo"
!define PRODUCT_VERSION "0.1"
!define PRODUCT_PUBLISHER "flingo.org"
!define PRODUCT_WEB_SITE "http://flingo.org"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\flingo.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

; for setting and restoring file associations.
!include "registerExtension.nsh"
!include "explorer_popup_menu.nsh"

; MUI 1.67 compatible ------
!include "MUI.nsh"

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

;Order of pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "fling_eula.rtf"
!insertmacro MUI_PAGE_DIRECTORY
Page custom SetCustom "" ""
!insertmacro MUI_PAGE_INSTFILES
;!define MUI_FINISHPAGE_RUN "$INSTDIR\flingo.exe"
; I thought maybe the finish page would allow me to specify checkboxes 
; to create shortcuts, but it doesn't.
!insertmacro MUI_PAGE_FINISH

; Language files
!insertmacro MUI_LANGUAGE "English"
; MUI end ------

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "Setup.exe"

; Default install directory.
InstallDir "$PROGRAMFILES\Flingo"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  ;File "release\flingo.exe"
  File "debug\flingo.exe"   ; "File" adds a file to be extracted to the OutPath.
  File "Readme.txt"
  File "flingo_eula.rtf"
SectionEnd
 
 
Section -AdditionalIcons 
  WriteIniStr "$INSTDIR\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  CreateShortCut "$SMPROGRAMS\FLING\Website.lnk" "$INSTDIR\${PRODUCT_NAME}.url"
  CreateShortCut "$SMPROGRAMS\FLING\Uninstall.lnk" "$INSTDIR\uninst.exe"
SectionEnd

Section -Post

  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\flingo.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\flingo.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}////"

  ; add explorer pop-up menus for types handled by FLING.
  ${addExplorerPopUpMenuItem} ".asf"  "Advanced Systems Format File" "FLING" "Send to FLING..." "$INSTDIR\flingo.exe $\"%L$\"" 
  ${addExplorerPopUpMenuItem} ".avi"  "AVI File" "FLING" "Send to FLING..." "$INSTDIR\flingo.exe $\"%L$\"" 
  ${addExplorerPopUpMenuItem} ".divx" "DivX Video File" "FLING" "Send to FLING..." "$INSTDIR\flingo.exe $\"%L$\""
  ${addExplorerPopUpMenuItem} ".dvx"  "DivX Video File" "FLING" "Send to FLING..."  "$INSTDIR\flingo.exe $\"%L$\""
  ${addExplorerPopUpMenuItem} ".mkv"  "Matroska Video File" "FLING" "Send to FLING..." "$INSTDIR\flingo.exe $\"%L$\"" 
  ${addExplorerPopUpMenuItem} ".mp4"  "MPEG-4 Video File" "FLING" "Send to FLING..."  "$INSTDIR\flingo.exe $\"%L$\""
  ${addExplorerPopUpMenuItem} ".m4v"  "MPEG-4 Video File" "FLING" "Send to FLING..."
  ${addExplorerPopUpMenuItem} ".m4a"  "MPEG-4 Audio File" "FLING" "Send to FLING..."
  ${addExplorerPopUpMenuItem} ".mov"  "QuickTime Movie" "FLING" "Send to FLING..."  "$INSTDIR\flingo.exe $\"%L$\""
  ${addExplorerPopUpMenuItem} ".moov" "QuickTime Movie" "FLING" "Send to FLING..."  "$INSTDIR\flingo.exe $\"%L$\""
  ${addExplorerPopUpMenuItem} ".3gp"  "3GPP Multimedia File" "FLING" "Send to FLING..."  "$INSTDIR\flingo.exe $\"%L$\""
  ${addExplorerPopUpMenuItem} ".ogg"  "Ogg Media File" "FLING" "Send to FLING..."  "$INSTDIR\flingo.exe $\"%L$\""
  ${addExplorerPopUpMenuItem} ".ogm"  "Ogg Media File" "FLING" "Send to FLING..."  "$INSTDIR\flingo.exe $\"%L$\""
  ${addExplorerPopUpMenuItem} ".wmv"  "Windows Media Video File" "FLING" "Send to FLING..."  "$INSTDIR\flingo.exe $\"%L$\""  
  ${addExplorerPopUpMenuItem} ".flv"  "Flash Video File" "FLING" "Send to FLING..."  "$INSTDIR\flingo.exe $\"%L$\""  
SectionEnd 


Function .onInit
 
  StrCpy $2 0
 
  InitPluginsDir

  ; We put the FileAssoc.ini file in a the plugins directory so it can be
  ; found later when InstallOptions is called to create our custom page.
  File /oname=$PLUGINSDIR\FileAssoc.ini "FileAssoc.ini"
  
FunctionEnd
 
Function SetCustom
 
  ;Display the InstallOptions dialog
  
  Push ${TEMP1}
 
  ; I removed "PLUGINSDIR" and the dialog stopped working.  Why PLUGINSDIR?
  ; I found this is in the NSIS docs which explains why it would be used:
  ;   [PLUGINSDIR is ...] the path to a temporary folder created upon
  ;   the first usage of a plug-in or a call to InitPluginsDir. This
  ;   folder is automatically deleted when the installer exits. This
  ;   makes this folder the ideal folder to hold INI files for
  ;   InstallOptions, bitmaps for the splash plug-in, or any other
  ;   file that a plug-in needs to work.
  ;
  ; See .onInit where we put FileAssoc.ini in the PLUGINSDIR.
  InstallOptions::dialog "$PLUGINSDIR\FileAssoc.ini"
  Pop ${TEMP1}
  
  StrCmp ${TEMP1} "success" 0 continue
  Var /Global InstallStartMenuShortcut
  Var /Global InstallDesktopShortcut
  Var /Global TorrentFileAssociation
  ReadINIStr $InstallStartMenuShortcut "$PLUGINSDIR\FileAssoc.ini" "Field 1" "State"
  ReadINIStr $InstallDesktopShortcut "$PLUGINSDIR\FileAssoc.ini" "Field 2" "State"
  ReadINIStr $TorrentFileAssociation "$PLUGINSDIR\FileAssoc.ini" "Field 3" "State"

  IntCmp $InstallStartMenuShortcut 1 install_startmenu no_startmenu no_startmenu
  install_startmenu:
    CreateDirectory "$SMPROGRAMS\FLING"
    CreateShortCut "$SMPROGRAMS\FLING\FLING.lnk" "$INSTDIR\flingo.exe"
  no_startmenu:

  IntCmp $InstallDesktopShortcut 1 install_desktop no_desktop no_desktop
  install_desktop:
    CreateShortCut "$DESKTOP\FLING.lnk" "$INSTDIR\flingo.exe"
  no_desktop:

  IntCmp $TorrentFileAssociation 1 set_torrent no_torrent no_torrent
  set_torrent:
    ; This makes a backup of the .torrent mapping in HKCR/.torrent/backup_xsval.
    ; I can use this mapping later in the application later to launch the appropriate
    ; application when the user decides not to send the file to the FLING.
    ${registerExtension} "$INSTDIR\flingo.exe" ".torrent" "BitTorrent Metainfo File" "FLING"
  no_torrent:

  continue:
    ; Restore the value of TEMP1 before returning.
    Pop ${TEMP1}
    Return
 
FunctionEnd

Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) was successfully removed from your computer."
FunctionEnd

Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Are you sure you want to completely remove $(^Name) and all of its components?" IDYES +2
  Abort
FunctionEnd


Section Uninstall
  Delete "$INSTDIR\${PRODUCT_NAME}.url"
  Delete "$INSTDIR\uninst.exe"
  Delete "$INSTDIR\fling_eula.rtf"
  Delete "$INSTDIR\Readme.txt"
  Delete "$INSTDIR\flingo.exe"

  Delete "$SMPROGRAMS\FLING\Uninstall.lnk"
  Delete "$SMPROGRAMS\FLING\Website.lnk"
  Delete "$DESKTOP\FLING.lnk"
  Delete "$SMPROGRAMS\FLING\FLING.lnk"

  RMDir "$SMPROGRAMS\FLING"
  RMDir "$INSTDIR"

  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"

  # Remove Explorer right-click menu items for types known to be handled by FLING and
  # restore file associations.
  ${unregisterExtension} ".torrent" "FLING"
  ${removeExplorerPopUpMenuItem} ".torrent" "FLING" "Send to FLING..."
  ${removeExplorerPopUpMenuItem} ".asf"  "FLING" "Send to FLING..."
  ${removeExplorerPopUpMenuItem} ".avi"  "FLING" "Send to FLING..." 
  ${removeExplorerPopUpMenuItem} ".divx" "FLING" "Send to FLING..." 
  ${removeExplorerPopUpMenuItem} ".dvx"  "FLING" "Send to FLING..." 
  ${removeExplorerPopUpMenuItem} ".mkv"  "FLING" "Send to FLING..." 
  ${removeExplorerPopUpMenuItem} ".mp4"  "FLING" "Send to FLING..." 
  ${removeExplorerPopUpMenuItem} ".m4v"  "FLING" "Send to FLING..." 
  ${removeExplorerPopUpMenuItem} ".m4a"  "FLING" "Send to FLING..." 
  ${removeExplorerPopUpMenuItem} ".mov"  "FLING" "Send to FLING..." 
  ${removeExplorerPopUpMenuItem} ".moov" "FLING" "Send to FLING..." 
  ${removeExplorerPopUpMenuItem} ".3gp"  "FLING" "Send to FLING..." 
  ${removeExplorerPopUpMenuItem} ".ogg"  "FLING" "Send to FLING..." 
  ${removeExplorerPopUpMenuItem} ".ogm"  "FLING" "Send to FLING..." 
  ${removeExplorerPopUpMenuItem} ".wmv"  "FLING" "Send to FLING..."   
  ${removeExplorerPopUpMenuItem} ".flv"  "FLING" "Send to FLING..."   

  SetAutoClose true
SectionEnd
