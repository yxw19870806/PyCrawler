# -*- coding:UTF-8  -*-
"""
新浪博客图片爬虫
http://blog.sina.com.cn/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import os
import re
import threading
import time
import traceback
from pyquery import PyQuery as pq
from common import *


# 获取指定页数的全部日志
def get_one_page_blog(account_id, page_count):
    # http://moexia.lofter.com/?page=1
    blog_pagination_url = "http://blog.sina.com.cn/s/articlelist_%s_0_%s.html" % (account_id, page_count)
    blog_pagination_response = net.http_request(blog_pagination_url, method="GET")
    result = {
        "blog_info_list": [],  # 全部日志地址
        "is_over": False,  # 是不是最后一页
    }
    if blog_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(blog_pagination_response.status))
    if page_count == 1 and blog_pagination_response.data.find("抱歉，您要访问的页面不存在或被删除！") >= 0:
        raise crawler.CrawlerException("账号不存在")
    article_list_selector = pq(blog_pagination_response.data.decode("UTF-8")).find(".articleList .articleCell")
    if article_list_selector.length == 0:
        raise crawler.CrawlerException("页面截取日志列表失败\n%s" % blog_pagination_response.data)
    for article_index in range(article_list_selector.length):
        result_blog_info = {
            "blog_url": None,  # 日志地址
            "blog_time": None,  # 日志时间
            "blog_title": "",  # 日志标题
        }
        article_selector = article_list_selector.eq(article_index)
        # 获取日志地址
        blog_url = article_selector.find("span.atc_title a").attr("href")
        if not blog_url:
            raise crawler.CrawlerException("日志列表解析日志地址失败\n%s" % article_selector.html().encode("UTF-8"))
        result_blog_info["blog_url"] = str(blog_url)
        # 获取日志标题
        blog_title = article_selector.find("span.atc_title a").text().encode("UTF-8")
        if not blog_title:
            raise crawler.CrawlerException("日志列表解析日志标题失败\n%s" % article_selector.html().encode("UTF-8"))
        result_blog_info["blog_title"] = str(blog_title)
        # 获取日志时间
        blog_time = article_selector.find("span.atc_tm").text()
        if not blog_time:
            raise crawler.CrawlerException("日志列表解析日志时间失败\n%s" % article_selector.html().encode("UTF-8"))
        try:
            result_blog_info["blog_time"] = int(time.mktime(time.strptime(blog_time, "%Y-%m-%d %H:%M")))
        except ValueError:
            raise crawler.CrawlerException("日志时间格式不正确\n%s" % blog_time)
        result["blog_info_list"].append(result_blog_info)
    # 获取分页信息
    pagination_html = tool.find_sub_string(blog_pagination_response.data, '<div class="SG_page">', '</div>')
    if not pagination_html:
        result["is_over"] = True
    else:
        max_page_count = tool.find_sub_string(pagination_html, "共", "页")
        if not crawler.is_integer(max_page_count):
            raise crawler.CrawlerException("分页信息截取总页数失败\n%s" % pagination_html)
        result["is_over"] = page_count >= int(max_page_count)
    return result


# 获取日志
def get_blog_page(blog_url):
    blog_response = net.http_request(blog_url, method="GET")
    result = {
        "image_url_list": [],  # 全部图片地址
    }
    if blog_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(blog_response.status))
    # 获取博客正文
    article_html = tool.find_sub_string(blog_response.data, "<!-- 正文开始 -->", "<!-- 正文结束 -->")
    # 获取图片地址
    image_url_list = re.findall('real_src ="([^"]*)"', article_html)
    result["image_url_list"] = map(str, image_url_list)
    # 获取全部图片地址
    return result


# 获取日志id
def get_blog_id(blog_url):
    return tool.find_sub_string(blog_url.split("/")[-1], "blog_", ".html")


# 获取图片原始地址
def get_image_url(image_url):
    if image_url.find("&amp") >= 0:
        temp_list = image_url.split("&amp")[0].split("/")
        temp_list[-2] = "orignal"
        image_url = "/".join(temp_list)
    return image_url


class Blog(crawler.Crawler):
    def __init__(self):
        # 设置APP目录
        tool.PROJECT_APP_PATH = os.path.abspath(os.path.dirname(__file__))

        # 初始化参数
        sys_config = {
            crawler.SYS_DOWNLOAD_IMAGE: True,
        }
        crawler.Crawler.__init__(self, sys_config)

        # 解析存档文件
        # account_name  last_blog_id
        self.account_list = crawler.read_save_data(self.save_data_path, 0, ["", "0"])

    def main(self):
        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for account_name in sorted(self.account_list.keys()):
            # 检查正在运行的线程数
            if threading.activeCount() >= self.thread_count + main_thread_count:
                self.wait_sub_thread()

            # 提前结束
            if not self.is_running():
                break

            # 开始下载
            thread = Download(self.account_list[account_name], self)
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
        if len(self.account_info) > 2 and self.account_info[2]:
            self.account_name = self.account_info[2]
        else:
            self.account_name = self.account_id
        log.step(self.account_name + " 开始")

    # 获取所有可下载日志
    def get_crawl_list(self):
        page_count = 1
        unique_list = []
        blog_info_list = []
        is_over = False
        # 获取全部还未下载过需要解析的日志
        while not is_over:
            self.main_thread_check()  # 检测主线程运行状态
            log.step(self.account_name + " 开始解析第%s页日志" % page_count)

            try:
                blog_pagination_response = get_one_page_blog(self.account_id, page_count)
            except crawler.CrawlerException, e:
                log.error(self.account_name + " 第%s页日志解析失败，原因：%s" % (page_count, e.message))
                raise

            log.trace(self.account_name + " 第%s页解析的全部日志：%s" % (page_count, blog_pagination_response["blog_info_list"]))

            # 寻找这一页符合条件的日志
            for blog_info in blog_pagination_response["blog_info_list"]:
                # 检查是否达到存档记录
                if blog_info["blog_time"] > int(self.account_info[1]):
                    # 新增日志导致的重复判断
                    if blog_info["blog_url"] in unique_list:
                        continue
                    else:
                        blog_info_list.append(blog_info)
                        unique_list.append(blog_info["blog_url"])
                else:
                    is_over = True
                    break

            if not is_over:
                if blog_pagination_response["is_over"]:
                    is_over = blog_pagination_response["is_over"]
                else:
                    page_count += 1

        return blog_info_list

    # 解析单个日志
    def crawl_blog(self, blog_info):
        # 获取日志
        try:
            blog_response = get_blog_page(blog_info["blog_url"])
        except crawler.CrawlerException, e:
            log.error(self.account_name + " 日志《%s》 %s 解析失败，原因：%s" % (blog_info["blog_title"], blog_info["blog_url"], e.message))
            raise

        log.trace(self.account_name + " 日志《%s》 %s 解析的全部图片：%s" % (blog_info["blog_title"], blog_info["blog_url"], blog_response["image_url_list"]))

        image_index = 1
        # 过滤标题中不支持的字符
        blog_title = path.filter_text(blog_info["blog_title"])
        blog_id = get_blog_id(blog_info["blog_url"])
        # 过滤标题中不支持的字符
        if blog_title:
            image_path = os.path.join(self.main_thread.image_download_path, self.account_name, "%s %s" % (blog_id, blog_title))
        else:
            image_path = os.path.join(self.main_thread.image_download_path, self.account_name, blog_id)
        self.temp_path_list.append(image_path)
        for image_url in blog_response["image_url_list"]:
            self.main_thread_check()  # 检测主线程运行状态
            # 获取图片原始地址
            image_url = get_image_url(image_url)
            log.step(self.account_name + " 日志《%s》 开始下载第%s张图片 %s" % (blog_info["blog_title"], image_index, image_url))

            if image_url.rfind(".") > image_url.rfind("/"):
                file_type = image_url.split(".")[-1]
            else:
                file_type = "jpg"
            file_path = os.path.join(image_path, "%04d.%s" % (image_index, file_type))
            save_file_return = net.save_net_file(image_url, file_path)
            if save_file_return["status"] == 1:
                log.step(self.account_name + " 日志《%s》 第%s张图片下载成功" % (blog_info["blog_title"], image_index))
                image_index += 1
            else:
                log.error(self.account_name + " 日志《%s》 第%s张图片 %s 下载失败，原因：%s" % (blog_info["blog_title"], image_index, image_url, crawler.download_failre(save_file_return["code"])))

        # 日志内图片全部下载完毕
        self.temp_path_list = []  # 临时目录设置清除
        self.total_image_count += image_index - 1  # 计数累加
        self.account_info[1] = str(blog_info["blog_time"])  # 设置存档记录

    def run(self):
        try:
            # 获取所有可下载日志
            blog_info_list = self.get_crawl_list()
            log.step("需要下载的全部日志解析完毕，共%s个" % len(blog_info_list))

            # 从最早的日志开始下载
            while len(blog_info_list) > 0:
                blog_info = blog_info_list.pop()
                log.step(self.account_name + " 开始解析日志《%s》 %s" % (blog_info["blog_title"], blog_info["blog_url"]))
                self.crawl_blog(blog_info)
                self.main_thread_check()  # 检测主线程运行状态
        except SystemExit, se:
            if se.code == 0:
                log.step(self.account_name + " 提前退出")
            else:
                log.error(self.account_name + " 异常退出")
            # 如果临时目录变量不为空，表示某个日志正在下载中，需要把下载了部分的内容给清理掉
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
    Blog().main()
