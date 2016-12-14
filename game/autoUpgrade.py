# -*- coding:UTF-8  -*-
"""
模拟点击clicker heroes后台窗口指定坐标
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import time
import win32api
import win32con
import win32gui


windows_title = "Clicker Heroes"
pos_x = 100
pos_y = 370


# 升级树精等级，默认窗口大小，滚动条在最上方
def auto_upgrade():
    handle = win32gui.FindWindow(None, windows_title)
    tmp = win32api.MAKELONG(pos_x, pos_y)
    win32gui.SendMessage(handle, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
    win32gui.SendMessage(handle, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, tmp)
    win32gui.SendMessage(handle, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, tmp)

if __name__ == "__main__":
    while True:
        auto_upgrade()
        time.sleep(1)
