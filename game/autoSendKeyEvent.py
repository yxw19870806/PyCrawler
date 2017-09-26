# -*- coding:UTF-8  -*-
"""
向指定窗口持续发送特定按键事件
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import time
import win32api
import win32con
import win32gui

WINDOW_TITLE = ""
KEYBOARD = ""

if __name__ == "__main__":
    while True:
        # 寻找窗口句柄
        window_handle = win32gui.FindWindow(None, WINDOW_TITLE)
        # key down
        win32api.PostMessage(window_handle, win32con.WM_KEYDOWN, KEYBOARD, 0)
        # key up
        win32api.PostMessage(window_handle, win32con.WM_KEYUP, win32con.VK_LEFT, 0)
        time.sleep(0.3)
