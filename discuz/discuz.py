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
def get_bbs_forum_url_list(index_page_url):
    index_page_response = net.http_request(index_page_url)
    if index_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        forum_find = re.findall('<a href="(forum-\w*-\d*.\w*)"[^>]*>([\S]*)</a>', index_page_response.data)
        host = index_page_url[0: index_page_url.rfind("/") + 1]
        forum_url_list = {}
        for forum_path, forum_name in forum_find:
            forum_url_list[host + forum_path] = forum_name
        return forum_url_list
    return None


# 获取论坛板块一页的帖子地址列表
def get_one_forum_page_thread_url_list(forum_page_url):
    forum_page_response = net.http_request(forum_page_url)
    if forum_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        forum_page = tool.find_sub_string(forum_page_response.data, '<div id="threadlist"', '<div id="filter_special_menu"', 1)
        thread_find = re.findall('<a href="(thread-\d*-1-1.\w*)" onclick="atarget\(this\)" class="s xst">([\S|\s]*?)</a>', forum_page)
        host = forum_page_url[0: forum_page_url.rfind("/") + 1]
        thread_url_list = {}
        for forum_path, forum_name in thread_find:
            thread_url_list[host + forum_path] = forum_name
        return thread_url_list
    return None


# 获取帖子作者楼层内容
def get_thread_author_post(thread_page_url):
    thread_page_response = net.http_request(thread_page_url)
    if thread_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        charset = tool.find_sub_string(thread_page_response.headers["Content-Type"], "charset=")
        post_message = tool.find_sub_string(thread_page_response.data, '<td class="t_f" id="postmessage_', '<div id="comment_')
        post_message = post_message[post_message.find('">') + 2: post_message.rfind("</td>")]
        return post_message.decode(charset)
    return None
