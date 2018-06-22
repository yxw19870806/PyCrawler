# -*- coding:UTF-8  -*-
"""
欅坂46公式Blog图片爬虫
http://www.keyakizaka46.com/mob/news/diarShw.php?cd=member
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

IMAGE_COUNT_PER_PAGE = 20


# 获取指定页数的全部日志
def get_one_page_blog(account_id, page_count):
    # http://www.keyakizaka46.com/mob/news/diarKiji.php?cd=member&ct=01&page=0&rw=20
    blog_pagination_url = "http://www.keyakizaka46.com/mob/news/diarKiji.php"
    query_data = {
        "cd": "member",
        "ct": "%02d" % int(account_id),
        "page": page_count - 1,
        "rw": IMAGE_COUNT_PER_PAGE,
    }
    blog_pagination_response = net.http_request(blog_pagination_url, method="GET", fields=query_data)
    result = {
        "blog_info_list": [],  # 全部日志信息
    }
    if blog_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(blog_pagination_response.status))
    if len(tool.find_sub_string(blog_pagination_response.data, '<div class="box-profile">', "</div>").strip()) < 10:
        raise crawler.CrawlerException("账号不存在")
    # 日志正文部分
    blog_article_html = tool.find_sub_string(blog_pagination_response.data, '<div class="box-main">', '<div class="box-sideMember">')
    if not blog_article_html:
        raise crawler.CrawlerException("页面正文截取失败\n%s" % blog_pagination_response.data)
    blog_list = re.findall("<article>([\s|\S]*?)</article>", blog_article_html)
    for blog_info in blog_list:
        result_blog_info = {
            "blog_id" : None,  # 日志id
            "image_url_list": [],  # 全部图片地址
        }
        # 获取日志id
        blog_id = tool.find_sub_string(blog_info, "/diary/detail/", "?")
        if not crawler.is_integer(blog_id):
            raise crawler.CrawlerException("日志页面截取日志id失败\n%s" % blog_info)
        result_blog_info["blog_id"] = str(blog_id)
        # 获取全部图片地址
        image_url_list = re.findall('<img[\S|\s]*?src="([^"]+)"', blog_info)
        result_blog_info["image_url_list"] = map(str, image_url_list)
        result["blog_info_list"].append(result_blog_info)
    return result


# 检测图片地址是否包含域名，如果没有则补上
def get_image_url(image_url):
    # 如果图片地址没有域名，表示直接使用当前域名下的资源，需要拼接成完整的地址
    if image_url[:7] != "http://" and image_url[:8] != "https://":
        if image_url[0] == "/":
            image_url = "http://www.keyakizaka46.com%s" % image_url
        else:
            image_url = "http://www.keyakizaka46.com/%s" % image_url
    return image_url


class Diary(crawler.Crawler):
    def __init__(self):
        sys_config = {
            crawler.SYS_DOWNLOAD_IMAGE: True,
        }
        crawler.Crawler.__init__(self, sys_config)

        # 解析存档文件
        # account_id  image_count  last_diary_time
        self.account_list = crawler.read_save_data(self.save_data_path, 0, ["", "0", "0"])

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
        if len(self.account_info) >= 4 and self.account_info[3]:
            self.account_name = self.account_info[3]
        else:
            self.account_name = self.account_info[0]
        log.step(self.account_name + " 开始")

    # 获取所有可下载日志
    def get_crawl_list(self):
        page_count = 1
        blog_info_list = []
        is_over = False
        # 获取全部还未下载过需要解析的日志
        while not is_over:
            self.main_thread_check()  # 检测主线程运行状态
            log.step(self.account_name + " 开始解析第%s页日志" % page_count)

            # 获取一页博客信息
            try:
                blog_pagination_response = get_one_page_blog(self.account_id, page_count)
            except crawler.CrawlerException, e:
                log.error(self.account_name + " 第%s页日志解析失败，原因：%s" % (page_count, e.message))
                raise

            # 没有获取到任何日志，全部日志已经全部获取完毕了
            if len(blog_pagination_response["blog_info_list"]) == 0:
                break

            log.trace(self.account_name + " 第%s页解析的全部日志：%s" % (page_count, blog_pagination_response["blog_info_list"]))

            # 寻找这一页符合条件的日志
            for blog_info in blog_pagination_response["blog_info_list"]:
                # 检查是否达到存档记录
                if int(blog_info["blog_id"]) > int(self.account_info[2]):
                    blog_info_list.append(blog_info)
                else:
                    is_over = True
                    break

            if not is_over:
                page_count += 1

        return blog_info_list

    # 解析单个日志
    def crawl_blog(self, blog_info):
        image_index = int(self.account_info[1]) + 1
        for image_url in blog_info["image_url_list"]:
            self.main_thread_check()  # 检测主线程运行状态
            # 检测图片地址是否包含域名
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
        self.account_info[2] = blog_info["blog_id"]  # 设置存档记录

    def run(self):
        try:
            # 获取所有可下载日志
            blog_info_list = self.get_crawl_list()
            log.step("需要下载的全部日志解析完毕，共%s个" % len(blog_info_list))

            # 从最早的日志开始下载
            while len(blog_info_list) > 0:
                blog_info =  blog_info_list.pop()
                log.step(self.account_name + " 开始解析日志%s" % blog_info["blog_id"])
                log.trace(self.account_name + " 日志%s解析的全部图片：%s" % (blog_info["blog_id"], blog_info["image_url_list"]))
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
    Diary().main()
