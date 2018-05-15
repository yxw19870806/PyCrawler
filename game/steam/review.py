# -*- coding:UTF-8  -*-
"""
获取steam全部打折游戏信息
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import output, crawler, tool
import steamCommon
import json
import os
import time
import datetime

REVIEW_DATA_PATH = os.path.realpath(os.path.join("review.txt"))


# 打折游戏列表保存到文件
def save_discount_list(review_data):
    tool.write_file(json.dumps(review_data), REVIEW_DATA_PATH, tool.WRITE_FILE_TYPE_REPLACE)


# 获取文件中的打折列表
def load_discount_list():
    review_data = {
        "checked_list": [],
        "owned_dlc": [],
        "review_list": [],
        "can_review_lists": [],
    }
    if not os.path.exists(REVIEW_DATA_PATH):
        return review_data
    review_data = tool.json_decode(tool.read_file(REVIEW_DATA_PATH), review_data)
    return review_data


def main(account_id):
    # 获取登录状态
    try:
        cookies_list = steamCommon.get_cookie_from_browser()
    except crawler.CrawlerException, e:
        output.print_msg("登录状态检测失败，原因：%s" % e.message)
        raise
    # 获取自己的全部玩过的游戏列表
    try:
        played_game_list = steamCommon.get_account_owned_app_list(account_id, True)
    except crawler.CrawlerException, e:
        output.print_msg("个人游戏主页解析失败，原因：%s" % e.message)
        raise
    # 历史记录
    review_data = load_discount_list()
    for game_id in played_game_list:
        game_id = int(game_id)
        # 已经检测过
        if game_id in review_data["checked_list"]:
            continue
        game_data = steamCommon.get_game_store_index(game_id, cookies_list)
        # 有DLC的话，遍历每个DLC
        for dlc_id in game_data["dlc_list"]:
            dlc_id = int(dlc_id)
            dlc_data = steamCommon.get_game_store_index(dlc_id, cookies_list)
            if dlc_data["owned"]:
                # 是否评测过
                if dlc_data["reviewed"]:
                    review_data["review_list"].append(dlc_id)
                else:
                    review_data["can_review_lists"].append(dlc_id)
        # 是否评测过
        if game_data["reviewed"]:
            review_data["review_list"].append(game_id)
        else:
            review_data["can_review_lists"].append(game_id)
        # 增加检测标记
        review_data["checked_list"].append(game_id)
        save_discount_list(review_data)


if __name__ == "__main__":
    main(steamCommon.get_account_id_from_file())
