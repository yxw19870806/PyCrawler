# -*- coding:UTF-8  -*-
"""
clicker heroes自动点击怪物
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import time
import clickerHeroes


if __name__ == "__main__":
    ch = clickerHeroes.ClickerHeroes()
    while True:
        ch.auto_click(865, 410)
        time.sleep(0.01)