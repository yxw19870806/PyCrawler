# -*- coding:UTF-8  -*-
"""
获取所有的steam游戏ID
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import tool
import json
import time


def get_owned_app_list(user_id):
    tool.quickly_set(1, 0)
    game_index_url = "http://steamcommunity.com/profiles/%s/games/?tab=all" % user_id
    game_index_page_return_code, game_index_page = tool.http_request(game_index_url)[:2]
    if game_index_page_return_code == 1:
        owned_all_game_data = tool.find_sub_string(game_index_page, "var rgGames = ", ";")
        try:
            owned_all_game_data = json.loads(owned_all_game_data)
        except ValueError:
            pass
        else:
            app_id_list = []
            for game_data in owned_all_game_data:
                if "appid" in game_data:
                    app_id_list.append(str(game_data["appid"]))
            return app_id_list
