# -*- coding:UTF-8  -*-
"""
clicker heroes窗口处理类
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import pywintypes
import win32api
import win32con
import win32gui


class ClickerHeroes():
    def __init__(self):
        windows_title = "Clicker Heroes"
        self.window_handle = win32gui.FindWindow(None, windows_title)

    def auto_click(self, pos_x, pos_y):
        tmp = win32api.MAKELONG(pos_x, pos_y)
        win32gui.SendMessage(self.window_handle, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
        win32gui.SendMessage(self.window_handle, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, tmp)
        win32gui.SendMessage(self.window_handle, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, tmp)

    def get_color(self, pos_x, pos_y):
        try:
            color = win32gui.GetPixel(win32gui.GetDC(self.window_handle), pos_x, pos_y)
        except pywintypes.error, e:
            return None, None, None
        red = color & 255
        green = (color >> 8) & 255
        blue = (color >> 16) & 255
        return red, green, blue
