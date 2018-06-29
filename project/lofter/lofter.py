# -*- coding:UTF-8  -*-
"""
lofter图片爬虫
http://www.lofter.com/
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


# 获取指定页数的全部日志
def get_one_page_blog(account_name, page_count):
    # http://moexia.lofter.com/?page=1
    blog_pagination_url = "http://%s.lofter.com" % account_name
    query_data = {"page": page_count}
    blog_pagination_response = net.http_request(blog_pagination_url, method="GET", fields=query_data)
    result = {
        "blog_url_list": [],  # 全部日志地址
    }
    if blog_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 获取全部日志地址
        blog_url_list = re.findall('"(http://' + account_name + '.lofter.com/post/[^"]*)"', blog_pagination_response.data)
        # 去重排序
        result["blog_url_list"] = sorted(list(set(blog_url_list)), reverse=True)
    elif page_count == 1 and blog_pagination_response.status == 404:
        raise crawler.CrawlerException("账号不存在")
    else:
        raise crawler.CrawlerException(crawler.request_failre(blog_pagination_response.status))
    return result


# 获取日志
def get_blog_page(blog_url):
    blog_response = net.http_request(blog_url, method="GET")
    result = {
        "image_url_list": [],  # 全部图片地址
    }
    if blog_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(blog_response.status))
    # 获取全部图片地址
    image_url_list = re.findall('bigimgsrc="([^"]*)"', blog_response.data)
    result["image_url_list"] = map(str, image_url_list)
    return result


# 从日志地址中解析出日志id
def get_blog_id(blog_url):
    return blog_url.split("/")[-1].split("_")[-1]


# 去除图片的参数
def get_image_url(image_url):
    if image_url.rfind("?") > image_url.rfind("."):
        return image_url.split("?")[0]
    return image_url


class Lofter(crawler.Crawler):
    def __init__(self):
        # 设置APP目录
        tool.PROJECT_APP_PATH = os.path.abspath(os.path.dirname(__file__))

        # 初始化参数
        sys_config = {
            crawler.SYS_DOWNLOAD_IMAGE: True,
        }
        crawler.Crawler.__init__(self, sys_config)

        # 解析存档文件
        # account_name  image_count  last_blog_id
        self.account_list = crawler.read_save_data(self.save_data_path, 0, ["", "0", ""])

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
        self.account_name = self.account_info[0]
        log.step(self.account_name + " 开始")

    # 获取所有可下载日志
    def get_crawl_list(self):
        page_count = 1
        unique_list = []
        blog_url_list = []
        is_over = False
        # 获取全部还未下载过需要解析的日志
        while not is_over:
            self.main_thread_check()  # 检测主线程运行状态
            log.step(self.account_name + " 开始解析第%s页日志" % page_count)

            try:
                blog_pagination_response = get_one_page_blog(self.account_name, page_count)
            except crawler.CrawlerException, e:
                log.error(self.account_name + " 第%s页日志解析失败，原因：%s" % (page_count, e.message))
                raise

            # 下载完毕了
            if len(blog_pagination_response["blog_url_list"]) == 0:
                break

            log.trace(self.account_name + " 第%s页解析的全部日志：%s" % (page_count, blog_pagination_response["blog_url_list"]))

            # 寻找这一页符合条件的日志
            for blog_url in blog_pagination_response["blog_url_list"]:
                blog_id = get_blog_id(blog_url)

                # 检查是否达到存档记录
                if blog_id > self.account_info[2]:
                    # 新增日志导致的重复判断
                    if blog_id in unique_list:
                        continue
                    else:
                        blog_url_list.append(blog_url)
                        unique_list.append(blog_id)
                else:
                    is_over = True
                    break

            if not is_over:
                page_count += 1

        return blog_url_list

    # 解析单个日志
    def crawl_blog(self, blog_url):
        # 获取日志
        try:
            blog_response = get_blog_page(blog_url)
        except crawler.CrawlerException, e:
            log.error(self.account_name + " 日志 %s 解析失败，原因：%s" % (blog_url, e.message))
            raise

        # 获取图片下载地址列表
        if len(blog_response["image_url_list"]) == 0:
            log.error(self.account_name + " 日志 %s 中没有找到图片" % blog_url)
            return

        log.trace(self.account_name + " 日志 %s 解析的全部图片：%s" % (blog_url, blog_response["image_url_list"]))

        image_index = int(self.account_info[1]) + 1
        for image_url in blog_response["image_url_list"]:
            self.main_thread_check()  # 检测主线程运行状态
            # 去除图片地址的参数
            image_url = get_image_url(image_url)
            log.step(self.account_name + " 开始下载第%s张图片 %s" % (image_index, image_url))

            file_type = image_url.split(".")[-1]
            file_path = os.path.join(self.main_thread.image_download_path, self.account_name, "%04d.%s" % (image_index, file_type))
            save_file_return = net.save_net_file(image_url, file_path)
            if save_file_return["status"] == 1:
                self.temp_path_list.append(file_path)
                log.step(self.account_name + " 第%s张图片下载成功" % image_index)
                image_index += 1
            else:
                log.error(self.account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_index, image_url, crawler.download_failre(save_file_return["code"])))

        # 日志内图片全部下载完毕
        self.temp_path_list = []  # 临时目录设置清除
        self.total_image_count += (image_index - 1) - int(self.account_info[1])  # 计数累加
        self.account_info[1] = str(image_index - 1)  # 设置存档记录
        self.account_info[2] = get_blog_id(blog_url)  # 设置存档记录

    def run(self):
        try:
            # 获取所有可下载日志
            blog_url_list = self.get_crawl_list()
            log.step("需要下载的全部日志解析完毕，共%s个" % len(blog_url_list))

            # 从最早的日志开始下载
            while len(blog_url_list) > 0:
                blog_url = blog_url_list.pop()
                log.step(self.account_name + " 开始解析日志 %s" % blog_url)
                self.crawl_blog(blog_url)
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
            self.main_thread.account_list.pop(self.account_name)
        log.step(self.account_name + " 下载完毕，总共获得%s张图片" % self.total_image_count)
        self.notify_main_thread()


if __name__ == "__main__":
    Lofter().main()
