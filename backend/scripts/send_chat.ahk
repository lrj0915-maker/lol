; LOL游戏内聊天发送脚本
; 用法: AutoHotkey.exe send_chat.ahk "消息内容"

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
Sleep 200

; 输入消息
SendText message
Sleep 200

; 按Enter发送
Send "{Enter}"

ExitApp
