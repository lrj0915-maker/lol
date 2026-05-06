; LOL队伍聊天发送脚本（不加/all，只发给队友）
; 用法: AutoHotkey.exe send_team_chat.ahk "消息内容"

#Requires AutoHotkey v2.0
#SingleInstance Force

; 获取命令行参数
if A_Args.Length < 1 {
    ExitApp
}

message := A_Args[1]

; 激活LOL窗口
if WinExist("League of Legends (TM) Client") {
    WinActivate
    Sleep 300
} else if WinExist("League of Legends") {
    WinActivate
    Sleep 300
}

; 按Enter打开聊天框
Send "{Enter}"
Sleep 300

; 直接输入消息（不加/all，发送到队伍频道）
SendText message
Sleep 150

; 按Enter发送
Send "{Enter}"

ExitApp
