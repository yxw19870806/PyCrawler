# -*- coding:UTF-8  -*-
"""
获取所有的steam打折游戏信息
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import robot, tool
import steamCommon
import json
import os
import time
import datetime

API_UPDATE_TIME_WEEKDAY = 2  # 每周优惠更新时间（周几）
API_UPDATE_TIME_HOUR = 1  # 每周优惠更新时间（几点）
INCLUDE_GAME = True
INCLUDE_PACKAGE = True
INCLUDE_BUNDLE = True
DISCOUNT_DATA_PATH = os.path.realpath(os.path.join("discount.txt"))


# 打折游戏列表保存到文件
def save_discount_list(discount_game_list):
    tool.write_file(json.dumps(discount_game_list), DISCOUNT_DATA_PATH, 2)


# 获取文件中的打折列表
def load_discount_list():
    discount_game_list = []
    if not os.path.exists(DISCOUNT_DATA_PATH):
        return discount_game_list
    week_day = int(time.strftime("%w"))
    # 已超过本周API更新时间
    if (week_day > API_UPDATE_TIME_WEEKDAY) or (week_day == API_UPDATE_TIME_WEEKDAY and int(time.strftime("%H")) >= API_UPDATE_TIME_WEEKDAY):
        last_api_update_day = (datetime.datetime.today() + datetime.timedelta(days=API_UPDATE_TIME_WEEKDAY - week_day)).timetuple()
    #  获取上周API更新时间
    else:
        last_api_update_day = (datetime.datetime.today() + datetime.timedelta(days=API_UPDATE_TIME_WEEKDAY - week_day - 7)).timetuple()
    last_api_update_day = time.strptime(time.strftime("%Y-%m-%d " + "%02d" % API_UPDATE_TIME_HOUR + ":00:00", last_api_update_day), "%Y-%m-%d %H:%M:%S")
    last_api_update_time = time.mktime(last_api_update_day)
    if os.path.getmtime(DISCOUNT_DATA_PATH) < last_api_update_time < time.time():
        tool.print_msg("discount game list expired")
        return discount_game_list
    try:
        discount_game_list = json.loads(tool.read_file(DISCOUNT_DATA_PATH))
    except ValueError:
        pass
    except TypeError:
        pass
    return discount_game_list


# 给出给定大等于最低折扣或者小等于最低价格的所有还没有的打折游戏
# min_discount_percent  最低折扣
# min_discount_price    最低价格
def main(account_id, include_type, min_discount_percent, min_discount_price):
    # 获取登录状态
    try:
        login_cookie = steamCommon.get_login_cookie_from_browser()
    except robot.RobotException, e:
        tool.print_msg("登录状态检测失败，原因：%s" % e.message)
        raise
    # 从文件里获取打折列表
    discount_game_list = load_discount_list()
    if not discount_game_list:
        # 调用API获取打折列表
        try:
            discount_game_list = steamCommon.get_discount_game_list(login_cookie)
        except robot.RobotException, e:
            tool.print_msg("所有打折游戏解析失败，原因：%s" % e.message)
            raise
        # 将打折列表写入文件
        save_discount_list(discount_game_list)
        tool.print_msg("get discount game list from website")
    else:
        tool.print_msg("get discount game list from cache file")
    # 获取自己的所有游戏列表
    try:
        owned_game_list = steamCommon.get_account_owned_app_list(account_id)
    except robot.RobotException, e:
        tool.print_msg("个人游戏主页解析失败，原因：%s" % e.message)
        raise
    for discount_info in discount_game_list:
        # 获取到的价格不大于0的跳过
        if discount_info["now_price"] <= 0 or discount_info["old_price"] <= 0:
            continue
        # 只显示当前价格或折扣小等于限制的那些游戏
        if discount_info["now_price"] <= min_discount_price or discount_info["discount"] >= min_discount_percent:
            # bundle 或者 package，都包含多个游戏
            if discount_info["type"] == "bundle" or discount_info["type"] == "package":
                # 是否不显示package
                if discount_info["type"] == "package" and include_type & 2 == 0:
                    continue
                # 是否不显示bundle
                if discount_info["type"] == "bundle" and include_type & 4 == 0:
                    continue
                is_all = True
                # 遍历包含的全部游戏，如果都有了，则跳过
                for app_id in discount_info["app_id"]:
                    if app_id not in owned_game_list:
                        is_all = False
                        break
                if not is_all:
                    if discount_info["type"] == "bundle":
                        tool.print_msg("http://store.steampowered.com/bundle/%s/ ,discount %s%%, old price: %s, discount price: %s" % (discount_info["id"], discount_info["discount"], discount_info["old_price"], discount_info["now_price"]), False)
                    else:
                        tool.print_msg("http://store.steampowered.com/sub/%s ,discount %s%%, old price: %s, discount price: %s" % (discount_info["id"], discount_info["discount"], discount_info["old_price"], discount_info["now_price"]), False)
            else:
                if include_type & 1 == 0:
                    continue
                if discount_info["app_id"] not in owned_game_list:
                    tool.print_msg("http://store.steampowered.com/app/%s/ ,discount %s%%, old price: %s, discount price: %s" % (discount_info["id"], discount_info["discount"], discount_info["old_price"], discount_info["now_price"]), False)


if __name__ == "__main__":
    include_type_id = 0
    if INCLUDE_GAME:
        include_type_id += 1
    if INCLUDE_PACKAGE:
        include_type_id += 2
    if INCLUDE_BUNDLE:
        include_type_id += 4

    main(steamCommon.get_account_id_from_file(), include_type_id, 90, 1)
