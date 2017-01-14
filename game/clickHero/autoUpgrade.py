# -*- coding:UTF-8  -*-
"""
clicker heroes自动升级树精
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import time
import clickerHeroes


# 检测遗物宝箱
# 如果有检测到宝箱并点击开启后返回True
def check_relic_box():
    red, green, blue = ch.get_color(570, 410)
    if red == 255 and 250 <= green <= 253 and 190 <= blue <= 210:
        ch.auto_click(575, 370)
        time.sleep(1)
        ch.auto_click(920, 125)
        return True
    return False


# 检测自动通过模式
# 如果有检测到自动通关模式被关闭，开启后返回
def check_progression_mode():
    for pos_x, pos_y in clickerHeroes.PROGRESSION_MODE_CHECK_POSITION:
        red, green, blue = ch.get_color(pos_x, pos_y)
        if red == 255 and green == 0 and blue == 0:
            ch.auto_click(1110, 250)
            return True
    return False


if __name__ == "__main__":
    ch = clickerHeroes.ClickerHeroes()

    count = 0
    # todo 根据当前窗口大小，自适应坐标位置
    # (点击升级的按钮位置，1 ~ 4），保证升级窗口中第一个按钮完整显示）
    click_button_index = 1
    click_x, click_y = clickerHeroes.UPGRADE_BUTTON_POS[click_button_index]
    is_open_equip_box = False
    while True:
        while clickerHeroes.PROCESS_STATUS == clickerHeroes.PROCESS_STATUS_PAUSE:
            time.sleep(1)
        # 自动升级
        ch.auto_click(click_x, click_y)

        # 每10分钟检测一次
        if count >= 600:
            # 只有窗口置顶时才进行判断
            if ch.is_foreground_window():
                # 检测宝箱，并且只要开启过一次后就不再检测
                if not is_open_equip_box and check_relic_box():
                    is_open_equip_box = True
                    print "open relic box"

                if check_progression_mode():
                    print "enable progression mode"
            # 重置计数
            count = 0

        time.sleep(1)
        count += 1
