# -*- coding:UTF-8  -*-
"""
微博收藏夹图片爬虫
http://www.weibo.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import os
import re

from pyquery import PyQuery as pq

from common import *
import weiboCommon

COOKIE_INFO = {"SUB": ""}


# 获取一页的收藏微博ge
def get_one_page_favorite(page_count):
    # http://www.weibo.com/fav?page=1
    favorite_pagination_url = "http://www.weibo.com/fav?page=%s" % page_count
    cookies_list = {"SUB": COOKIE_INFO["SUB"]}
    favorite_pagination_response = net.http_request(favorite_pagination_url, cookies_list=cookies_list)
    extra_info = {
        "is_error": False,  # 是不是不符合格式
        "is_over": False,  # 是不是最后一页收藏
        "blog_info_list": [],  # 页面解析出的微博信息列表
    }
    if favorite_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        html_data = tool.find_sub_string(favorite_pagination_response.data, '"ns":"pl.content.favoriteFeed.index"', '"})</script>', 2)
        html_data = tool.find_sub_string(html_data, '"html":"', '"})')
        # 替换全部转义斜杠以及没有用的换行符等
        html_data = html_data.replace("\\\\", chr(1))
        for replace_string in ["\\n", "\\r", "\\t", "\\"]:
            html_data = html_data.replace(replace_string, "")
        html_data = html_data.replace(chr(1), "\\")
        # 解析页面
        children_selector = pq(html_data).find('div.WB_feed').children()
        if children_selector.size() <= 1:
            extra_info["is_error"] = True
        else:
            # 解析日志id和图片地址
            for i in range(0, children_selector.size() - 1):
                feed_selector = children_selector.eq(i)
                # 已被删除的微博
                if not feed_selector.has_class("WB_feed_type"):
                    continue
                extra_blog_info = {
                    "blog_id": None,  # 页面解析出的日志id（mid）
                    "image_url_list": [],  # 页面解析出的微博图片地址列表
                    "html_data": feed_selector.html(),  # 原始页面数据
                }
                # 解析日志id
                blog_id = feed_selector.attr("mid")
                if robot.is_integer(blog_id):
                    extra_blog_info["blog_id"] = str(blog_id)
                    # WB_text       微博文本
                    # WB_media_wrap 微博媒体（图片）
                    # .WB_feed_expand .WB_expand     转发的微博，下面同样包含WB_text、WB_media_wrap这些结构
                    # 包含转发微博
                    if feed_selector.find(".WB_feed_expand .WB_expand").size() == 0:
                        media_selector = feed_selector.find(".WB_media_wrap")
                    else:
                        media_selector = feed_selector.find(".WB_feed_expand .WB_expand .WB_media_wrap")
                    # 如果存在媒体
                    if media_selector.size() == 1:
                        thumb_image_url_list = re.findall('<img src="([^"]*)"/>', media_selector.html())
                        if len(thumb_image_url_list) > 0:
                            image_url_list = []
                            for image_url in thumb_image_url_list:
                                temp_list = image_url.split("/")
                                temp_list[3] = "large"
                                image_url_list.append("http:" + str("/".join(temp_list)))
                            extra_blog_info["image_url_list"] = image_url_list
                else:
                    extra_info["is_error"] = True
                    break
                if len(extra_blog_info["image_url_list"]) > 0:
                    extra_info["blog_info_list"].append(extra_blog_info)
            # 最后一条feed是分页信息
            page_selector = children_selector.eq(children_selector.size() - 1)
            # 是不是最后一页
            page_count_find = re.findall("第([\d]*)页",  page_selector.html())
            if len(page_count_find) > 0:
                page_count_find = map(int, page_count_find)
                extra_info["is_over"] = page_count >= max(page_count_find)
    favorite_pagination_response.extra_info = extra_info
    return favorite_pagination_response


class Favorite(robot.Robot):
    def __init__(self, extra_config=None):
        global COOKIE_INFO

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_NOT_CHECK_SAVE_DATA: True,
            robot.SYS_GET_COOKIE: {
                ".sina.com.cn": (),
                ".login.sina.com.cn": (),
            },
        }
        robot.Robot.__init__(self, sys_config, extra_config)

        # 设置全局变量，供子线程调用
        COOKIE_INFO.update(self.cookie_value)

    def main(self):
        # 检测登录状态
        if not weiboCommon.check_login(COOKIE_INFO):
            # 如果没有获得登录相关的cookie，则模拟登录并更新cookie
            new_cookies_list = weiboCommon.generate_login_cookie(COOKIE_INFO)
            if new_cookies_list:
                COOKIE_INFO.update(new_cookies_list)
            # 再次检测登录状态
            if not weiboCommon.check_login(COOKIE_INFO):
                log.error("没有检测到您的登录信息，无法获取图片或视频，自动退出程序！")
                tool.process_exit()

        page_count = 1
        total_image_count = 0
        is_over = False
        while not is_over:
            log.step("开始解析第%s页收藏" % page_count)

            favorite_pagination_response = get_one_page_favorite(page_count)
            if favorite_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                log.error("第%s页收藏访问失败，原因：%s" % (page_count, robot.get_http_request_failed_reason(favorite_pagination_response.status)))
                tool.process_exit()

            if favorite_pagination_response.extra_info["is_error"]:
                log.error("第%s页收藏解析失败" % page_count)
                tool.process_exit()

            for blog_info in favorite_pagination_response.extra_info["blog_info_list"]:
                log.step("开始解析微博%s" % blog_info["blog_id"])

                image_path = os.path.join(self.image_download_path, blog_info["blog_id"])

                if not tool.make_dir(image_path, 0):
                    log.error("创建图片下载目录 %s 失败" % image_path)
                    tool.process_exit()
                
                image_count = 1
                for image_url in blog_info["image_url_list"]:
                    log.step("开始下载微博%s的第%s张图片 %s" % (blog_info["blog_id"], image_count, image_url))

                    file_type = image_url.split(".")[-1]
                    file_path = os.path.join(image_path, "%s.%s" % (image_count, file_type))
                    save_file_return = net.save_net_file(image_url, file_path)
                    if save_file_return["status"] == 1:
                        if weiboCommon.check_image_invalid(file_path):
                            tool.remove_dir_or_file(file_path)
                            log.error("微博%s的第%s张图片 %s 资源已被删除，跳过" % (blog_info["blog_id"], image_count, image_url))
                        else:
                            log.step("微博%s的第%s张图片下载成功" % (blog_info["blog_id"], image_count))
                            image_count += 1
                            total_image_count += 1
                    else:
                        log.error("微博%s的第%s张图片 %s 下载失败，原因：%s" % (blog_info["blog_id"], image_count, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

            if favorite_pagination_response.extra_info["is_over"]:
                is_over = True
            else:
                page_count += 1

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), total_image_count))


if __name__ == "__main__":
    Favorite().main()
