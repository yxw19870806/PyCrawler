# -*- coding:UTF-8  -*-
"""
欅坂46公式ブログ成员id获取
http://www.keyakizaka46.com/mob/news/diarShw.php?cd=member
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import tool
import re


def get_member_list():
    index_url = "http://www.keyakizaka46.com/mob/news/diarShw.php?cd=member"
    index_return_code, index_page = tool.http_request(index_url)[:2]
    if index_return_code:
        member_list_data = tool.find_sub_string(index_page, '<ul class="thumb">', "</ul>")
        if member_list_data:
            member_list_find = re.findall("<li ([\S|\s]*?)</li>", member_list_data)
            for member_info in member_list_find:
                ct = tool.find_sub_string(member_info, "&ct=", '">')
                name = tool.find_sub_string(member_info, '<p class="name">', '</p>').strip().replace(" ", "")
                tool.print_msg("%s\t\t\t%s" % (ct, name), False)
            if len(member_list_find) > 0:
                tool.print_msg("复制以上内容到save.data中，删除不需要的行，即可开始运行", False)
    return None

if __name__ == "__main__":
    get_member_list()
