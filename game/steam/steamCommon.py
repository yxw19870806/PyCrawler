# -*- coding:UTF-8  -*-
"""
steam相关数据解析爬虫
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import os
import re
from pyquery import PyQuery as pq
from common import *

INVENTORY_ITEM_TYPE_GEM = "Gems"
INVENTORY_ITEM_TYPE_TRADE_CARD = "Trading Card"
INVENTORY_ITEM_TYPE_PROFILE_BACKGROUND = "Profile Background"
INVENTORY_ITEM_TYPE_EMOTICON = "Emoticon"

COOKIE_INFO = None
ACCOUNT_ID_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "data\\account.data"))


# 从文件中读取account id，如果不存在提示输入
def get_account_id_from_file():
    account_id = tool.read_file(ACCOUNT_ID_FILE_PATH)
    while not account_id:
        console_account_id = output.console_input(crawler.get_time() + " 请输入STEAM账号ID: ")
        while True:
            input_str = output.console_input(crawler.get_time() + " 是否使用输入的STEAM账号ID '%s' 是Y(es) / 否N(o) ?" % console_account_id)
            input_str = input_str.lower()
            if input_str in ["y", "yes"]:
                account_id = console_account_id
                tool.write_file(console_account_id, ACCOUNT_ID_FILE_PATH, tool.WRITE_FILE_TYPE_REPLACE)
                break
            elif input_str in ["n", "no"]:
                break
    return account_id


# 从浏览器中获取登录cookies
def init_cookie_from_browser():
    global COOKIE_INFO
    # 获取cookies
    all_cookie_from_browser = crawler.quickly_get_all_cookies_from_browser()
    if "store.steampowered.com" not in all_cookie_from_browser:
        raise crawler.CrawlerException("浏览器解析cookies失败\n%s" % all_cookie_from_browser)
    COOKIE_INFO = all_cookie_from_browser["store.steampowered.com"]
    login_url = "https://store.steampowered.com/login/checkstoredlogin/?redirectURL="
    login_response = net.http_request(login_url, method="GET", cookies_list=all_cookie_from_browser["store.steampowered.com"], is_auto_redirect=False)
    if login_response.status != 302:
        raise crawler.CrawlerException("登录返回code不正确，\n%s\n%s" % (login_response.status, login_response.data))
    set_cookies = net.get_cookies_from_response_header(login_response.headers)
    if "steamLogin" not in set_cookies:
        raise crawler.CrawlerException("登录返回cookies不正确，\n%s" % set_cookies)
    COOKIE_INFO.update(set_cookies)
    # 强制使用英文
    COOKIE_INFO["Steam_Language"] = "english"


# 获取全部正在打折的游戏列表
def get_discount_game_list():
    page_count = 1
    discount_game_list = []
    app_id_list = []
    while True:
        output.print_msg("开始解析第%s页打折游戏" % page_count)
        discount_game_pagination_url = "http://store.steampowered.com/search/results?sort_by=Price_ASC&category1=996,998&os=win&specials=1&page=%s" % page_count
        discount_game_pagination_response = net.http_request(discount_game_pagination_url, method="GET", cookies_list=COOKIE_INFO)
        if discount_game_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
            raise crawler.CrawlerException("第%s页打折游戏解析失败" % page_count)
        search_result_selector = pq(discount_game_pagination_response.data).find("#search_result_container")
        game_list_selector = search_result_selector.find("div").eq(1).find("a")
        for game_index in range(0, game_list_selector.length):
            game_selector = game_list_selector.eq(game_index)
            # game app id
            app_id = game_selector.attr("data-ds-appid")
            package_id = game_selector.attr("data-ds-packageid")
            bundle_id = game_selector.attr("data-ds-bundleid")
            # 不同类型取对应唯一id
            if bundle_id is not None:
                prime_id = bundle_id
                game_type = "bundle"
                bundle_info = game_selector.attr("data-ds-bundle-data")
                app_id = []
                if bundle_info:
                    # 包含的全部app_id
                    app_id_find = re.findall('"m_rgIncludedAppIDs":\[([^\]]*)\]', bundle_info)
                    for temp_id_list in app_id_find:
                        temp_id_list = temp_id_list.split(",")
                        app_id += temp_id_list
                else:
                    output.print_msg("bundle_info not found\n%s" % game_selector.html().encode("UTF-8"))
            elif package_id is not None:
                prime_id = package_id
                game_type = "package"
                # package，包含多个游戏
                if app_id.find(",") >= 0:
                    app_id = app_id.split(",")
            else:
                prime_id = app_id
                game_type = "game"
            # 过滤那些重复的游戏
            if prime_id in app_id_list:
                continue
            app_id_list.append(prime_id)
            # discount
            discount = filter(str.isdigit, game_selector.find(".search_discount span").text().encode("UTF-8"))
            # old price
            old_price = filter(str.isdigit, game_selector.find(".search_price span strike").text().encode("UTF-8"))
            # now price
            now_price = filter(str.isdigit, game_selector.find(".search_price").remove("span").text().encode("UTF-8"))
            # 如果没有取到，给个默认值
            if not crawler.is_integer(old_price):
                old_price = 0
            else:
                old_price = int(old_price)
            if not crawler.is_integer(now_price):
                now_price = 0
            else:
                now_price = int(now_price)
            if not crawler.is_integer(discount):
                if old_price == 0:
                    discount = 100
                else:
                    discount = int(now_price / old_price * 100)
            else:
                discount = int(discount)
            # 游戏打折信息
            discount_info = {"type": game_type, "id": prime_id, "app_id": app_id, "discount": discount, "old_price": old_price, "now_price": now_price}
            discount_game_list.append(discount_info)
        # 下一页
        pagination_html = search_result_selector.find(".search_pagination .search_pagination_right").html()
        if pagination_html is None:
            break
        page_count_find = re.findall("<a [\s|\S]*?>([\d]*)</a>", pagination_html.encode("UTF-8"))
        if len(page_count_find) > 0:
            total_page_count = max(map(int, page_count_find))
            if page_count < total_page_count:
                page_count += 1
            else:
                break
        else:
            raise crawler.CrawlerException("分页信息没有找到\n%s" % discount_game_pagination_response.data)
    return discount_game_list


# 获取游戏商店首页
def get_game_store_index(game_id):
    game_index_url = "https://store.steampowered.com/app/%s" % game_id
    game_index_response = net.http_request(game_index_url, method="GET", cookies_list=COOKIE_INFO)
    if game_index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(game_index_response.status))
    result = {
        "dlc_list": [],  # 游戏下的DLC列表
        "reviewed": False,  # 是否评测过
        "owned": False,  # 是否已拥有
    }
    # 所有DLC
    dlc_list_selection = pq(game_index_response.data).find(".game_area_dlc_section a.game_area_dlc_row")
    if dlc_list_selection.length > 0:
        for index in range(0, dlc_list_selection.length):
            result["dlc_list"].append(dlc_list_selection.eq(index).attr("data-ds-appid"))
    # 是否已评测
    result["reviewed"] = pq(game_index_response.data).find("#review_create").length == 0
    # 是否已拥有
    result["owned"] = pq(game_index_response.data).find(".already_in_library").length == 1
    return result


# 获取全部已经没有剩余卡牌掉落且还没有收集完毕的徽章详细地址
def get_self_account_badges(account_id):
    # 徽章第一页
    badges_index_url = "http://steamcommunity.com/profiles/%s/badges/" % account_id
    badges_index_response = net.http_request(badges_index_url, method="GET", cookies_list=COOKIE_INFO)
    if badges_index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(badges_index_response.status))
    badges_detail_url_list = []
    # 徽章div
    badges_selector = pq(badges_index_response.data).find(".maincontent .badges_sheet .badge_row")
    for index in range(0, badges_selector.length):
        badge_html = badges_selector.eq(index).html().encode("UTF-8")
        # 已经掉落全部卡牌的徽章
        if badge_html.find("无剩余卡牌掉落") >= 0:
            # 徽章详细信息页面地址
            badge_detail_url = tool.find_sub_string(badge_html, '<a class="badge_row_overlay" href="', '"/>')
            if not badge_detail_url:
                raise crawler.CrawlerException("徽章信息截取徽章详细界面地址失败\n%s" % badge_html)
            badges_detail_url_list.append(badge_detail_url)
    # ['http://steamcommunity.com/profiles/76561198172925593/gamecards/459820/', 'http://steamcommunity.com/profiles/76561198172925593/gamecards/357200/', 'http://steamcommunity.com/profiles/76561198172925593/gamecards/502740/', 'http://steamcommunity.com/profiles/76561198172925593/gamecards/359600/', 'http://steamcommunity.com/profiles/76561198172925593/gamecards/354380/', 'http://steamcommunity.com/profiles/76561198172925593/gamecards/359670/', 'http://steamcommunity.com/profiles/76561198172925593/gamecards/525300/', 'http://steamcommunity.com/profiles/76561198172925593/gamecards/337980/', 'http://steamcommunity.com/profiles/76561198172925593/gamecards/591420/']
    return badges_detail_url_list


# 获取指定徽章仍然缺少的集换式卡牌名字和对应缺少的数量
# badge_detail_url -> http://steamcommunity.com/profiles/76561198172925593/gamecards/459820/
def get_self_account_badge_card(badge_detail_url):
    badge_detail_response = net.http_request(badge_detail_url, method="GET", cookies_list=COOKIE_INFO)
    if badge_detail_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(badge_detail_response.status))
    wanted_card_list = {}
    page_selector = pq(badge_detail_response.data)
    # 徽章等级
    badge_selector = page_selector.find(".maincontent .badge_current .badge_info")
    # 有等级
    if badge_selector.find(".badge_info_description").length == 1:
        badge_level_html = badge_selector.find(".badge_info_description div").eq(1).text()
        if not badge_level_html:
            raise crawler.CrawlerException("页面截取徽章等级信息失败\n%s" % badge_detail_response.data)
        badge_level_html = badge_level_html.encode("UTF-8")
        badge_level_find = re.findall("(\d*) 级,", badge_level_html)
        if len(badge_level_find) != 1:
            raise crawler.CrawlerException("徽章等级信息徽章等级失败\n%s" % badge_level_html)
        if not crawler.is_integer(badge_level_find[0]):
            raise crawler.CrawlerException("徽章等级类型不正确\n%s" % badge_level_html)
        badge_level = int(badge_level_find[0])
    else:
        badge_level = 0
    wanted_count = 5 - badge_level
    # 集换式卡牌div
    cards_selector = page_selector.find(".maincontent .badge_detail_tasks .badge_card_set_card")
    for card_index in range(0, cards_selector.length):
        card_selector = cards_selector.eq(card_index)
        owned_count_selector = card_selector.find(".badge_card_set_text .badge_card_set_text_qty")
        card_name = card_selector.find(".badge_card_set_text").eq(0).remove(".badge_card_set_text_qty").text()
        if owned_count_selector.length == 1:
            owned_count = owned_count_selector.text().replace("(", "").replace(")", "")
        else:
            owned_count = 0
        if int(owned_count) < wanted_count:
            wanted_card_list[card_name] = wanted_count - int(owned_count)
    # {'Mio': 2}
    return wanted_card_list


# 获取某个游戏的集换式卡牌市场售价
def get_market_game_trade_card_price(game_id):
    market_search_url = "http://steamcommunity.com/market/search/render/"
    market_search_url += "?query=&count=20&appid=753&category_753_Game[0]=tag_app_%s&category_753_cardborder[0]=tag_cardborder_0" % game_id
    market_search_response = net.http_request(market_search_url, method="GET", cookies_list=COOKIE_INFO, json_decode=True)
    if market_search_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(market_search_response.status))
    market_item_list = {}
    if not crawler.check_sub_key(("success", "results_html"), market_search_response.json_data):
        raise crawler.CrawlerException("返回信息'success'或'results_html'字段不存在\n%s" % market_search_response.json_data)
    if market_search_response.json_data["success"] is not True:
        raise crawler.CrawlerException("返回信息'success'字段取值不正确\n%s" % market_search_response.json_data)
    card_selector = pq(market_search_response.json_data["results_html"]).find(".market_listing_row_link")
    for index in range(0, card_selector.length):
        card_name = card_selector.eq(index).find(".market_listing_item_name").text()
        card_min_price = card_selector.eq(index).find("span.normal_price span.normal_price").text().encode("UTF-8").replace("¥ ", "")
        market_item_list[card_name] = card_min_price
    # {'Pamu': '1.77', 'Fumi (Trading Card)': '2.14', 'Mio (Trading Card)': '1.33', 'Bonnibel (Trading Card)': '1.49', 'Groupshot': '1.87', 'Q-Piddy': '1.35', 'Elle (Trading Card)': '1.19', 'Quill': '1.50', 'Iro (Trading Card)': '1.42', 'Bearverly (Trading Card)': '1.27', 'Cassie (Trading Card)': '1.35'}
    return market_item_list


# 获取指定账号所有库存
def get_account_inventory(account_id):
    # 强制使用英文，避免多语言
    # 库存大批信息 item class id => item count
    item_list = {}
    # 每次请求获取的物品数量
    each_page_inventory_count = 1000
    page_count = 1
    last_assert_id = "0"
    while True:
        output.print_msg("开始解析%s ~ %s的库存" % (each_page_inventory_count * (page_count - 1) + 1, each_page_inventory_count * page_count))
        api_url = "https://steamcommunity.com/inventory/%s/753/6" % account_id
        query_data = {
            "l": "english",
            "count": each_page_inventory_count,
        }
        if last_assert_id > 0:
            query_data["start_assetid"] = last_assert_id
        api_response = net.http_request(api_url, method="GET", fields=query_data, json_decode=True)
        if api_response.status == 403:
            raise crawler.CrawlerException("账号隐私设置中未公开库存详情")
        if api_response.status != net.HTTP_RETURN_CODE_SUCCEED:
            raise crawler.CrawlerException(crawler.request_failre(api_response.status))
        # 物品数量
        item_count_list = {}
        if not crawler.check_sub_key(("assets",), api_response.json_data):
            raise crawler.CrawlerException("返回信息'assets'字段不存在\n%s" % api_response.json_data)
        for asset in api_response.json_data["assets"]:
            if not crawler.check_sub_key(("classid", "amount"), asset):
                raise crawler.CrawlerException("物品信息'classid'或'amount'字段不存在\n%s" % asset)
            class_id = int(asset["classid"])
            if class_id in item_count_list:
                item_count_list[class_id] += int(asset["amount"])
            else:
                item_count_list[class_id] = int(asset["amount"])
        # 物品信息
        if not crawler.check_sub_key(("descriptions",), api_response.json_data):
            raise crawler.CrawlerException("返回信息'descriptions'字段不存在\n%s" % api_response.json_data)
        for item_info in api_response.json_data["descriptions"]:
            # 物品类
            if not crawler.check_sub_key(("classid",), item_info):
                raise crawler.CrawlerException("物品信息'classid'字段不存在\n%s" % item_info)
            class_id = int(item_info["classid"])
            if class_id not in item_count_list:
                continue
            item_list[class_id] = {}
            # 物品数量
            item_list[class_id]["count"] = item_count_list[class_id]
            # 物品名字
            if not crawler.check_sub_key(("name",), item_info):
                raise crawler.CrawlerException("物品信息'name'字段不存在\n%s" % item_info)
            item_list[class_id]["name"] = item_info["name"].encode("UTF-8")
            # 物品所在游戏app id
            if not crawler.check_sub_key(("market_fee_app",), item_info):
                raise crawler.CrawlerException("物品信息'market_fee_app'字段不存在\n%s" % item_info)
            if not crawler.is_integer(item_info["market_fee_app"]):
                raise crawler.CrawlerException("物品信息'market_fee_app'字段类型不正确\n%s" % item_info)
            item_list[class_id]["game_id"] = str(item_info["market_fee_app"])
            # 物品类型
            for tag in item_info["tags"]:
                if not crawler.check_sub_key(("category", "localized_tag_name"), tag):
                    raise crawler.CrawlerException("物品标签信息'category'或'localized_tag_name'字段不存在\n%s" % tag)
                # Gems / Trading Card / Trading Card / Profile Background / Emoticon
                if tag["category"] == "item_class":
                    item_list[class_id]["type"] = str(tag["localized_tag_name"])
                    break
        # 下一页起始asset id
        if crawler.check_sub_key(("more_items", "last_assetid"), api_response.json_data):
            if api_response.json_data["more_items"] == 1 and api_response.json_data["last_assetid"] != last_assert_id:
                last_assert_id = str(api_response.json_data["last_assetid"])
                page_count += 1
            else:
                break
        else:
            break
    return item_list


# 获取指定账号的所有徽章等级
def get_account_completed_badges(account_id):
    # 强制使用英文，避免多语言
    cookies_list = {
        "Steam_Language": "english",
        "steamCountry": "US",
    }
    # 徽章等级信息 game id => badge level
    badge_level_list = {}
    page_count = 1
    while True:
        output.print_msg("开始解析第%s页徽章" % page_count)
        badges_pagination_url = "http://steamcommunity.com/profiles/%s/badges/" % account_id
        badges_pagination_response = net.http_request(badges_pagination_url, method="GET", cookies_list=cookies_list)
        badge_list_selector = pq(badges_pagination_response.data).find("div.badge_row")
        if badge_list_selector.length == 0:
            # 如果是隐私账号，会302到主页的，这里只判断页面文字就不判断状态了
            if pq(badges_pagination_response.data).find("div.profile_private_info").length == 1:
                raise crawler.CrawlerException("账号隐私设置中未公开游戏详情")
        for badge_index in range(0, badge_list_selector.length):
            badge_selector = badge_list_selector.eq(badge_index)
            # 获取game id
            detail_badge_url = badge_selector.find('a.badge_row_overlay').attr("href")
            if detail_badge_url is None:
                raise crawler.CrawlerException("页面截取徽章详情地址失败\n%s" % badge_selector.html())
            # 非游戏徽章
            if detail_badge_url.find("/badges/") >= 0:
                continue
            elif detail_badge_url.find("/gamecards/") == -1:
                raise crawler.CrawlerException("页面截取的徽章详情地址 %s 格式不正确" % detail_badge_url)
            game_id = detail_badge_url.split("/")[-2]
            if not crawler.is_integer(game_id):
                raise crawler.CrawlerException("徽章详情地址 %s 截取游戏id失败" % detail_badge_url)
            # 获取徽章等级
            badge_info_text = badge_selector.find('div.badge_content div.badge_info_description div').eq(1).html()
            if badge_info_text is None:
                raise crawler.CrawlerException("页面截取徽章详情失败\n%s" % badge_selector.html())
            badge_level_find = re.findall("Level (\d*),", badge_info_text)
            if len(badge_level_find) != 1:
                raise crawler.CrawlerException("徽章详情截取徽章等级失败\n%s" % badge_info_text)
            badge_level_list[game_id] = int(badge_level_find[0])
        # 判断是不是还有下一页
        next_page_selector = pq(badges_pagination_response.data).find("div.profile_paging div.pageLinks a.pagelink:last")
        if next_page_selector.length == 0:
            break
        if page_count >= int(next_page_selector.attr("href").split("?p=")[-1]):
            break
        page_count += 1


# 获取指定账号的全部游戏id列表
def get_account_owned_app_list(user_id, is_played=False):
    game_index_url = "http://steamcommunity.com/profiles/%s/games/?tab=all" % user_id
    game_index_response = net.http_request(game_index_url, method="GET")
    if game_index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(game_index_response.status))
    # 如果是隐私账号，会302到主页的，这里只判断页面文字就不判断状态了
    if pq(game_index_response.data).find("div.profile_private_info").length == 1:
        raise crawler.CrawlerException("账号隐私设置中未公开游戏详情")
    owned_all_game_data = tool.find_sub_string(game_index_response.data, "var rgGames = ", "\n")
    if not owned_all_game_data:
        raise crawler.CrawlerException("页面截取游戏列表失败\n%s" % game_index_response.data)
    owned_all_game_data = tool.json_decode(owned_all_game_data.strip().rstrip(";"))
    if owned_all_game_data is None:
        raise crawler.CrawlerException("游戏列表加载失败\n%s" % owned_all_game_data)
    app_id_list = []
    for game_data in owned_all_game_data:
        if "appid" not in game_data:
            raise crawler.CrawlerException("游戏信息'appid'字段不存在\n%s" % game_data)
        # 只需要玩过的游戏
        if is_played and "hours_forever" not in game_data:
            continue
        app_id_list.append(str(game_data["appid"]))
    return app_id_list
