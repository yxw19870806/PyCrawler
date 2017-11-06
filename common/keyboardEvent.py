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


SUPPORT_KEYBOARD_LIST = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S",
                       "T", "U", "V", "W", "X", "Y", "Z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "F1", "F2",
                       "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12", "NUMPAD0", "NUMPAD1", "NUMPAD2",
                       "NUMPAD3", "NUMPAD4", "NUMPAD5", "NUMPAD6", "NUMPAD7", "NUMPAD8", "NUMPAD9", "INSERT", "HOME",
                       "PRIOR", "DELETE", "END", "NEXT", "OEM_1", "OEM_2", "OEM_3", "OEM_4", "OEM_5", "OEM_6", "OEM_7",
                       "OEM_COMMA", "OEM_PERIOD", "ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "DECIMAL"]

SUPPORT_SUB_KEYBOARD_LIST = {
    "CTRL": "CONTROL",
    "SHIFT": "SHIFT",
    "ALT": "MENU",
}


class KeyboardEvent(threading.Thread):
    """Keyboard Event Listener Class"""
    key_down_list ={
        "LSHIFT": False,
        "RSHIFT": False,
        "LCONTROL": False,
        "RCONTROL": False,
        "LMENU": False,
        "RMENU": False,
    }
    # 按键名 => 回调方法名
    event_key_list = {}

    def __init__(self, event_list):
        """Init keyboard Event Listener

        :param event_list:
            dictionary of key and trigger function
            key name => event function object
        """
        threading.Thread.__init__(self)
        for key, function in event_list.iteritems():
            event_function = event_list[key]
            key = str(key).upper()
            # 如果使用+号连接的组合键
            if key.find("+") >= 0:
                sub_key, key = key.split("+", 1)
                sub_key = sub_key.strip()
                # 不在支持的组合键控制按键中
                if sub_key not in SUPPORT_SUB_KEYBOARD_LIST:
                    continue
                sub_key = SUPPORT_SUB_KEYBOARD_LIST[sub_key] + " "
                key = key.strip()
            else:
                sub_key = ""
            # 判断是否在支持的按键里
            if key in SUPPORT_KEYBOARD_LIST:
                self.event_key_list[sub_key + key] = event_function

    # 按键判断并执行方法
    def on_keyboard_down(self, event):
        """Function of key down event listener"""
        key = str(event.Key).upper()
        # 组合键按下，本身没有单独的事件
        if key in self.key_down_list:
            self.key_down_list[key] = True
        else:
            # 如果有任意功能键按下，那么只判断组合键
            if True in self.key_down_list.values():
                for sub_key in ["SHIFT", "CONTROL", "MENU"]:
                    # 如果功能键有按下
                    if self.key_down_list["L" + sub_key] or self.key_down_list["R" + sub_key]:
                        if sub_key + " " + key in self.event_key_list:
                            self.event_key_list[sub_key + " " + key]()
            else:
                if key in self.event_key_list:
                    self.event_key_list[key]()

    def on_keyboard_up(self, event):
        """Function of key up event listener"""
        key = str(event.Key).upper()
        # 组合键归位
        if key in self.key_down_list:
            self.key_down_list[key] = False

    def run(self):
        """Start listener"""
        hook_manager = pyHook.HookManager()
        hook_manager.KeyDown = self.on_keyboard_down
        hook_manager.KeyUp = self.on_keyboard_up
        hook_manager.HookKeyboard()
        pythoncom.PumpMessages()
