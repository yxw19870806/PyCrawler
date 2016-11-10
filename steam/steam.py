# -*- coding:UTF-8  -*-
"""
steam相关数据解析爬虫
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import tool
import json
import re


# 读取cookies后获取指定账号的全部游戏列表
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


# 获取所有打折游戏列表
def get_discount_list():
    page_count = 1
    total_page_count = 99
    discount_list = []
    while page_count <= total_page_count:
        index_url = "http://store.steampowered.com/search/results"
        index_url += "?sort_by=Price_ASC&category1=998&os=win&specials=1&page=%s" % page_count
        index_page_return_code, index_page = tool.http_request(index_url)[:2]
        if index_page_return_code != 1:
            break
        items_page = tool.find_sub_string(index_page, "<!-- List Items -->", "<!-- End List Items -->")
        items_page = tool.find_sub_string(items_page, "<a href=", None)
        items_page = items_page.replace("\n", "").replace("\r", "").replace("<a href=", "\n<a href=")
        items = items_page.split("\n")
        for item in items:
            app_id = tool.find_sub_string(item, 'data-ds-appid="', '"')
            discount_data = tool.find_sub_string(item, '<div class="col search_discount responsive_secondrow">', "</div>")
            discount = tool.find_sub_string(discount_data, "<span>", "</span>").replace("-", "").replace("%", "")
            if not discount:
                discount = 0
            price_data = tool.find_sub_string(item, '<div class="col search_price discounted responsive_secondrow">', "</div>", 2)
            old_price = tool.find_sub_string(price_data, '<strike>', '</strike>').replace("¥", "").strip()
            if not old_price:
                old_price = 0
            new_price = tool.find_sub_string(price_data, '<br>', '</div>').replace("¥", "").strip()
            if not new_price:
                new_price = 0
            discount_list.append("%s\t%s\t%s\t%s" % (app_id, discount, old_price, new_price))
        if total_page_count == 99:
            pagination_page = tool.find_sub_string(index_page, '<div class="search_pagination">', None)
            page_find = re.findall('return false;">([\d]*)</a>', pagination_page)
            if len(page_find) > 0:
                total_page_count = 0
                for page_id in page_find:
                    total_page_count = max(total_page_count, int(page_id))
        page_count += 1
    return discount_list
