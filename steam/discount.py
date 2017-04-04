# -*- coding:UTF-8  -*-
"""
获取所有的steam打折游戏信息
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import tool
import steamCommon
import json
import os


# 打折游戏列表保存到文件
def save_discount_list(discount_game_list):
    tool.write_file(json.dumps(discount_game_list), "discount.txt", 2)


# 获取文件中的打折列表
def load_discount_list():
    file_path = os.path.join("discount.txt")
    if not os.path.exists(file_path):
        return []
    file_handle = open("discount.txt", "r")
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
def main(account_id, min_discount_percent, min_discount_price):
    discount_game_list = load_discount_list()
    if not discount_game_list:
        discount_game_list = steamCommon.get_discount_game_list()
        save_discount_list(discount_game_list)
        tool.print_msg("get discount game list from website", False)
    else:
        tool.print_msg("get discount game list from cache file", False)
    owned_game_list = steamCommon.get_account_owned_app_list(account_id)
    for discount_info in discount_game_list:
        if discount_info["now_price"] <= min_discount_price or discount_info["discount"] >= min_discount_percent:
            if isinstance(discount_info["game_id"], list):
                for game_id in discount_info["game_id"]:
                    if game_id not in owned_game_list:
                        if "package_id" in discount_info:
                            tool.print_msg("http://store.steampowered.com/sub/%s ,discount %s%%, old price: %s, discount price: %s" % (discount_info["package_id"], discount_info["discount"], discount_info["old_price"], discount_info["now_price"]), False)
                        else:
                            tool.print_msg("http://store.steampowered.com/app/%s/ ,discount %s%%, old price: %s, discount price: %s" % (discount_info["game_id"], discount_info["discount"], discount_info["old_price"], discount_info["now_price"]), False)
            else:
                if discount_info["game_id"] not in owned_game_list:
                    tool.print_msg("http://store.steampowered.com/app/%s/ ,discount %s%%, old price: %s, discount price: %s" % (discount_info["game_id"], discount_info["discount"], discount_info["old_price"], discount_info["now_price"]), False)


if __name__ == "__main__":
    main(76561198172925593, 90, 1)