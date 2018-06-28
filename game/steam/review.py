# -*- coding:UTF-8  -*-
"""
获取steam全部打折游戏信息
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import json
import os
from common import output, crawler, tool
import steamCommon

REVIEW_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "data\\review.txt"))


# 保存评测记录到文件
def save_discount_list(review_data):
    tool.write_file(json.dumps(review_data), REVIEW_DATA_PATH, tool.WRITE_FILE_TYPE_REPLACE)


# 获取历史评测记录
def load_review_list():
    review_data = {
        "can_review_lists": [],
        "dlc_in_game": {},
        "review_list": [],
    }
    if not os.path.exists(REVIEW_DATA_PATH):
        return review_data
    review_data = tool.json_decode(tool.read_file(REVIEW_DATA_PATH), review_data)
    return review_data


def main(account_id):
    # 获取登录状态
    try:
        steamCommon.init_cookie_from_browser()
    except crawler.CrawlerException, e:
        output.print_msg("登录状态检测失败，原因：%s" % e.message)
        raise
    # 历史记录
    review_data = load_review_list()
    # 获取自己的全部玩过的游戏列表
    try:
        played_game_list = steamCommon.get_account_owned_app_list(account_id, True)
    except crawler.CrawlerException, e:
        output.print_msg("个人游戏主页解析失败，原因：%s" % e.message)
        raise
    for game_id in played_game_list:
        game_id = int(game_id)
        # 获取游戏信息
        game_data = steamCommon.get_game_store_index(game_id)

        # 有DLC的话，遍历每个DLC
        for dlc_id in game_data["dlc_list"]:
            dlc_id = int(dlc_id)

            # 已经评测过了，跳过检查
            if dlc_id in review_data["review_list"]:
                continue

            # DLC和游戏本体关系字典
            review_data["dlc_in_game"][dlc_id] = game_id

            # 获取DLC信息
            dlc_data = steamCommon.get_game_store_index(dlc_id)

            if dlc_data["owned"]:
                # 已经评测过了
                if dlc_data["reviewed"]:
                    # 从待评测列表中删除
                    if dlc_id in review_data["can_review_lists"]:
                        review_data["can_review_lists"].remove(dlc_id)
                    # 增加已评测记录
                    if dlc_id not in review_data["review_list"]:
                        review_data["review_list"].append(dlc_id)
                # 新的可以评测游戏
                else:
                    if dlc_id not in review_data["can_review_lists"]:
                        review_data["can_review_lists"].append(dlc_id)

        # 已经评测过了
        if game_data["reviewed"]:
            # 从待评测列表中删除
            if game_id in review_data["can_review_lists"]:
                review_data["can_review_lists"].remove(game_id)
            # 增加已评测记录
            if game_id not in review_data["review_list"]:
                review_data["review_list"].append(game_id)
        # 新的可以评测游戏
        else:
            if game_id not in review_data["can_review_lists"]:
                review_data["can_review_lists"].append(game_id)

        # 增加检测标记
        save_discount_list(review_data)


# 打印列表
# print_type  0 全部游戏
# print_type  1 只要本体
# print_type  2 只要DLC
# print_type  3 只要本体已评测的DLC
def print_list(print_type=0):
    review_data = load_review_list()
    for game_id in review_data["can_review_lists"]:
        # 是DLC
        if str(game_id) in review_data["dlc_in_game"]:
            if print_type == 1:
                continue
            # 本体没有评测过
            if review_data["dlc_in_game"][str(game_id)] in review_data["can_review_lists"]:
                if print_type == 3:
                    continue
        else:
            if print_type == 2 or print_type == 3:
                continue
        output.print_msg("https://store.steampowered.com/app/%s" % game_id)


if __name__ == "__main__":
    main(steamCommon.get_account_id_from_file())
    print_list()
