# -*- coding:UTF-8  -*-
"""
获取所有的steam打折游戏信息
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import steam


if __name__ == "__main__":
    user_id = 76561198172925593
    min_discount_percent = 90  # 折扣
    min_discount_price = 1  # 打完折后当前价格
    owned_list = steam.get_owned_app_list(user_id)
    discount_list = steam.get_discount_list()

    for discount_info in discount_list:
        discount_info = discount_info.replace("\n", "")
        if len(discount_info) > 0:
            discount_info = discount_info.split("\t")
            if discount_info[0] not in owned_list:
                if int(discount_info[1].replace("-", "").replace("%", "")) >= min_discount_percent or int(discount_info[3] <= min_discount_percent):
                    print "http://store.steampowered.com/app/%s/ ,discount %s%%, old price: %s, discount price: %s" % (discount_info[0], discount_info[1], discount_info[2], discount_info[3])
