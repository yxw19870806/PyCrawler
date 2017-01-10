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
    count = 0
    while True:
        # 自动升级
        ch.auto_click(100, 370)
        # 判断指定制定坐标，是不是出现了装备宝箱，如果出现了就打开并关闭弹出界面
        red, green, blue = ch.get_color(570, 410)
        if red == 255 and 250 <= green <= 253 and 190 <= blue <= 210:
            ch.auto_click(575, 370)
            time.sleep(1)
            ch.auto_click(920, 125)
            print "open equip box"
        # 每隔60秒检查一次是否启动了自动通关模式（战斗失败会自动关闭）
        if count >= 60:
            is_find = False
            for pos_x in range(1110, 1130):
                for pos_y in range(240, 260):
                    red, green, blue = ch.get_color(pos_x, pos_y)
                    if red == 255 and green == 0 and blue == 0:
                        ch.auto_click(1120, 250)
                        print "continue battle"
                        is_find = True
                        break
                if is_find:
                    break
            count = 0
        time.sleep(1)
        count += 1