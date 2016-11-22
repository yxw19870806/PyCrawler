# -*- coding:UTF-8  -*-
"""
微博文章图片爬虫
http://www.weibo.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, robot, tool
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


# 访问微博域名网页，自动判断是否需要跳转
def auto_redirect_visit(url):
    page_return_code, page_response = tool.http_request(url)[:2]
    if page_return_code == 1:
        # 有重定向
        redirect_url_find = re.findall('location.replace\(["|\']([^"|^\']*)["|\']\)', page_response)
        if len(redirect_url_find) == 1:
            return auto_redirect_visit(redirect_url_find[0])
        # 没有cookies无法访问的处理
        if page_response.find("用户名或密码错误") != -1:
            log.error("登陆状态异常，请在浏览器中重新登陆微博账号")
            tool.process_exit()
        # 返回页面
        if page_response:
            return str(page_response)
    return False


# 获取一页的文章预览信息
# page_id -> 1005052212970554
def get_one_page_preview_article_data(page_id, page_count):
    # http://weibo.com/p/1005052212970554/wenzhang?Pl_Core_ArticleList__63_page=1
    preview_article_page_url = "http://weibo.com/p/%s/wenzhang?Pl_Core_ArticleList__63_page=%s" % (page_id, page_count)
    preview_article_page = auto_redirect_visit(preview_article_page_url)
    if preview_article_page:
        return preview_article_page
    else:
        return None


# 将文章预览页面内容按照文章分组
def get_preview_article_data_list(preview_article_page):
    preview_article_page = tool.find_sub_string(preview_article_page, '"domid":"Pl_Core_ArticleList__63"', "</script>")
    preview_article_page = tool.find_sub_string(preview_article_page, '"html":"', '"})')
    preview_article_page = preview_article_page.replace("\\t", "").replace("\\n", "").replace("\\r", "")
    return re.findall("<li([\S|\s]*?)<\\\\/li>", preview_article_page)


# 获取账号对应的page_id
def get_account_page_id(account_id):
    for i in range(0, 50):
        index_url = "http://weibo.com/u/%s?is_all=1" % account_id
        index_page = auto_redirect_visit(index_url)
        if index_page:
            account_page_id = tool.find_sub_string(index_page, "$CONFIG['page_id']='", "'")
            if account_page_id:
                return account_page_id
        time.sleep(5)
    return None


# 根据文章预览获取文章的发布时间
def get_article_time(preview_article_data):
    article_time = tool.find_sub_string(preview_article_data, '<span class=\\"subinfo S_txt2\\">', "<\/span>")
    if article_time:
        return int(time.mktime(time.strptime(article_time, "%Y 年 %m 月 %d 日 %H:%M")))
    else:
        return None


# 根据文章预览页面解析出文章地址
def get_article_url(preview_article_data):
    page_route = tool.find_sub_string(preview_article_data, '<a target=\\"_blank\\" href=\\"', '\\">')
    page_route = page_route.replace("\\/", "/").replace("&amp;", "&")
    if page_route:
        return "http://weibo.com" + page_route
    else:
        return None


# 根据文章预览页面，获取文章总页数
def get_max_page_count(preview_article_data):
    page_count_find = re.findall('Pl_Core_ArticleList__63\\\\">([\d]+)<\\\\/a>', preview_article_data)
    return max(map(int, page_count_find))


# 根据文章地址，获取文章id
# 原创文章：t_XXXXXXXXXXXXXXXXXXXXXX
# 转载文章: p_XXXXXXXXXXXXXXXXXXXXXX
# article_url -> http://weibo.com/ttarticle/p/show?id=2309404035316578158020&mod=zwenzhang
#                http://weibo.com/p/1001594033894323210501?mod=zwenzhang
def get_article_id(article_url):
    article_id = tool.find_sub_string(article_url, "http://weibo.com/ttarticle/p/show?id=", "&mod=zwenzhang")
    if article_id:
        return "t_%s" % article_id
    else:
        article_id = tool.find_sub_string(article_url, "http://weibo.com/p/", "?mod=zwenzhang")
        if article_id:
            return "p_%s" % article_id
    return None


# 根据文章页面，获取文章标题
def get_article_title(article_page, article_type):
    if article_type == "t":
        return tool.find_sub_string(article_page, '<div class="title" node-type="articleTitle">', "</div>")
    elif article_type == "p":
        return tool.find_sub_string(article_page, '<h1 class=\\"title\\">', "<\\/h1>")
    else:
        return None


# 根据文章页面，获取文章顶部的图片地址
def get_article_top_picture_url(article_page):
    article_top_picture = tool.find_sub_string(article_page, '<div class="main_toppic">', '<div class="main_editor')
    if article_top_picture:
        return tool.find_sub_string(article_top_picture, 'src="', '" />')


# 根据文章页面，获取正文中的所有图片地址列表
def get_article_image_url_list(article_page, article_type):
    if article_type == "t":
        article_body = tool.find_sub_string(article_page, '<div class="WB_editor_iframe', '<div class="artical_add_box"')
    elif article_type == "p":
        article_body = tool.find_sub_string(article_page, '{"ns":"pl.content.longFeed.index"', "</script>")
        article_body = article_body.replace("\\", "")
    else:
        return None
    if article_body:
        return re.findall('<img[^>]* src="([^"]*)"[^>]*>', article_body)
    return None


class Article(robot.Robot):
    def __init__(self):
        global GET_IMAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_SET_COOKIE: ("weibo.com", ".sina.com.cn"),
        }
        extra_config = {
            "save_data_path": os.path.join(os.path.abspath(""), "info\\article.data",)
        }
        robot.Robot.__init__(self, sys_config, extra_config)

        # 设置全局变量，供子线程调用
        GET_IMAGE_COUNT = self.get_image_count
        IMAGE_TEMP_PATH = self.image_temp_path
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        IS_SORT = self.is_sort
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

    def main(self):
        global ACCOUNTS

        # 解析存档文件
        # account_id  last_article_time  (account_name)
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "0"])
        ACCOUNTS = account_list.keys()

        # 先访问下页面，产生cookies
        auto_redirect_visit("http://www.weibo.com/")
        time.sleep(2)

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

            # 获取账号对应的page_id
            account_page_id = get_account_page_id(account_id)
            if account_page_id is None:
                log.error(account_name + " 微博主页没有获取到page_id")
                tool.process_exit()

            page_count = 1
            this_account_total_image_count = 0
            first_article_time = "0"
            is_over = False
            image_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
            while not is_over:
                # 获取一页文章预览页面
                preview_article_page = get_one_page_preview_article_data(account_page_id, page_count)

                if preview_article_page is None:
                    log.error(account_name + " 第%s页文章获取失败" % page_count)
                    tool.process_exit()

                # 将文章预览页面内容分组
                preview_article_data_list = get_preview_article_data_list(preview_article_page)
                if len(preview_article_data_list) == 0:
                    log.error(account_name + " 第%s页文章解析失败，页面：%s" % (page_count, preview_article_page))
                    tool.process_exit()

                for preview_article_data in preview_article_data_list:
                    # 获取文章的发布时间
                    article_time = get_article_time(preview_article_data)
                    if article_time is None:
                        log.error(account_name + " 预览 %s 中的文章发布时间解析失败" % preview_article_data)
                        continue

                    # 检查是否是上一次的最后视频
                    if article_time <= int(self.account_info[1]):
                        is_over = True
                        break

                    # 将第一个视频的地址做为新的存档记录
                    if first_article_time == "0":
                        first_article_time = str(article_time)

                    # 获取文章地址
                    article_url = get_article_url(preview_article_data)
                    if article_url is None:
                        log.error(account_name + " 预览 %s 中的文章地址解析失败" % preview_article_data)
                        continue

                    # 获取文章id
                    article_id = get_article_id(article_url)
                    if article_id is None:
                        log.error(account_name + " 文章地址 %s 解析文章id失败" % article_url)
                        continue

                    # 获取文章页面内容
                    article_page = auto_redirect_visit(article_url)
                    if not article_page:
                        log.error(account_name + " 文章 %s 获取失败" % article_url)
                        continue

                    # 文章标题
                    title = get_article_title(article_page, article_id[0])
                    # 过滤标题中不支持的字符
                    title = robot.filter_text(title)
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
                    top_picture_url = get_article_top_picture_url(article_page)
                    if top_picture_url:
                        log.step(account_name + " %s 开始下载顶部图片 %s" % (title, top_picture_url))

                        file_type = top_picture_url.split(".")[-1]
                        file_path = os.path.join(article_path, "0000.%s" % file_type)
                        if tool.save_net_file(top_picture_url, file_path):
                            log.step(account_name + " %s 顶部图片下载成功" % title)
                            this_account_total_image_count += 1
                        else:
                            log.error(account_name + " %s 顶部图片 %s 下载失败" % (title, top_picture_url))

                    # 获取文章正文的图片地址列表
                    image_url_list = get_article_image_url_list(article_page, article_id[0])
                    if image_url_list is None:
                        log.error(account_name + " 文章 %s 正文解析失败" % article_url)
                        continue

                    image_count = 1
                    for image_url in list(image_url_list):
                        if image_url.find("/p/e_weibo_com") >= 0 or image_url.find("e.weibo.com") >= 0:
                            continue
                        log.step(account_name + " %s 开始下载第%s张图片 %s" % (title, image_count, image_url))

                        file_type = image_url.split(".")[-1]
                        file_path = os.path.join(article_path, "%s.%s" % (image_count, file_type))
                        if tool.save_net_file(image_url, file_path):
                            log.step(account_name + " %s 第%s张图片下载成功" % (title, image_count))
                            image_count += 1
                        else:
                            log.error(account_name + " %s 第%s张图片 %s 下载失败" % (title, image_count, image_url))

                    if image_count > 1:
                        this_account_total_image_count += image_count - 1

                if not is_over:
                    # 获取文章总页数
                    if page_count >= get_max_page_count(preview_article_page):
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
