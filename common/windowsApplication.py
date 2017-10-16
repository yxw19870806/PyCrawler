# -*- coding:UTF-8  -*-
"""
windows应用窗口处理类
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import keyboardEvent, process
import pywintypes
import time
import win32api
import win32con
import win32gui


class WindowsApplication:
    window_title = ""

    @property
    def window_handle(self):
        return win32gui.FindWindow(None, self.window_title)

    def __init__(self, window_title, default_windows_size=None):
        self.window_title = window_title
        # 设置为默认窗口大小（避免坐标产生偏移）
        if default_windows_size:
            self.set_window_size(default_windows_size[0], default_windows_size[1])
        keyboard_event_bind = {"Prior": process.pause_process, "Next": process.continue_process}
        keyboard_control_thread = keyboardEvent.KeyboardEvent(keyboard_event_bind)
        keyboard_control_thread.setDaemon(True)
        keyboard_control_thread.start()

    # 获取窗口大小
    def get_window_size(self):
        win_rect = win32gui.GetWindowRect(self.window_handle)
        return win_rect[2] - win_rect[0], win_rect[3] - win_rect[1]  # width, height

    # 获取显示大小（去除windows标题栏和边框的尺寸）
    def get_client_size(self):
        win_rect = win32gui.GetClientRect(self.window_handle)
        return win_rect[2] - win_rect[0], win_rect[3] - win_rect[1]  # width, height

    # win32gui.SetWindowPos参数详解
    # 第一个参数：窗口句柄
    # 第二个参数：窗口层级
    #   win32con.HWND_TOP：将窗口置于Z序的顶部。
    #   win32con.HWND_BOTTOM：将窗口置于Z序的底部。如果参数hWnd标识了一个顶层窗口，则窗口失去顶级位置，并且被置在其他窗口的底部。
    #   win32con.HWND_NOTOPMOST：将窗口置于所有非顶层窗口之上（即在所有顶层窗口之后）。如果窗口已经是非顶层窗口则该标志不起作用。
    #   win32con.HWND_TOPMOST：将窗口置于所有非顶层窗口之上。即使窗口未被激活窗口也将保持顶级位置。
    # 第三个参数：窗口X坐标
    # 第四个参数：窗口Y坐标
    # 第五个参数：窗口宽度
    # 第六个参数：窗口高度
    # 第七个参数：窗口尺寸和定位的标志
    #   win32con.SWP_ASNCWINDOWPOS：如果调用进程不拥有窗口，系统会向拥有窗口的线程发出需求。这就防止调用线程在其他线程处理需求的时候发生死锁。
    #   win32con.SWP_DEFERERASE：防止产生WM_SYNCPAINT消息。
    #   win32con.SWP_DRAWFRAME：在窗口周围画一个边框（定义在窗口类描述中）。
    #   win32con.SWP_FRAMECHANGED：给窗口发送WM_NCCALCSIZE消息，即使窗口尺寸没有改变也会发送该消息。如果未指定这个标志，只有在改变了窗口尺寸时才发送WM_NCCALCSIZE。
    #   win32con.SWP_HIDEWINDOW：隐藏窗口。
    #   win32con.SWP_NOACTIVATE：不激活窗口。如果未设置标志，则窗口被激活，并被设置到其他最高级窗口或非最高级组的顶部（根据参数hWndlnsertAfter设置）。
    #   win32con.SWP_NOCOPYBITS：清除客户区的所有内容。如果未设置该标志，客户区的有效内容被保存并且在窗口尺寸更新和重定位后拷贝回客户区。
    #   win32con.SWP_NOMOVE：维持当前位置（忽略第3个和第4个参数）。
    #   win32con.SWP_NOOWNERZORDER：不改变z序中的所有者窗口的位置。
    #   win32con.SWP_NOREDRAW：不重画改变的内容。如果设置了这个标志，则不发生任何重画动作。适用于客户区和非客户区（包括标题栏和滚动条）和任何由于窗回移动而露出的父窗口的所有部分。如果设置了这个标志，应用程序必须明确地使窗口无效并区重画窗口的任何部分和父窗口需要重画的部分。
    #   win32con.SWP_NOREPOSITION：与SWP_NOOWNERZORDER标志相同。
    #   win32con.SWP_NOSENDCHANGING：防止窗口接收WM_WINDOWPOSCHANGING消息。
    #   win32con.SWP_NOSIZE：维持当前尺寸（忽略第5个和第6个参数）。
    #   win32con.SWP_NOZORDER：维持当前Z序（忽略第2个参数）。
    #   win32con.SWP_SHOWWINDOW：显示窗口。
    # 设置窗口大小
    def set_window_size(self, width, height):
        win32gui.SetWindowPos(self.window_handle, 0, 0, 0, width, height, win32con.SWP_NOMOVE | win32con.SWP_NOZORDER)

    # 设置窗口坐标
    def set_window_pos(self, pos_x, pos_y):
        win32gui.SetWindowPos(self.window_handle, 0, pos_x, pos_y, 0, 0, win32con.SWP_NOSIZE | win32con.SWP_NOZORDER)

    # 自动点击窗口某个坐标（窗口可以不在最顶端）
    def auto_click(self, pos_x, pos_y, click_time=0):
        tmp = win32api.MAKELONG(pos_x, pos_y)
        win32gui.SendMessage(self.window_handle, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
        win32gui.SendMessage(self.window_handle, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, tmp)
        if click_time > 0:
            time.sleep(click_time)
        win32gui.SendMessage(self.window_handle, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, tmp)

    def move_click(self, pos_x, pos_y, click_time=0):
        win32api.SetCursorPos((pos_x, pos_y))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
        if click_time > 0:
            time.sleep(click_time)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)

    # 自动向窗口发送按键指令（必须在前台激活窗口）
    def send_key(self, keyboard):
        # key down
        win32api.PostMessage(self.window_handle, win32con.WM_KEYDOWN, keyboard, 0)
        # key up
        win32api.PostMessage(self.window_handle, win32con.WM_KEYUP, keyboard, 0)

    # 获取窗口某个坐标的颜色（窗口必须在最顶端）
    def get_color(self, pos_x, pos_y):
        try:
            color = win32gui.GetPixel(win32gui.GetDC(self.window_handle), pos_x, pos_y)
        except pywintypes.error:
            return None, None, None
        red = color & 255
        green = (color >> 8) & 255
        blue = (color >> 16) & 255
        return red, green, blue

    # 判断是否是最顶端窗口
    def is_foreground_window(self):
        return win32gui.GetForegroundWindow() == self.window_handle

    # 根据屏幕坐标获取对应窗口坐标
    def get_client_position(self, pos_x, pos_y):
        return win32gui.ScreenToClient(self.window_handle, (pos_x, pos_y))
