# -*- coding:UTF-8  -*-
"""
获取指定账号的全部重复库存内个人资料背景和表情
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import output, crawler
import steamCommon
DUPLICATE_BACKGROUND = True
DUPLICATE_EMOTICON = True


# 获取当前account正在收集的徽章进度
def main(account_id):
    # 获取登录状态
    try:
        cookies_list = steamCommon.get_cookie_from_browser()
    except crawler.CrawlerException, e:
        output.print_msg("登录状态检测失败，原因：%s" % e.message)
        raise
    last_assert_id = "0"
    inventory_item_list = {}
    while True:
        try:
            inventory_pagination_response = steamCommon.get_one_page_inventory(account_id, cookies_list, last_assert_id)
        except crawler.CrawlerException, e:
            print e.message
            output.print_msg("assert id: %s后一页的库存解析失败，原因：%s" % (last_assert_id, e.message))
            raise
        inventory_item_list.update(inventory_pagination_response["item_list"])
        if inventory_pagination_response["last_assert_id"] is None:
            break
        else:
            last_assert_id = inventory_pagination_response["last_assert_id"]
    for item_id, item_info in inventory_item_list.iteritems():
        if item_info["type"] == "ProfileBackground":
            if DUPLICATE_BACKGROUND and item_info["count"] > 1:
                output.print_msg(item_info)
        elif item_info["type"] == "Emoticon":
            if DUPLICATE_EMOTICON and item_info["count"] > 1:
                output.print_msg(item_info)


if __name__ == "__main__":
    main(steamCommon.get_account_id_from_file())
