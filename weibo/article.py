# -*- coding:UTF-8  -*-
"""
微博文章图片爬虫
http://www.weibo.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, net, robot, tool
import os
import re
import threading
import time
import traceback

ACCOUNTS = []
TOTAL_IMAGE_COUNT = 0
IMAGE_TEMP_PATH = ""
IMAGE_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_SORT = True
COOKIE_INFO = {"SUB": ""}


# 检测登录状态
def check_login():
    if not COOKIE_INFO["SUB"]:
        return False
    header_list = {"cookie": "SUB=" + COOKIE_INFO["SUB"]}
    weibo_index_page_url = "http://weibo.com/"
    weibo_index_page_response = net.http_request(weibo_index_page_url, header_list=header_list)
    if weibo_index_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        return weibo_index_page_response.data.find("$CONFIG['islogin']='1';") >= 0
    return False


# 获取账号首页
def get_home_page(account_id):
    home_page_url = "http://weibo.com/u/%s?is_all=1" % account_id
    header_list = {"cookie": "SUB=" + COOKIE_INFO["SUB"]}
    extra_info = {
        "account_page_id": None,  # 页面解析出的账号page id
    }
    home_page_response = net.http_request(home_page_url, header_list=header_list)
    if home_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        account_page_id = tool.find_sub_string(home_page_response.data, "$CONFIG['page_id']='", "'")
        if account_page_id and robot.is_integer(account_page_id):
            extra_info["account_page_id"] = account_page_id
    home_page_response.extra_info = extra_info
    return home_page_response


# 获取一页的预览文章
# page_id -> 1005052212970554
def get_one_page_preview_article(page_id, page_count):
    # http://weibo.com/p/1005052212970554/wenzhang?pids=Pl_Core_ArticleList__62&Pl_Core_ArticleList__62_page=1&ajaxpagelet=1
    index_page_url = "http://weibo.com/p/%s/wenzhang?pids=Pl_Core_ArticleList__62&Pl_Core_ArticleList__62_page=%s&ajaxpagelet=1" % (page_id, page_count)
    header_list = {"cookie": "SUB=" + COOKIE_INFO["SUB"]}
    extra_info = {
        "article_info_list": [],  # 页面解析出的文章信息列表
        "is_over": False,  # 是不是最后一页文章
    }
    index_page_response = net.http_request(index_page_url, header_list=header_list)
    if index_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        article_data = tool.find_sub_string(index_page_response.data, '"html":"', '"})')
        article_data = article_data.replace("\\t", "").replace("\\n", "").replace("\\r", "")
        preview_article_data_list = re.findall("<li([\S|\s]*?)<\\\\/li>", article_data)
        if len(preview_article_data_list) > 0:
            for preview_article_data in preview_article_data_list:
                extra_article_info = {
                    "article_time": None,  # 页面解析出的文章发布时间
                    "article_url": None,  # 页面解析出的文章地址
                    "article_html": preview_article_data,  # 原始数据
                }
                # 获取文章上传时间
                article_time_string = tool.find_sub_string(preview_article_data, '<span class=\\"subinfo S_txt2\\">', "<\/span>")
                if article_time_string:
                    extra_article_info["article_time"] = int(time.mktime(time.strptime(article_time_string, "%Y 年 %m 月 %d 日 %H:%M")))
                # 获取文章地址
                article_path = tool.find_sub_string(preview_article_data, '<a target=\\"_blank\\" href=\\"', '\\">')
                if article_path:
                    extra_article_info["article_url"] = "http://weibo.com" + str(article_path).replace("\\/", "/").replace("&amp;", "&")
                extra_info["article_info_list"].append(extra_article_info)
            # 检测是否还有下一页
            page_count_find = re.findall('<a[\s|\S]*?>([\d]+)<\\\\/a>', index_page_response.data)
            extra_info["is_over"] = page_count >= max(map(int, page_count_find))
    index_page_response.extra_info = extra_info
    return index_page_response


# 获取文章页面
def get_article_page(article_page_url):
    header_list = {"cookie": "SUB=" + COOKIE_INFO["SUB"]}
    article_page_response = net.http_request(article_page_url, header_list=header_list)
    extra_info = {
        "is_error": False,  # 是不是页面格式不符合
        "is_pay": False,  # 是否需要购买
        "article_id": "",  # 文章地址解析出的文章id
        "article_title": "",  # 页面解析出的文章标题
        "top_image_url": None,  # 页面解析出的文章顶部图片
        "image_url_list": [],  # 页面解析出的文章信息列表
    }
    if article_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        extra_info["is_pay"] = article_page_response.data.find("购买继续阅读") >= 0
        article_type = None
        article_id = tool.find_sub_string(article_page_url, "http://weibo.com/ttarticle/p/show?id=", "&mod=zwenzhang")
        if article_id:
            article_type = "t"
            extra_info["article_id"] = "t_" + article_id
        else:
            article_id = tool.find_sub_string(article_page_url, "http://weibo.com/p/", "?mod=zwenzhang")
            if article_id:
                article_type = "p"
                extra_info["article_id"] = "p_" + article_id
        if article_type is not None:
            # 获取文章标题
            if article_type == "t":
                extra_info["article_title"] = tool.find_sub_string(article_page_response.data, '<div class="title" node-type="articleTitle">', "</div>")
            elif article_type == "p":
                extra_info["article_title"] = tool.find_sub_string(article_page_response.data, '<h1 class=\\"title\\">', "<\\/h1>")
            # 获取文章顶部图片地址
            article_top_image_html = tool.find_sub_string(article_page_response.data, '<div class="main_toppic">', '<div class="main_editor')
            if article_top_image_html:
                extra_info["top_image_url"] = tool.find_sub_string(article_top_image_html, 'src="', '" />')
            # 获取文章图片地址列表
            article_body = None
            if article_type == "t":
                # 正文到作者信息间的页面
                article_body = tool.find_sub_string(article_page_response.data, '<div class="WB_editor_iframe', '<div class="artical_add_box')
                if not article_body:
                    # 正文到打赏按钮间的页面（未登录不显示关注界面）
                    article_body = tool.find_sub_string(article_page_response.data, '<div class="WB_editor_iframe', '<div node-type="fanService">')
            elif article_type == "p":
                article_body = tool.find_sub_string(article_page_response.data, '{"ns":"pl.content.longFeed.index"', "</script>").replace("\\", "")
            if article_body is not None:
                image_url_list = re.findall('<img[^>]* src="([^"]*)"[^>]*>', article_body)
                extra_info["image_url_list"] = map(str, image_url_list)
            else:
                extra_info["is_error"] = True
        else:
            extra_info["is_error"] = True
    article_page_response.extra_info = extra_info
    return article_page_response


class Article(robot.Robot):
    def __init__(self, extra_config=None):
        global GET_IMAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT
        global COOKIE_INFO

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_GET_COOKIE: {".sina.com.cn": ("SUB",)},
        }
        robot.Robot.__init__(self, sys_config, extra_config, use_urllib3=True)

        # 设置全局变量，供子线程调用
        GET_IMAGE_COUNT = self.get_image_count
        IMAGE_TEMP_PATH = self.image_temp_path
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        IS_SORT = self.is_sort
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)
        COOKIE_INFO["SUB"] = self.cookie_value["SUB"]

    def main(self):
        global ACCOUNTS

        if not check_login():
            while True:
                input_str = tool.console_input(tool.get_time() + " 没有检测到您的登录信息，可能无法获取到需要关注才能查看的文章，是否继续程序(Y)es？或者退出程序(N)o？:")
                input_str = input_str.lower()
                if input_str in ["y", "yes"]:
                    COOKIE_INFO["SUB"] = tool.generate_random_string(50)
                    break
                elif input_str in ["n", "no"]:
                    tool.process_exit()

        # 解析存档文件
        # account_id  last_article_time  (account_name)
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "0"])
        ACCOUNTS = account_list.keys()

        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for account_id in sorted(account_list.keys()):
            # 检查正在运行的线程数
            while threading.activeCount() >= self.thread_count + main_thread_count:
                if robot.is_process_end() == 0:
                    time.sleep(10)
                else:
                    break

            # 提前结束
            if robot.is_process_end() > 0:
                break

            # 开始下载
            thread = Download(account_list[account_id], self.thread_lock)
            thread.start()

            time.sleep(1)

        # 检查除主线程外的其他所有线程是不是全部结束了
        while threading.activeCount() > main_thread_count:
            time.sleep(10)

        # 未完成的数据保存
        if len(ACCOUNTS) > 0:
            new_save_data_file = open(NEW_SAVE_DATA_PATH, "a")
            for account_id in ACCOUNTS:
                new_save_data_file.write("\t".join(account_list[account_id]) + "\n")
            new_save_data_file.close()

        # 重新排序保存存档文件
        robot.rewrite_save_file(NEW_SAVE_DATA_PATH, self.save_data_path)

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), TOTAL_IMAGE_COUNT))


class Download(threading.Thread):
    def __init__(self, account_info, thread_lock):
        threading.Thread.__init__(self)
        self.account_info = account_info
        self.thread_lock = thread_lock

    def run(self):
        global TOTAL_IMAGE_COUNT

        account_id = self.account_info[0]
        if len(self.account_info) >= 3 and self.account_info[2]:
            account_name = self.account_info[2]
        else:
            account_name = self.account_info[0]

        try:
            log.step(account_name + " 开始")

            # 获取账号首页
            home_page_response = get_home_page(account_id)
            if home_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                log.error(account_name + " 首页访问失败，原因：%s" % robot.get_http_request_failed_reason(home_page_response.status))
                tool.process_exit()

            if home_page_response.extra_info["account_page_id"] is None:
                log.error(account_name + " 账号page id解析失败")
                tool.process_exit()

            page_count = 1
            this_account_total_image_count = 0
            first_article_time = "0"
            is_over = False
            image_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
            while not is_over:
                # 获取一页文章预览页面
                index_page_response = get_one_page_preview_article(home_page_response.extra_info["account_page_id"], page_count)

                if index_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                    log.error(account_name + " 第%s页文章访问失败，原因：%s" % (page_count, robot.get_http_request_failed_reason(index_page_response.status)))
                    tool.process_exit()

                if len(index_page_response.extra_info["article_info_list"]) == 0:
                    log.error(account_name + " 第%s页文章解析失败" % page_count)
                    tool.process_exit()

                for article_info in index_page_response.extra_info["article_info_list"]:
                    # 文章的发布时间
                    if article_info["article_time"] is None:
                        log.error(account_name + " 文章预览 %s 中的发布时间解析失败" % article_info["article_html"])
                        tool.process_exit()

                    # 文章的地址
                    if article_info["article_url"] is None:
                        log.error(account_name + " 文章预览 %s 中的地址解析失败" % article_info["article_html"])
                        tool.process_exit()

                    # 检查是否是上一次的最后视频
                    if article_info["article_time"] <= int(self.account_info[1]):
                        is_over = True
                        break

                    # 将第一个视频的地址做为新的存档记录
                    if first_article_time == "0":
                        first_article_time = str(article_info["article_time"])

                    log.step(account_name + " 开始解析文章%s" % article_info["article_url"])

                    # 获取文章页面内容
                    article_page_response = get_article_page(article_info["article_url"])
                    if article_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                        log.error(account_name + " 文章 %s 访问失败" % article_info["article_url"])
                        tool.process_exit()

                    if article_page_response.extra_info["is_error"]:
                        log.error(account_name + " 文章 %s 解析失败" % article_info["article_url"])
                        tool.process_exit()

                    if article_page_response.extra_info["is_pay"]:
                        log.error(account_name + " 文章 %s 存在付费查看的内容" % article_info["article_url"])

                    article_id = article_page_response.extra_info["article_id"]
                    article_title = article_page_response.extra_info["article_title"]
                    # 过滤标题中不支持的字符
                    title = robot.filter_text(article_title)
                    if title:
                        article_path = os.path.join(image_path, "%s %s" % (article_id, title))
                    else:
                        article_path = os.path.join(image_path, article_id)
                    if not tool.make_dir(article_path, 0):
                        # 目录出错，把title去掉后再试一次，如果还不行退出
                        log.error(account_name + " 创建文章目录 %s 失败，尝试不使用title" % article_path)
                        article_path = os.path.join(image_path, article_id)
                        if not tool.make_dir(article_path, 0):
                            log.error(account_name + " 创建文章目录 %s 失败" % article_path)
                            tool.process_exit()

                    # 文章顶部图片
                    if article_page_response.extra_info["top_image_url"] is not None:
                        log.step(account_name + " 文章%s《%s》 开始下载顶部图片 %s" % (article_id, article_title, article_page_response.extra_info["top_image_url"]))

                        file_type = article_page_response.extra_info["top_image_url"].split(".")[-1]
                        file_path = os.path.join(article_path, "0000.%s" % file_type)
                        save_file_return = net.save_net_file(article_page_response.extra_info["top_image_url"], file_path)
                        if save_file_return["status"] == 1:
                            log.step(account_name + " 文章%s《%s》 顶部图片下载成功" % (article_id, article_title))
                            this_account_total_image_count += 1
                        else:
                            log.error(account_name + " 文章%s《%s》 顶部图片 %s 下载失败" % (article_id, article_title, article_page_response.extra_info["top_image_url"]))

                    # 文章正文图片
                    image_count = 1
                    for image_url in article_page_response.extra_info["image_url_list"]:
                        if image_url.find("/p/e_weibo_com") >= 0 or image_url.find("e.weibo.com") >= 0:
                            continue
                        log.step(account_name + " 文章%s《%s》 开始下载第%s张图片 %s" % (article_id, article_title, image_count, image_url))

                        file_type = image_url.split(".")[-1]
                        file_path = os.path.join(article_path, "%s.%s" % (image_count, file_type))
                        save_file_return = net.save_net_file(image_url, file_path)
                        if save_file_return["status"] == 1:
                            log.step(account_name + " 文章%s《%s》 第%s张图片下载成功" % (article_id, article_title, image_count))
                            image_count += 1
                        else:
                            log.error(account_name + " 文章%s《%s》 第%s张图片 %s 下载失败" % (article_id, article_title, image_count, image_url))

                    if image_count > 1:
                        this_account_total_image_count += image_count - 1

                if not is_over:
                    # 获取文章总页数
                    if index_page_response.extra_info["is_over"]:
                        is_over = True
                    else:
                        page_count += 1

            log.step(account_name + " 下载完毕，总共获得%s张图片" % this_account_total_image_count)

            # 新的存档记录
            if first_article_time != "0":
                self.account_info[1] = first_article_time

            # 保存最后的信息
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            self.thread_lock.acquire()
            TOTAL_IMAGE_COUNT += this_account_total_image_count
            ACCOUNTS.remove(account_id)
            self.thread_lock.release()

            log.step(account_name + " 完成")
        except SystemExit, se:
            if se.code == 0:
                log.step(account_name + " 提前退出")
            else:
                log.error(account_name + " 异常退出")
        except Exception, e:
            log.error(account_name + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))


if __name__ == "__main__":
    Article().main()
