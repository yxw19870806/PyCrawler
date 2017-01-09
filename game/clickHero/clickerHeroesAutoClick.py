# -*- coding:UTF-8  -*-
"""
模拟点击clicker heroes后台窗口指定坐标
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import win32api
import win32con
import win32gui


def auto_click(pos_x, pos_y):
    windows_title = "Clicker Heroes"
    handle = win32gui.FindWindow(None, windows_title)
    tmp = win32api.MAKELONG(pos_x, pos_y)
    win32gui.SendMessage(handle, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
    win32gui.SendMessage(handle, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, tmp)
    win32gui.SendMessage(handle, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, tmp)
