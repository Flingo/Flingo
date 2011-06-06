; DAVE'S NOTE: This was an initial installer I wrote for a different project
; and then mapped to Flingo, but Omar Zennadi decided to write his own. 
; This script has some useful features that could be added to the main
; flingo.nsi script or this one could replace Omar's.  In particular, this
; install fling menu items that appear on the pop-up menu when you right-click
; on a file in Windows Explorer.

; Flingo for Desktop Installer
;
; This script uses MUI.  Docs for MUI can be found at 
;  http://nsis.sourceforge.net/Docs/Modern%20UI/Readme.html
;
; Copyright(C) 2008. David Harrison. Released under the terms of GPL v2.0.
; Copyright(C) 2009. 2010. Freestream Media Corp.  Released under the
; terms of GPL v2.0.
;
; To build an nsis installer, start the "nullsoft scriptable install system."
; Click on "Compile NSI scripts."  This opens a dialog title "MakeNSISW."
; Drag and drop the flingo.nsi file onto this dialog.
; Once complete a setup.exe file will reside in Flingo\Desktop\nsis



; Normal location for settings in the windows registry:
;   HKEY_CURRENT_USER\Software\Vendor's name\Application's name\Version\Setting name
;
; HKCU is short for HKEY_CURRENT_USER. 
; In the flingo case, we combine "Vendor's name" and "Application's name."  For
; now I won't worry about version number.
;
;   HKEY_CURRENT_USER\Software\flingo\0.2\Setting name
;
; i.e.,
;
;   HKEY_CURRENT_USER\Software\${PRODUCT_NAME}\Setting name
;   
; Author: David Harrison

!define TEMP1 $R0 ;Temp variable
 
; HM NIS Edit Wizard helper defines
!define PRODUCT_NAME "flingo_test"
!define PRODUCT_VERSION "v0.2"
!define PRODUCT_PUBLISHER "Flingo"
!define PRODUCT_WEB_SITE "http://flingo.org"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\flingo.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

; for setting and restoring file associations.
!include "registerExtension.nsh"
!include "explorer_popup_menu.nsh"

; MUI 1.67 compatible ------
!include "MUI.nsh"

;Request application privileges for Windows Vista
RequestExecutionLevel admin

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

;Order of pages
!insertmacro MUI_PAGE_WELCOME
;!insertmacro MUI_PAGE_LICENSE "flingo_eula.rtf"
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
OutFile "setup.exe"

; Default install directory.
InstallDir "$PROGRAMFILES\flingo"
; InstallDirRegKey tells installer to check a string in the registry
; and use it for the install dir if that string is valid, it will
; override the InstallDir attribute if the registry key is valid,
; otherwise it will fall back to the InstallDir default. 
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

; "File" adds file(s) to be extracted to OutPath. /r = recursive
Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  File /r "..\dist\*.*"  
  ;File "Readme.txt"
SectionEnd
 
 
Section -AdditionalIcons 
  WriteIniStr "$INSTDIR\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  CreateShortCut "$SMPROGRAMS\flingo\Website.lnk" "$INSTDIR\${PRODUCT_NAME}.url" 

  # The "..\flingo.icns" in the next line appears to have no effect.
  #CreateShortCut "$SMPROGRAMS\flingo\Website.lnk" "$INSTDIR\${PRODUCT_NAME}.url" "..\flingo.icns"
  CreateShortCut "$SMPROGRAMS\flingo\Uninstall.lnk" "$INSTDIR\uninst.exe"
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

  ; add default settings.  In Linx these settings are found in the flingo.conf file.
  WriteRegStr HKLM "Software\${PRODUCT_NAME}" "name" "All Devices"
  WriteRegStr HKLM "Software\${PRODUCT_NAME}" "cache" "None"
  WriteRegStr HKLM "Software\${PRODUCT_NAME}" "host" "http://flingo.tv"
  WriteRegStr HKLM "Software\${PRODUCT_NAME}" "flingdir" "Unchecked"
  WriteRegStr HKLM "Software\${PRODUCT_NAME}" "port" "8080"

  ; add explorer pop-up menus for types handled by flingo.
  ${addExplorerPopUpMenuItem} ".asf"  "Advanced Systems Format File" "flingo" "Fling to TV or media device..." "$INSTDIR\flingo.exe $\"%L$\"" 
  ${addExplorerPopUpMenuItem} ".avi"  "AVI File" "flingo" "Fling to TV or media device..." "$INSTDIR\flingo.exe $\"%L$\"" 
  ${addExplorerPopUpMenuItem} ".divx" "DivX Video File" "flingo" "Fling to TV or media device..." "$INSTDIR\flingo.exe $\"%L$\""
  ${addExplorerPopUpMenuItem} ".dvx"  "DivX Video File" "flingo" "Fling to TV or media device..."  "$INSTDIR\flingo.exe $\"%L$\""
  ${addExplorerPopUpMenuItem} ".mkv"  "Matroska Video File" "flingo" "Fling to TV or media device..." "$INSTDIR\flingo.exe $\"%L$\"" 
  ${addExplorerPopUpMenuItem} ".mp4"  "MPEG-4 Video File" "flingo" "Fling to TV or media device..."  "$INSTDIR\flingo.exe $\"%L$\""
  ${addExplorerPopUpMenuItem} ".m4v"  "MPEG-4 Video File" "flingo" "Fling to TV or media device..." "$INSTDIR\flingo.exe $\"%L$\"" 
  ${addExplorerPopUpMenuItem} ".m4a"  "MPEG-4 Audio File" "flingo" "Fling to TV or media device..." "$INSTDIR\flingo.exe $\"%L$\"" 
  ${addExplorerPopUpMenuItem} ".mov"  "QuickTime Movie" "flingo" "Fling to TV or media device..."  "$INSTDIR\flingo.exe $\"%L$\""
  ${addExplorerPopUpMenuItem} ".moov" "QuickTime Movie" "flingo" "Fling to TV or media device..."  "$INSTDIR\flingo.exe $\"%L$\""
  ${addExplorerPopUpMenuItem} ".3gp"  "3GPP Multimedia File" "flingo" "Fling to TV or media device..."  "$INSTDIR\flingo.exe $\"%L$\""
  ${addExplorerPopUpMenuItem} ".ogg"  "Ogg Media File" "flingo" "Fling to TV or media device..."  "$INSTDIR\flingo.exe $\"%L$\""
  ${addExplorerPopUpMenuItem} ".ogm"  "Ogg Media File" "flingo" "Fling to TV or media device..."  "$INSTDIR\flingo.exe $\"%L$\""
  ${addExplorerPopUpMenuItem} ".wmv"  "Windows Media Video File" "flingo" "Fling to TV or media device..."  "$INSTDIR\flingo.exe $\"%L$\""  
  ${addExplorerPopUpMenuItem} ".flv"  "Flash Video File" "flingo" "Fling to TV or media device..."  "$INSTDIR\flingo.exe $\"%L$\""  
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
  ;Var /Global TorrentFileAssociation
  ReadINIStr $InstallStartMenuShortcut "$PLUGINSDIR\FileAssoc.ini" "Field 1" "State"
  ReadINIStr $InstallDesktopShortcut "$PLUGINSDIR\FileAssoc.ini" "Field 2" "State"
  ;ReadINIStr $TorrentFileAssociation "$PLUGINSDIR\FileAssoc.ini" "Field 3" "State"

  IntCmp $InstallStartMenuShortcut 1 install_startmenu no_startmenu no_startmenu
  install_startmenu:
    CreateDirectory "$SMPROGRAMS\flingo"
    CreateShortCut "$SMPROGRAMS\flingo\flingo.lnk" "$INSTDIR\flingo.exe"
  no_startmenu:

  IntCmp $InstallDesktopShortcut 1 install_desktop no_desktop no_desktop
  install_desktop:
    CreateShortCut "$DESKTOP\flingo.lnk" "$INSTDIR\flingo.exe"
  no_desktop:

  ;IntCmp $TorrentFileAssociation 1 set_torrent no_torrent no_torrent
  ;set_torrent:
  ;  ; This makes a backup of the .torrent mapping in HKCR/.torrent/backup_xsval.
  ;  ; I can use this mapping later in the application later to launch the appropriate
  ;  ; application when the user decides not to send the file to the flingo.
  ;  ${registerExtension} "$INSTDIR\flingo.exe" ".torrent" "BitTorrent Metainfo File" "flingo"
  ;no_torrent:

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

  Delete "$SMPROGRAMS\flingo\Uninstall.lnk"
  Delete "$SMPROGRAMS\flingo\Website.lnk"
  Delete "$DESKTOP\flingo.lnk"
  Delete "$SMPROGRAMS\flingo\flingo.lnk"

  RMDir "$SMPROGRAMS\flingo"
  RMDir "$INSTDIR"

  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  DeleteRegKey HKLM "Software\${PRODUCT_NAME}"

  # Remove Explorer right-click menu items for types known to be handled by flingo and
  # restore file associations.
  ${unregisterExtension} ".torrent" "flingo"
  ${removeExplorerPopUpMenuItem} ".torrent" "flingo" "Fling to TV or media device..."
  ${removeExplorerPopUpMenuItem} ".asf"  "flingo" "Fling to TV or media device..."
  ${removeExplorerPopUpMenuItem} ".avi"  "flingo" "Fling to TV or media device..." 
  ${removeExplorerPopUpMenuItem} ".divx" "flingo" "Fling to TV or media device..." 
  ${removeExplorerPopUpMenuItem} ".dvx"  "flingo" "Fling to TV or media device..." 
  ${removeExplorerPopUpMenuItem} ".mkv"  "flingo" "Fling to TV or media device..." 
  ${removeExplorerPopUpMenuItem} ".mp4"  "flingo" "Fling to TV or media device..." 
  ${removeExplorerPopUpMenuItem} ".m4v"  "flingo" "Fling to TV or media device..." 
  ${removeExplorerPopUpMenuItem} ".m4a"  "flingo" "Fling to TV or media device..." 
  ${removeExplorerPopUpMenuItem} ".mov"  "flingo" "Fling to TV or media device..." 
  ${removeExplorerPopUpMenuItem} ".moov" "flingo" "Fling to TV or media device..." 
  ${removeExplorerPopUpMenuItem} ".3gp"  "flingo" "Fling to TV or media device..." 
  ${removeExplorerPopUpMenuItem} ".ogg"  "flingo" "Fling to TV or media device..." 
  ${removeExplorerPopUpMenuItem} ".ogm"  "flingo" "Fling to TV or media device..." 
  ${removeExplorerPopUpMenuItem} ".wmv"  "flingo" "Fling to TV or media device..."   
  ${removeExplorerPopUpMenuItem} ".flv"  "flingo" "Fling to TV or media device..."   

  SetAutoClose true
SectionEnd
