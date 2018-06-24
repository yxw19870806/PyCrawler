# -*- coding:UTF-8  -*-
"""
获取指定账号的全部未收集完成徽章对应的集换卡价格
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import urllib
from common import output, crawler
import steamCommon

MIN_CARD_PRICE = 0  # 最低卡牌价格
MAX_CARD_PRICE = 99  # 最高卡牌价格


# 获取当前account正在收集的徽章进度
def main(account_id):
    # 获取登录状态
    try:
        cookies_list = steamCommon.get_cookie_from_browser()
    except crawler.CrawlerException, e:
        output.print_msg("登录状态检测失败，原因：%s" % e.message)
        raise
    # 获取全部没有收到恒宇卡牌掉落且还可以升级的徽章
    try:
        badges_detail_url_list = steamCommon.get_self_account_badges(account_id, cookies_list)
    except crawler.CrawlerException, e:
        output.print_msg("个人徽章首页解析失败，原因：%s" % e.message)
        raise
    for badges_detail_url in badges_detail_url_list:
        # 查询徽章剩余的卡牌以及数量
        try:
            wanted_card_list = steamCommon.get_self_account_badge_card(badges_detail_url, cookies_list)
        except crawler.CrawlerException, e:
            output.print_msg("徽章%s解析失败，原因：%s" % (badges_detail_url, e.message))
            continue
        if len(wanted_card_list) > 0:
            game_id = badges_detail_url.split("/")[-2]
            output.print_msg("game id: %s" % game_id, False)
            # 获取全部卡牌的市场售价
            try:
                market_card_list = steamCommon.get_market_game_trade_card_price(game_id, cookies_list)
            except crawler.CrawlerException, e:
                output.print_msg("游戏id%s的市场解析失败，原因：%s" % (game_id, e.message))
                continue
            card_real_name_dict = {}
            for card_read_name in market_card_list:
                card_name = card_read_name.replace(" (Trading Card)", "")
                card_real_name_dict[card_name] = card_read_name
            for card_name in wanted_card_list:
                if card_name in card_real_name_dict:
                    card_read_name = card_real_name_dict[card_name]
                else:
                    card_read_name = card_name
                if card_read_name in market_card_list:
                    if MIN_CARD_PRICE < float(market_card_list[card_read_name]) <= MAX_CARD_PRICE:
                        market_link = "http://steamcommunity.com/market/listings/753/%s-%s" % (game_id, urllib.quote(card_read_name.encode("UTF-8")))
                        output.print_msg("card: %s, wanted %s, min price: %s, link: %s" % (card_name, wanted_card_list[card_name], market_card_list[card_read_name], market_link), False)
                else:
                    output.print_msg("card: %s, wanted %s, not found price in market" % (card_name, wanted_card_list[card_read_name]), False)


if __name__ == "__main__":
    main(steamCommon.get_account_id_from_file())
