; From http://nsis.sourceforge.net/File_Association
;
; Thanks to Vytautas and Intersol
; Comments and some modifications by David Harrison

!ifndef REGISTER_EXTENSION_NSH
!define REGISTER_EXTENSION_NSH

!define registerExtension "!insertmacro registerExtension"
!define unregisterExtension "!insertmacro unregisterExtension"

 ; see function registerExtension.
!macro registerExtension executable extension description appname
       Push "${appname}" ; "FLING MKV File"
       Push "${executable}"  ; "full path to my.exe"
       Push "${extension}"   ; ".mkv"
       Push "${description}" ; "MKV File"
       Call registerExtension
!macroend
 
; Registers the file association for extension (e.g., .bfloog) to the
; typename (e.g., "FLING").  This assumes that appname uniquely
; identifies the mapping from the filetype onto the executable.  If
; fling.exe and flit.exe both use FLINGFloogie then registerExtension will
; not recognize these as different applications and the second install
; overwrites rather than backs up the prior file association.
;
; Associates the file extension with icon 0 from the executable. --Dave
; This doesn't associate a mime type with the extension. --Dave
; back up old value of .opt
;
; For example:
;   ${registerExtension} "$INSTDIR\fling.exe" ".bfloog" "BitFloogie File" "FLING"
;
;  creates
;    HKCR/.bfloog/""                    FLING
;    HKCR/FLING/""                      BitFloogie File
;    HKCR/FLING/"Default Icon"          "C:\Program Files\FLING\fling.exe,0"
;    HKCR/FLING/shell/""                open
;    HKCR/FLING/shell/open/""           (value not set)
;    HKCR/FLING/shell/open/command      c:\Program Files\FLING\fling.exe "%1"
;
;  additionally if there had been a previous mapping for .bfloog to 
;  "GiantFloogie File" then registerExtensions creates
;    HKCR/.bfloog/backup_val          GiantFloogie File
;      
Function registerExtension
!define Index "Line${__LINE__}"
  pop $R0 ; description.
  pop $R1 ; extension  (e.g., .bfloog)
  pop $R2 ; path to executable
  pop $R3 ; unique type name.
  push $1 ; save value to avoid side effects to global state.
  push $0 ; save value to avoid side effects to global state.
  ReadRegStr $1 HKCR $R1 ""    
  StrCmp $1 "" "${Index}-NoBackup"  ; don't backup if no prior association
  StrCmp $1 $R3 "${Index}-NoBackup" ; don't backup if we've already set association
  StrCmp $1 "OptionsFile" "${Index}-NoBackup"
    WriteRegStr HKCR $R1 "backup_val" $1
"${Index}-NoBackup:"
  WriteRegStr HKCR $R1 "" $R3 
  ReadRegStr $0 HKCR $R0 ""
  StrCmp $0 "" 0 "${Index}-Skip"
	WriteRegStr HKCR $R3 "" $R0   ; I thought $R0 was the description? --Dave
	WriteRegStr HKCR "$R3\shell" "" "open"
	WriteRegStr HKCR "$R3\DefaultIcon" "" "$R2,0"
"${Index}-Skip:"
  WriteRegStr HKCR "$R3\shell\open\command" "" '$R2 "%1"'
  ;WriteRegStr HKCR "$R3\shell\edit" "" "Edit $R0"
  ;WriteRegStr HKCR "$R3\shell\edit\command" "" '$R2 "%1"'
  pop $0  ; restore value to before this call.
  pop $1  ; restore value to before this call.
!undef Index
FunctionEnd
 
!macro unregisterExtension extension appname
       Push "${extension}"         ;  ".mkv"
       Push "${appname}"   ;  "FLING MKV File"
       Call un.unregisterExtension
!macroend

Function un.unregisterExtension
  pop $R1 ; appname
  pop $R0 ; extension
!define Index "Line${__LINE__}"
  ReadRegStr $1 HKCR $R0 ""
  StrCmp $1 $R1 0 "${Index}-NoOwn"  ; only do this if we own it
  ReadRegStr $1 HKCR $R0 "backup_val"
  StrCmp $1 "" 0 "${Index}-Restore" ; if backup="" then delete the whole key
  DeleteRegKey HKCR $R0
  Goto "${Index}-NoOwn"
"${Index}-Restore:"
  WriteRegStr HKCR $R0 "" $1
  DeleteRegValue HKCR $R0 "backup_val"
  DeleteRegKey HKCR $R1 ;Delete key with association name settings
"${Index}-NoOwn:"
!undef Index
FunctionEnd

!endif
