# -*- coding:UTF-8  -*-
"""
获取指定账号的全部含有异常成就的游戏
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import tool
import astatsCommon, steamCommon


def main(account_id):
    owned_game_list = steamCommon.get_account_owned_app_list(account_id)
    for game_id in owned_game_list:
        tool.print_msg("开始解析游戏 %s" % game_id)
        astatsCommon.get_game_invalid_achievements(game_id)

if __name__ == "__main__":
    main(steamCommon.get_account_id_from_file())
