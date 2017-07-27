# -*- coding:UTF-8  -*-
"""
获取所有的steam打折游戏信息
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import json
import os

from common import tool
import steamCommon

INCLUDE_GAME = True
INCLUDE_PACKAGE = True
INCLUDE_BUNDLE = True
DISCOUNT_DATA_PATH = os.path.join("discount.txt")


# 打折游戏列表保存到文件
def save_discount_list(discount_game_list):
    tool.write_file(json.dumps(discount_game_list), DISCOUNT_DATA_PATH, 2)


# 获取文件中的打折列表
def load_discount_list():
    if not os.path.exists(DISCOUNT_DATA_PATH):
        return []
    file_handle = open(DISCOUNT_DATA_PATH, "r")
    discount_game_list = []
    try:
        discount_game_list = json.loads(file_handle.read())
    except ValueError:
        pass
    except TypeError:
        pass
    file_handle.close()
    return discount_game_list


# 给出给定大等于最低折扣或者小等于最低价格的所有还没有的打折游戏
# min_discount_percent  最低折扣
# min_discount_price    最低价格
def main(account_id, include_type, min_discount_percent, min_discount_price):
    login_cookie = steamCommon.get_login_cookie_from_browser()
    discount_game_list = load_discount_list()
    if not discount_game_list:
        discount_game_list = steamCommon.get_discount_game_list(login_cookie)
        save_discount_list(discount_game_list)
        tool.print_msg("get discount game list from website", False)
    else:
        tool.print_msg("get discount game list from cache file", False)
    owned_game_list = steamCommon.get_account_owned_app_list(account_id)
    for discount_info in discount_game_list:
        if discount_info["now_price"] > 0 and discount_info["old_price"] > 0 and (discount_info["now_price"] <= min_discount_price or discount_info["discount"] >= min_discount_percent):
            # bundle 或者 package，都包含多个游戏
            if discount_info["type"] == "bundle" or discount_info["type"] == "package":
                if discount_info["type"] == "package" and include_type & 2 == 0:
                    continue
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
