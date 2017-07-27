# -*- coding:UTF-8  -*-
"""
获取指定账号的全部未收集完成徽章对应的集换卡价格
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import urllib

from common import tool
import steamCommon


# 获取当前account正在收集的徽章进度
def main(account_id):
    login_cookie = steamCommon.get_login_cookie_from_browser()

    badges_detail_url_list = steamCommon.get_self_account_badges(account_id, login_cookie)
    for badges_detail_url in badges_detail_url_list:
        wanted_card_list = steamCommon.get_self_account_badge_card(badges_detail_url, login_cookie)
        if len(wanted_card_list) > 0:
            game_id = badges_detail_url.split("/")[-2]
            tool.print_msg("game id: %s" % game_id, False)
            market_card_list = steamCommon.get_market_game_trade_card_price(game_id, login_cookie)
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
                    market_link = "http://steamcommunity.com/market/listings/753/%s-%s" % (game_id, urllib.quote(card_read_name))
                    tool.print_msg("card: %s, wanted %s, min price: %s, link: %s" % (card_name, wanted_card_list[card_name], market_card_list[card_read_name], market_link), False)
                else:
                    tool.print_msg("card: %s, wanted %s, not found price in market" % (card_name, wanted_card_list[card_read_name]), False)


if __name__ == "__main__":
    main(steamCommon.get_account_id_from_file())