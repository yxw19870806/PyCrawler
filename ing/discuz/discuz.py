# -*- coding:UTF-8  -*-
"""
discuz论坛解析爬虫
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import net, tool
import re


# 获取论坛所有版块的地址列表
def get_bbs_forum_url_list(index_url):
    index_response = net.http_request(index_url)
    if index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        forum_find = re.findall('<a href="(forum-\w*-\d*.\w*)"[^>]*>([\S]*)</a>', index_response.data)
        host = index_url[0: index_url.rfind("/") + 1]
        forum_url_list = {}
        for forum_path, forum_name in forum_find:
            forum_url_list[host + forum_path] = forum_name
        return forum_url_list
    return None


# 获取论坛板块一页的帖子地址列表
def get_one_forum_page_thread_url_list(forum_url):
    forum_response = net.http_request(forum_url)
    if forum_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        forum_page = tool.find_sub_string(forum_response.data, '<div id="threadlist"', '<div id="filter_special_menu"', 1)
        thread_find = re.findall('<a href="(thread-\d*-1-1.\w*)" onclick="atarget\(this\)" class="s xst">([\S|\s]*?)</a>', forum_page)
        host = forum_url[0: forum_url.rfind("/") + 1]
        thread_url_list = {}
        for forum_path, forum_name in thread_find:
            thread_url_list[host + forum_path] = forum_name
        return thread_url_list
    return None


# 获取帖子作者楼层内容
def get_thread_author_post(thread_url):
    thread_response = net.http_request(thread_url)
    if thread_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        post_message = tool.find_sub_string(thread_response.data, '<td class="t_f" id="postmessage_', '<div id="comment_')
        post_message = post_message[post_message.find('">') + 2: post_message.rfind("</td>")]
        content_type = thread_response.getheader("Content-Type")
        if content_type is None:
            return post_message
        charset = tool.find_sub_string(content_type, "charset=")
        return post_message.decode(charset)

    return None
