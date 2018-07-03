# -*- coding:UTF-8  -*-
"""
获取指定账号的全部重复库存内个人资料背景和表情
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import output, crawler
import steamCommon

CHECK_DUPLICATE_BACKGROUND = True
CHECK_DUPLICATE_EMOTICON = True


# 获取当前account正在收集的徽章进度
def main(account_id):
    # 获取登录状态
    try:
        steamCommon.init_cookie_from_browser()
    except crawler.CrawlerException, e:
        output.print_msg("登录状态检测失败，原因：%s" % e.message)
        raise
    try:
        inventory_item_list = steamCommon.get_inventory(account_id)
    except crawler.CrawlerException, e:
        output.print_msg("库存解析失败，原因：%s" % e.message)
        raise
    for item_id, item_info in inventory_item_list.iteritems():
        if item_info["type"] == "Profile Background":
            if CHECK_DUPLICATE_BACKGROUND and item_info["count"] > 1:
                output.print_msg(item_info)
        elif item_info["type"] == "Emoticon":
            if CHECK_DUPLICATE_EMOTICON and item_info["count"] > 1:
                output.print_msg(item_info)


if __name__ == "__main__":
    main(steamCommon.get_account_id_from_file())
