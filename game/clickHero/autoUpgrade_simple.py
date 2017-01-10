# -*- coding:UTF-8  -*-
"""
clicker heroes自动升级树精
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import time
import clickerHeroes


if __name__ == "__main__":
    ch = clickerHeroes.ClickerHeroes()
    while True:
        # 自动升级
        ch.auto_click(100, 370)
        time.sleep(1)
