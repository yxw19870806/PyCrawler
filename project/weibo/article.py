# -*- coding:UTF-8  -*-
"""
微博文章图片爬虫
http://www.weibo.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import os
import re
import threading
import time
import traceback
from common import *
from . import weiboCommon

COOKIE_INFO = {"SUB": ""}


# 获取一页的预览文章
# page_id -> 1005052212970554
def get_one_page_article(page_id, page_count):
    # http://weibo.com/p/1005052212970554/wenzhang?pids=Pl_Core_ArticleList__62&Pl_Core_ArticleList__62_page=1&ajaxpagelet=1
    preview_article_pagination_url = "http://weibo.com/p/%s/wenzhang" % page_id
    query_data = {
        "pids": "Pl_Core_ArticleList__62",
        "Pl_Core_ArticleList__62_page": page_count,
        "ajaxpagelet": "1",
    }
    cookies_list = {"SUB": COOKIE_INFO["SUB"]}
    result = {
        "article_info_list": [],  # 全部章信息
        "is_over": False,  # 是不是最后一页文章
    }
    article_pagination_response = net.http_request(preview_article_pagination_url, method="GET", fields=query_data, cookies_list=cookies_list, is_auto_redirect=False)
    if article_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(article_pagination_response.status))
    # 截取文章数据
    article_list_html = tool.find_sub_string(article_pagination_response.data, '"html":"', '"})')
    article_data = article_list_html.replace("\\t", "").replace("\\n", "").replace("\\r", "")
    if not article_data:
        raise crawler.CrawlerException("页面截取文章预信息失败\n%s" % article_pagination_response.data)
    # 文章分组
    preview_article_data_list = re.findall("<li([\S|\s]*?)<\\\\/li>", article_data)
    if len(preview_article_data_list) == 0:
        raise crawler.CrawlerException("文章分组失败\n%s" % article_data)
    for preview_article_data in preview_article_data_list:
        result_article_info = {
            "article_time": None,  # 文章发布时间
            "article_url": None,  # 文章地址
        }
        # 获取文章上传时间
        article_time = tool.find_sub_string(preview_article_data, '<span class=\\"subinfo S_txt2\\">', "<\/span>")
        if not article_time:
            raise crawler.CrawlerException("文章预览截取文章时间失败\n%s" % preview_article_data)
        try:
            result_article_info["article_time"] = int(time.mktime(time.strptime(article_time, "%Y 年 %m 月 %d 日 %H:%M")))
        except ValueError:
            raise crawler.CrawlerException("tweet发布时间文本格式不正确\n%s" % article_time)
        # 获取文章地址
        article_path = tool.find_sub_string(preview_article_data, '<a target=\\"_blank\\" href=\\"', '\\">')
        if not article_time:
            raise crawler.CrawlerException("文章预览截取文章地址失败\n%s" % preview_article_data)
        result_article_info["article_url"] = "http://weibo.com" + str(article_path).replace("\\/", "/").replace("&amp;", "&")
        result["article_info_list"].append(result_article_info)
    # 检测是否还有下一页
    page_count_find = re.findall('<a[\s|\S]*?>([\d]+)<\\\\/a>', article_pagination_response.data)
    result["is_over"] = page_count >= max(map(int, page_count_find))
    return result


# 获取文章页面
def get_article_page(article_url):
    cookies_list = {"SUB": COOKIE_INFO["SUB"]}
    article_response = net.http_request(article_url, method="GET", cookies_list=cookies_list)
    result = {
        "article_id": "",  # 文章id
        "article_title": "",  # 文章标题
        "image_url_list": [],  # 全部图片地址
        "is_pay": False,  # 是否需要购买
        "top_image_url": None,  # 文章顶部图片
    }
    if article_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(article_response.status))
    # 判断是否需要购买
    result["is_pay"] = article_response.data.find("购买继续阅读") >= 0
    article_id = tool.find_sub_string(article_url, "http://weibo.com/ttarticle/p/show?id=", "&mod=zwenzhang")
    if article_id:
        article_type = "t"
        result["article_id"] = "t_" + article_id
    else:
        article_id = tool.find_sub_string(article_url, "http://weibo.com/p/", "?mod=zwenzhang")
        if not article_id:
            raise crawler.CrawlerException("文章地址截取文章类型失败\n%s" % article_url)
        article_type = "p"
        result["article_id"] = "p_" + article_id
    # 获取文章标题
    if article_type == "t":
        result["article_title"] = tool.find_sub_string(article_response.data, '<div class="title" node-type="articleTitle">', "</div>")
    else:  # p
        result["article_title"] = tool.find_sub_string(article_response.data, '<h1 class=\\"title\\">', "<\\/h1>")
    if not result["article_title"]:
        raise crawler.CrawlerException("页面截取文章标题失败\n%s" % article_url)
    # 获取文章顶部图片地址
    article_top_image_html = tool.find_sub_string(article_response.data, '<div class="main_toppic">', '<div class="main_editor')
    if article_top_image_html:
        result["top_image_url"] = tool.find_sub_string(article_top_image_html, 'src="', '" />')
    # 获取文章图片地址列表
    if article_type == "t":
        # 正文到作者信息间的页面
        article_body = tool.find_sub_string(article_response.data, '<div class="WB_editor_iframe', '<div class="artical_add_box')
        if not article_body:
            # 正文到打赏按钮间的页面（未登录不显示关注界面）
            article_body = tool.find_sub_string(article_response.data, '<div class="WB_editor_iframe', '<div node-type="fanService">')
    else:  # p
        article_body = tool.find_sub_string(article_response.data, '{"ns":"pl.content.longFeed.index"', "</script>").replace("\\", "")
    if not article_body:
        raise crawler.CrawlerException("页面截取文章正文失败\n%s" % article_response.data)
    image_url_list = re.findall('<img[^>]* src="([^"]*)"[^>]*>', article_body)
    for image_url in image_url_list:
        # 无效地址
        if image_url.find("/p/e_weibo_com") >= 0 or image_url.find("//e.weibo.com") >= 0:
            continue
        if image_url.find("//") == 0:
            image_url = "http:" + image_url
        result["image_url_list"].append(str(image_url))
    return result


class Article(crawler.Crawler):
    def __init__(self, extra_config=None):
        global COOKIE_INFO

        # 设置APP目录
        tool.PROJECT_APP_PATH = os.path.abspath(os.path.dirname(__file__))

        # 初始化参数
        sys_config = {
            crawler.SYS_DOWNLOAD_IMAGE: True,
            crawler.SYS_GET_COOKIE: {
                ".sina.com.cn": (),
                ".login.sina.com.cn": (),
            },
        }
        crawler.Crawler.__init__(self, sys_config, extra_config)

        # 设置全局变量，供子线程调用
        COOKIE_INFO.update(self.cookie_value)

        # 解析存档文件
        # account_id  last_article_time  (account_name)
        self.account_list = crawler.read_save_data(self.save_data_path, 0, ["", "0"])

        # 检测登录状态
        if not weiboCommon.check_login(COOKIE_INFO):
            # 如果没有获得登录相关的cookie，则模拟登录并更新cookie
            new_cookies_list = weiboCommon.generate_login_cookie(COOKIE_INFO)
            if new_cookies_list:
                COOKIE_INFO.update(new_cookies_list)
            # 再次检测登录状态
            if not weiboCommon.check_login(COOKIE_INFO):
                while True:
                    input_str = output.console_input(crawler.get_time() + " 没有检测到登录信息，可能无法获取到需要关注才能查看的文章，是否继续程序(Y)es？或者退出程序(N)o？:")
                    input_str = input_str.lower()
                    if input_str in ["y", "yes"]:
                        COOKIE_INFO["SUB"] = tool.generate_random_string(50)
                        break
                    elif input_str in ["n", "no"]:
                        tool.process_exit()

    def main(self):
        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for account_id in sorted(self.account_list.keys()):
            # 检查正在运行的线程数
            if threading.activeCount() >= self.thread_count + main_thread_count:
                self.wait_sub_thread()

            # 提前结束
            if not self.is_running():
                break

            # 开始下载
            thread = Download(self.account_list[account_id], self)
            thread.start()

            time.sleep(1)

        # 检查除主线程外的其他所有线程是不是全部结束了
        while threading.activeCount() > main_thread_count:
            self.wait_sub_thread()

        # 未完成的数据保存
        if len(self.account_list) > 0:
            tool.write_file(tool.list_to_string(self.account_list.values()), self.temp_save_data_path)

        # 重新排序保存存档文件
        crawler.rewrite_save_file(self.temp_save_data_path, self.save_data_path)

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), self.total_image_count))


class Download(crawler.DownloadThread):
    def __init__(self, account_info, main_thread):
        crawler.DownloadThread.__init__(self, account_info, main_thread)
        self.account_id = self.account_info[0]
        if len(self.account_info) >= 3 and self.account_info[2]:
            self.account_name = self.account_info[2]
        else:
            self.account_name = self.account_info[0]
        log.step(self.account_name + " 开始")

    # 获取所有可下载视频
    def get_crawl_list(self):
        # 获取账号首页
        try:
            account_index_response = weiboCommon.get_account_index_page(self.account_id)
        except crawler.CrawlerException, e:
            log.error(self.account_name + " 首页解析失败，原因：%s" % e.message)
            raise

        page_count = 1
        article_info_list = []
        is_over = False
        # 获取全部还未下载过需要解析的文章
        while not is_over:
            self.main_thread_check()  # 检测主线程运行状态
            # 获取一页文章预览页面
            try:
                article_pagination_response = get_one_page_article(account_index_response["account_page_id"], page_count)
            except crawler.CrawlerException, e:
                log.error(self.account_name + " 第%s页文章解析失败，原因：%s" % (page_count, e.message))
                raise

            # 寻找这一页符合条件的文章
            for article_info in article_pagination_response["article_info_list"]:
                # 检查是否达到存档记录
                if article_info["article_time"] > int(self.account_info[1]):
                    article_info_list.append(article_info)
                else:
                    is_over = True
                    break

            if not is_over:
                # 获取文章总页数
                if article_pagination_response["is_over"]:
                    is_over = True
                else:
                    page_count += 1

        return article_info_list

    # 解析单篇文章
    def crawl_article(self, article_info):
        # 获取文章页面内容
        try:
            article_response = get_article_page(article_info["article_url"])
        except crawler.CrawlerException, e:
            log.error(self.account_name + " 文章 %s 解析失败，原因：%s" % (article_info["article_url"], e.message))
            raise

        if article_response["is_pay"]:
            log.error(self.account_name + " 文章 %s 存在付费查看的内容" % article_info["article_url"])

        article_id = article_response["article_id"]
        article_title = article_response["article_title"]
        # 过滤标题中不支持的字符
        title = path.filter_text(article_title)
        if title:
            article_path = os.path.join(self.main_thread.image_download_path, self.account_name, "%s %s" % (article_id, title))
        else:
            article_path = os.path.join(self.main_thread.image_download_path, self.account_name, article_id)
        self.temp_path_list.append(article_path)
        # 文章正文图片
        image_index = 1
        for image_url in article_response["image_url_list"]:
            self.main_thread_check()  # 检测主线程运行状态
            if image_url.find("/p/e_weibo_com") >= 0 or image_url.find("//e.weibo.com") >= 0:
                continue
            log.step(self.account_name + " 文章%s《%s》 开始下载第%s张图片 %s" % (article_id, article_title, image_index, image_url))
            file_type = image_url.split(".")[-1]
            file_path = os.path.join(article_path, "%03d.%s" % (image_index, file_type))
            save_file_return = net.save_net_file(image_url, file_path)
            if save_file_return["status"] == 1:
                if weiboCommon.check_image_invalid(file_path):
                    path.delete_dir_or_file(file_path)
                    log.error(self.account_name + " 文章%s《%s》 第%s张图片 %s 资源已被删除，跳过" % (article_id, article_title, image_index, image_url))
                else:
                    log.step(self.account_name + " 文章%s《%s》 第%s张图片下载成功" % (article_id, article_title, image_index))
                    image_index += 1
            else:
                log.error(self.account_name + " 文章%s《%s》 第%s张图片 %s 下载失败，原因：%s" % (article_id, article_title, image_index, image_url, crawler.download_failre(save_file_return["code"])))

        # 文章顶部图片
        if article_response["top_image_url"] is not None:
            self.main_thread_check()  # 检测主线程运行状态
            log.step(self.account_name + " 文章%s《%s》 开始下载顶部图片 %s" % (article_id, article_title, article_response["top_image_url"]))

            file_type = article_response["top_image_url"].split(".")[-1]
            file_path = os.path.join(article_path, "000.%s" % file_type)
            save_file_return = net.save_net_file(article_response["top_image_url"], file_path)
            if save_file_return["status"] == 1:
                if weiboCommon.check_image_invalid(file_path):
                    path.delete_dir_or_file(file_path)
                    log.error(self.account_name + " 文章%s《%s》 顶部图片 %s 资源已被删除，跳过" % (article_id, article_title, article_response["top_image_url"]))
                else:
                    log.step(self.account_name + " 文章%s《%s》 顶部图片下载成功" % (article_id, article_title))
                    image_index += 1
            else:
                log.error(self.account_name + " 文章%s《%s》 顶部图片 %s 下载失败，原因：%s" % (article_id, article_title, article_response["top_image_url"], crawler.download_failre(save_file_return["code"])))

        # 文章内图片全部下载完毕
        self.temp_path_list = []  # 临时目录设置清除
        self.total_image_count += image_index - 1  # 计数累加
        self.account_info[1] = str(article_info["article_time"])  # 设置存档记录

    def run(self):
        try:
            # 获取所有可下载文章
            article_info_list = self.get_crawl_list()
            log.step(self.account_name + " 需要下载的全部文章解析完毕，共%s个" % len(article_info_list))

            # 从最早的文章开始下载
            while len(article_info_list) > 0:
                article_info = article_info_list.pop()
                log.step(self.account_name + " 开始解析文章 %s" % article_info["article_url"])
                self.crawl_article(article_info)
                self.main_thread_check()  # 检测主线程运行状态
        except SystemExit, se:
            if se.code == 0:
                log.step(self.account_name + " 提前退出")
            else:
                log.error(self.account_name + " 异常退出")
            # 如果临时目录变量不为空，表示某个文章正在下载中，需要把下载了部分的内容给清理掉
            self.clean_temp_path()
        except Exception, e:
            log.error(self.account_name + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 保存最后的信息
        with self.thread_lock:
            tool.write_file("\t".join(self.account_info), self.main_thread.temp_save_data_path)
            self.main_thread.total_image_count += self.total_image_count
            self.main_thread.account_list.pop(self.account_id)
        log.step(self.account_name + " 下载完毕，总共获得%s张图片" % self.total_image_count)
        self.notify_main_thread()


if __name__ == "__main__":
    Article().main()
