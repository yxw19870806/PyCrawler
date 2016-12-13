# -*- coding:UTF-8  -*-
"""
键盘事件监控类
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import pythoncom
import pyHook
import threading


class KeyboardEvent(threading.Thread):
    def __init__(self, event_list):
        threading.Thread.__init__(self)
        # 按键 => 回调方法名
        filter_event_list = {}
        for key, function in event_list.iteritems():
            key = key.capitalize()
            # 判断是否在支持的按键里
            if key in ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S",
                       "T", "U", "V", "W", "X", "Y", "Z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "F1", "F2",
                       "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12", "Numpad0", "Numpad1", "Numpad2",
                       "Numpad3", "Numpad4", "Numpad5", "Numpad6", "Numpad7", "Numpad8", "Numpad9", "Insert", "Home",
                       "Prior", "Delete", "End", "Next", "Oem_1", "Oem_2", "Oem_3", "Oem_4", "Oem_5", "Oem_6", "Oem_7",
                       "Oem_Comma", "Oem_Period", "Add", "Subtract", "Multiply", "Divide", "Decimal"]:
                filter_event_list[key] = event_list[key]
        self.event_key_list = filter_event_list

    # 按键判断并执行方法
    def on_keyboard_event(self, event):
        if event.Key in self.event_key_list:
            self.event_key_list[event.Key]()

    # 监听所有键盘事件
    def run(self):
        hook_manager = pyHook.HookManager()
        hook_manager.KeyDown = self.on_keyboard_event
        hook_manager.HookKeyboard()
        pythoncom.PumpMessages()
