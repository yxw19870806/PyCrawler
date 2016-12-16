# -*- coding:UTF-8  -*-
"""
Crush Crush连续快进时间
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import datetime
import win32api
import time


def set_system_time(year, month, day, hour, minute, second):
    win32api.SetSystemTime(year, month, datetime.date(year, month, day).weekday(), day, hour, minute, second, 0)


if __name__ == "__main__":
    while True:
        set_system_time(2005, 1, 1, 0, 0, 0)
        time.sleep(0.2)
        set_system_time(2035, 1, 1, 0, 0, 0)
        time.sleep(0.2)
