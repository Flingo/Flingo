; Copyright(C) 2008. David Harrison.  Released under the terms of GPL v2.0.
; Copyright(C) 2009. 2010. Free Stream Media Corp.  Released under the
; terms of GPL v2.0.
;
; Author: David Harrison

!ifndef EXPLORER_POPUP_MENU_NSH
!define EXPLORER_POPUP_MENU_NSH

!include "registerExtension.nsh"

; !define below allows the caller to call the macro as just ${addExplorerPopMenuItem}
; thus making the code easier to read.
!define addExplorerPopUpMenuItem "!insertmacro addExplorerPopUpMenuItem"

; Creates a pop-up menu item in the Windows explorer when you right-click on 
; a file.  If there is no associated app for this file type then it also
; associates the app_path as the default application for this type.
;
; Arguments:
;   extension: .mkv
;   description:  "MKV File"
;   unique_typename: "MKVAPP"
;   menu_item: "Send to MKV App"
;

;HEREPOOP! Why doesn't this work?  Is it getting executed?  How do I debug NSIS?
;Maybe some way to popup an alert?
; I modified the registry directly and was able to add a command "blah" 
; (see HKCR/flingo/shell/blah/command) that runs 
; Flingo successfully, but I need to make sure Flingo handles command-line arguments
; correctly.  Before I do that, I need to figure out why this function DIDN'T
; create the same mapping.
!macro addExplorerPopUpMenuItem extension description unique_typename menu_item app_path
!define Index "Line${__LINE__}"
  Push $1  ; save so don't interfere with caller.  Locally used for type_name.
  ReadRegStr $1 HKCR "${extension}" ""  
  ; StrCmp $x $y jump_if_equal jump_if_not   
  ; means if x == y then jump to jump_if_equal else jump_if_not 
  ; The zero means execute the following line.
  StrCmp $1 "" 0 "${Index}-add_menu_item"
  ${registerExtension} "${app_path}" "${extension}" "${description}" "${unique_typename}"

"${Index}-add_menu_item:"
  WriteRegStr HKCR "$1\shell\${menu_item}\command" "" "${app_path} $\"%L$\""
  Pop $1   ; restore.
!undef Index
!macroend

!define removeExplorerPopUpMenuItem "!insertmacro removeExplorerPopUpMenuItem"

; Removes the pop-up menu item created using addExplorerPopUpMenuItem.
; If app_path is the default association for this type then this is also removed.
; Arguments:
;   extension: .mkv
;   description:  "MKV File"
;   menu_item: "Send to MKV App"
;
!macro removeExplorerPopUpMenuItem extension unique_typename menu_item
  ${unregisterExtension} "${extension}" "${unique_typename}"
  Push $1 ; save so don't interfer with caller.  Locally used for type_name
  ReadRegStr $1 HKCR  "${extension}" ""   ; get type_name
  DeleteRegValue HKCR "$1\shell\${menu_item}\command" ""
  DeleteRegKey HKCR   "$1\shell\${menu_item}\command" 
  DeleteRegKey HKCR   "$1\shell\${menu_item}"
  Pop $1  ; restore.
!macroend


!endif
