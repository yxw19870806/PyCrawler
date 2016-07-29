# -*- coding:UTF-8  -*-
from common import tool
import re

for sid in range(1, 200):
    index_url = "http://www.snh48.com/member_detail.php?sid=%s" % sid
    return_code, index_page = tool.http_request(index_url)[:2]
    if return_code == 1:
        name = tool.find_sub_string(index_page, "</i>首页 > 成员 >", "</div>").strip()
        if name:
            weibo_uid_find = re.findall('<a href="http://weibo.com/[u]?[/]?([\w]*)["|/|\?]', index_page)
            if len(weibo_uid_find) >= 1:
                print name, weibo_uid_find[0]
            else:
                print "error weibo uid " + index_page
    else:
        print "error member id " + str(sid)