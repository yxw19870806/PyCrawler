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
    try:
        inventory_item_list = steamCommon.get_account_inventory(account_id)
    except crawler.CrawlerException, e:
        output.print_msg("库存解析失败，原因：%s" % e.message)
        raise
    for item_id, item_info in inventory_item_list.iteritems():
        if item_info["type"] == steamCommon.INVENTORY_ITEM_TYPE_PROFILE_BACKGROUND:
            if CHECK_DUPLICATE_BACKGROUND and item_info["count"] > 1:
                output.print_msg(item_info)
        elif item_info["type"] == steamCommon.INVENTORY_ITEM_TYPE_EMOTICON:
            if CHECK_DUPLICATE_EMOTICON and item_info["count"] > 1:
                output.print_msg(item_info)


if __name__ == "__main__":
    main(steamCommon.get_account_id_from_file())
