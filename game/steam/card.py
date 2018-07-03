# -*- coding:UTF-8  -*-
"""
获取账号多余的交换卡
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import output, crawler
import steamCommon


# 获取账号多余的交换卡
def main(account_id):
    # 获取库存
    try:
        inventory_item_list = steamCommon.get_account_inventory(account_id)
    except crawler.CrawlerException, e:
        output.print_msg("获取库存失败，原因：%s" % e.message)
        raise
    # 获取徽章等级
    try:
        badges_list = steamCommon.get_account_badges(account_id)
    except crawler.CrawlerException, e:
        output.print_msg("获取徽章等级失败，原因：%s" % e.message)
        raise
    for item_id, item_info in inventory_item_list.iteritems():
        if item_info["type"] != steamCommon.INVENTORY_ITEM_TYPE_TRADE_CARD:
            continue
        # 有这个徽章并且徽章等级大等于5
        if item_info["game_id"] in badges_list and badges_list[item_info["game_id"]] == 5:
            output.print_msg(item_info)


if __name__ == "__main__":
    main(steamCommon.get_account_id_from_file())
