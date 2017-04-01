# -*- coding:UTF-8  -*-
"""
steam相关数据解析爬虫
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import net, robot, tool
from pyquery import PyQuery as pq
import os
import re


# 获取所有已经没有剩余卡牌掉落且还没有收集完毕的徽章详细地址
def get_self_account_badges(account_id, login_cookie):
    # 徽章第一页
    badges_index_page_url = "http://steamcommunity.com/profiles/%s/badges/" % account_id
    cookies_list = {
        "steamLogin": login_cookie,
    }
    badges_index_page_response = net.http_request(badges_index_page_url, cookies_list=cookies_list)
    if badges_index_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        tool.print_msg("第一页徽章访问失败")
        tool.process_exit()
    badges_detail_url_list = []
    # 所有徽章div
    badges_selector = pq(badges_index_page_response.data).find(".maincontent .badges_sheet .badge_row")
    for index in range(0, badges_selector.size()):
        badge_html = badges_selector.eq(index).html().encode("utf-8")
        # 已经掉落全部卡牌的徽章
        if badge_html.find("无剩余卡牌掉落") >= 0:
            # 徽章详细信息页面地址
            badge_detail_page_url = tool.find_sub_string(badge_html, '<a class="badge_row_overlay" href="', '"/>')
            if badge_detail_page_url:
                badges_detail_url_list.append(badge_detail_page_url)
            else:
                tool.print_msg("%s 没有解析到徽章详细界面地址" % badge_html)
                tool.process_exit()
    # ['http://steamcommunity.com/profiles/76561198172925593/gamecards/459820/', 'http://steamcommunity.com/profiles/76561198172925593/gamecards/357200/', 'http://steamcommunity.com/profiles/76561198172925593/gamecards/502740/', 'http://steamcommunity.com/profiles/76561198172925593/gamecards/359600/', 'http://steamcommunity.com/profiles/76561198172925593/gamecards/354380/', 'http://steamcommunity.com/profiles/76561198172925593/gamecards/359670/', 'http://steamcommunity.com/profiles/76561198172925593/gamecards/525300/', 'http://steamcommunity.com/profiles/76561198172925593/gamecards/337980/', 'http://steamcommunity.com/profiles/76561198172925593/gamecards/591420/']
    return badges_detail_url_list


# 获取指定徽章仍然缺少的集换式卡牌名字和对应缺少的数量
# badge_detail_page_url -> http://steamcommunity.com/profiles/76561198172925593/gamecards/459820/
def get_self_account_badge_card(badge_detail_page_url, login_cookie):
    cookies_list = {
        "steamLogin": login_cookie,
    }
    badge_detail_page_response = net.http_request(badge_detail_page_url, cookies_list=cookies_list)
    if badge_detail_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        tool.print_msg("徽章详细页%s访问失败" % badge_detail_page_url)
        tool.process_exit()
    wanted_card_list = {}
    page_selector = pq(badge_detail_page_response.data)
    # 徽章等级
    badge_level = 0
    badge_selector = page_selector.find(".maincontent .badge_current .badge_info")
    # 有等级
    if badge_selector.find(".badge_info_description").size() == 1:
        badge_level_find = re.findall("(\d) 级, [\d]00 点经验值", badge_selector.find(".badge_info_description div").eq(1).text().encode("utf-8"))
        if len(badge_level_find) == 1 and robot.is_integer(badge_level_find[0]):
            badge_level = int(badge_level_find[0])
        else:
            tool.print_msg("徽章详细页%s等级解析失败" % badge_detail_page_url)
            tool.process_exit()
    wanted_count = 5 - badge_level
    # 所有集换式卡牌div
    cards_selector = page_selector.find(".maincontent .badge_detail_tasks .badge_card_set_card")
    for card_index in range(0, cards_selector.size()):
        card_selector = cards_selector.eq(card_index)
        owned_count_selector = card_selector.find(".badge_card_set_text .badge_card_set_text_qty")
        card_name = card_selector.find(".badge_card_set_text").eq(0).remove(".badge_card_set_text_qty").text()
        if owned_count_selector.size() == 1:
            owned_count = owned_count_selector.text().replace("(", "").replace(")", "")
        else:
            owned_count = 0
        if int(owned_count) < wanted_count:
            wanted_card_list[card_name] = wanted_count - int(owned_count)
    # {'Mio': 2}
    return wanted_card_list


# 获取某个游戏的集换式卡牌市场售价
def get_market_game_trade_card_price(game_id, login_cookie):
    cookies_list = {
        "steamLogin": login_cookie,
    }
    market_search_page_url = "http://steamcommunity.com/market/search/render/"
    market_search_page_url += "?query=&count=20&appid=753&category_753_Game[0]=tag_app_%s&category_753_cardborder[0]=tag_cardborder_0" % game_id
    market_search_page_response = net.http_request(market_search_page_url, cookies_list=cookies_list, json_decode=True)
    if market_search_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        tool.print_msg("游戏%s市场页访问失败" % game_id)
        tool.process_exit()
    market_item_list = {}
    if "success" in market_search_page_response.json_data and market_search_page_response.json_data["success"] and "results_html" in market_search_page_response.json_data:
        card_selector = pq(market_search_page_response.json_data["results_html"]).find(".market_listing_row_link")
        for index in range(0, card_selector.size()):
            # print card_selector.eq(index).html()
            card_name = card_selector.eq(index).find(".market_listing_item_name").text()
            card_min_price = card_selector.eq(index).find("span.normal_price span.normal_price").text().encode("utf-8").replace("¥ ", "")
            market_item_list[card_name] = card_min_price
    # {'Pamu': '1.77', 'Fumi (Trading Card)': '2.14', 'Mio (Trading Card)': '1.33', 'Bonnibel (Trading Card)': '1.49', 'Groupshot': '1.87', 'Q-Piddy': '1.35', 'Elle (Trading Card)': '1.19', 'Quill': '1.50', 'Iro (Trading Card)': '1.42', 'Bearverly (Trading Card)': '1.27', 'Cassie (Trading Card)': '1.35'}
    return market_item_list


# 从浏览器中获取登录cookies
def get_login_cookie_from_browser():
    config = robot.read_config(os.path.join(os.getcwd(), "..\\common\\config.ini"))
    # 操作系统&浏览器
    browser_type = robot.get_config(config, "BROWSER_TYPE", 2, 1)
    # cookie
    is_auto_get_cookie = robot.get_config(config, "IS_AUTO_GET_COOKIE", True, 4)
    if is_auto_get_cookie:
        cookie_path = robot.tool.get_default_browser_cookie_path(browser_type)
    else:
        cookie_path = robot.get_config(config, "COOKIE_PATH", "", 0)
    all_cookie_from_browser = tool.get_all_cookie_from_browser(browser_type, cookie_path)
    if "store.steampowered.com" in all_cookie_from_browser:
        if "steamLogin" in all_cookie_from_browser["store.steampowered.com"]:
            return all_cookie_from_browser["store.steampowered.com"]["steamLogin"]
    tool.print_msg("登录cookie获取失败")
    tool.process_exit()
    return None
