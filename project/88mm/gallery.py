# -*- coding:UTF-8  -*-
"""
88mm图库图片爬虫
http://www.88mmw.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
from pyquery import PyQuery as pq
import os
import re
import string
import threading
import time
import traceback
import urllib

SUB_PATH_LIST = {
    "Rosi": "1",
    "Sibao": "2",
    "Tpimage": "3",
    "RiBen": "4",
    "Dgxz": "5",
    "Pansi": "6",
    "Sityle": "7",
    "JiePai": '8',
    "GaoQing": "9",
}


# 获取指定一页的图集
def get_album_page(sub_path, page_count):
    album_pagination_url = "http://www.88mmw.com/%s/list_%s_%s.html" % (sub_path, SUB_PATH_LIST[sub_path], page_count)
    album_pagination_response = net.http_request(album_pagination_url, method="GET")
    result = {
        "album_info_list": [],  # 全部图集信息
        "is_over": False,  # 是不是最后一页图集
    }
    if album_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(album_pagination_response.status))
    # 页面编码
    album_pagination_html = album_pagination_response.data.decode("GBK")
    # 获取图集信息，存在两种页面样式
    album_list_selector = pq(album_pagination_html).find("div.xxx li a")
    if album_list_selector.length == 0:
        album_list_selector = pq(album_pagination_html).find("div.yyy li a")
    if album_list_selector.length == 0:
        raise crawler.CrawlerException("页面截取图集列表失败\n%s" % album_pagination_html.encode("UTF-8"))
    for album_index in range(0, album_list_selector.length):
        result_album_info = {
            "album_title": "",  # 图集id
            "page_id": None,  # 图集页面id
        }
        album_selector = album_list_selector.eq(album_index)
        # 获取图集id
        album_url = album_selector.attr("href")
        if not album_url:
            raise crawler.CrawlerException("图集列表截取图集地址失败\n%s" % album_selector.html().encode("UTF-8"))
        album_id = album_url.split("/")[-2]
        if not crawler.is_integer(album_id):
            raise crawler.CrawlerException("图集地址截取图集id失败\n%s" % str(album_url))
        result_album_info["page_id"] = album_id
        # 获取图集标题
        album_title = album_selector.attr("title").encode("UTF-8")
        if len(re.findall("_共\d*张", album_title)) == 1:
            result_album_info["album_title"] = album_title[:album_title.rfind("_共")]
        else:
            result_album_info["album_title"] = album_title
        result["album_info_list"].append(result_album_info)
    # 判断是不是最后一页
    max_page_info = pq(album_pagination_html).find("div.page a").eq(-1).text()
    if not max_page_info:
        raise crawler.CrawlerException("总页数信息截取失败\n%s" % album_pagination_html.encode("UTF-8"))
    max_page_count = tool.find_sub_string(max_page_info.encode("UTF-8"), "共", "页")
    if not crawler.is_integer(max_page_count):
        raise crawler.CrawlerException("总页数截取失败\n%s" % max_page_info.encode("UTF-8"))
    result["is_over"] = page_count >= int(max_page_count)
    return result


# 获取图集全部图片
def get_album_photo(sub_path, page_id):
    page_count = 1
    result = {
        "image_url_list": [],  # 全部图片地址
    }
    while True:
        if page_count == 1:
            photo_pagination_url = "http://www.88mmw.com/%s/%s" % (sub_path, page_id)
        else:
            photo_pagination_url = "http://www.88mmw.com/%s/%s/index_%s.html" % (sub_path, page_id, page_count)
        photo_pagination_response = net.http_request(photo_pagination_url, method="GET")
        if photo_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
            raise crawler.CrawlerException("第%s页 " % page_count + crawler.request_failre(photo_pagination_response.status))
        # 页面编码
        photo_pagination_html = photo_pagination_response.data.decode("GBK")
        # 获取图片地址
        image_list_selector = pq(photo_pagination_html).find("div.zzz li img")
        if image_list_selector.length == 0:
            raise crawler.CrawlerException("第%s页 页面匹配图片地址失败\n%s" % (page_count, photo_pagination_html.encode("UTF-8")))
        for image_index in range(0, image_list_selector.length):
            result["image_url_list"].append("http://www.88mmw.com" + str(image_list_selector.eq(image_index).attr("src")).replace("-lp", ""))
        # 判断是不是最后一页
        is_over = False
        max_page_selector = pq(photo_pagination_html).find("div.page").eq(0).find("span strong").text()
        if not max_page_selector:
            is_over = True
        elif crawler.is_integer(max_page_selector):
            is_over = page_count >= int(max_page_selector)
        if is_over:
            break
        else:
            page_count += 1
    return result


# 对图片地址中的特殊字符（如，中文）进行转义
def get_image_url(image_url):
    return urllib.quote(image_url, safe=string.printable.replace(" ", ""))


class Gallery(crawler.Crawler):
    def __init__(self):
        sys_config = {
            crawler.SYS_DOWNLOAD_IMAGE: True,
            crawler.SYS_NOT_CHECK_SAVE_DATA: True,
        }
        crawler.Crawler.__init__(self, sys_config)

        # 解析存档文件
        # sub_path  last_page_id
        self.account_list = crawler.read_save_data(self.save_data_path, 0, ["", "0"])
        for sub_path in SUB_PATH_LIST:
            if sub_path not in self.account_list:
                self.account_list[sub_path] = [sub_path, "0"]

    def main(self):
        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for sub_path in sorted(self.account_list.keys()):
            # 检查正在运行的线程数
            while threading.activeCount() >= self.thread_count + main_thread_count:
                self.wait_sub_thread()

            # 提前结束
            if not self.is_running():
                break

            # 开始下载
            thread = Download(self.account_list[sub_path], self)
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
        self.sub_path = self.account_info[0]
        log.step(self.sub_path + " 开始")

    # 获取所有可下载图集
    def get_crawl_list(self):
        page_count = 1
        album_info_list = []
        is_over = False
        # 获取全部还未下载过需要解析的图集
        while not is_over:
            self.main_thread_check()  # 检测主线程运行状态
            log.step(self.sub_path + " 开始解析第%s页图集" % page_count)

            # 获取一页图集
            try:
                album_response = get_album_page(self.sub_path, page_count)
            except crawler.CrawlerException, e:
                log.error(self.sub_path + " 第%s页图集解析失败，原因：%s" % (page_count, e.message))
                raise

            log.trace(self.sub_path + " 第%s页解析的全部图集：%s" % (page_count, album_response["album_info_list"]))

            # 寻找这一页符合条件的图集
            for album_info in album_response["album_info_list"]:
                # 检查是否达到存档记录
                if int(album_info["page_id"]) > int(self.account_info[1]):
                    album_info_list.append(album_info)
                else:
                    is_over = True
                    break

            if not is_over:
                if album_response["is_over"]:
                    is_over = True
                else:
                    page_count += 1

        return album_info_list

    # 解析单个图集
    def crawl_album(self, album_info):
        # 获取图集全部图片
        try:
            photo_pagination_response = get_album_photo(self.sub_path, album_info["page_id"])
        except crawler.CrawlerException, e:
            log.error(self.sub_path + " %s号图集解析失败，原因：%s" % (album_info["page_id"], e.message))
            raise

        log.trace(self.sub_path + " %s号图集《%s》解析的全部图片：%s" % (album_info["page_id"], album_info["album_title"], photo_pagination_response["image_url_list"]))

        image_index = 1
        # 过滤标题中不支持的字符
        album_title = path.filter_text(album_info["album_title"])
        if album_title:
            album_path = os.path.join(self.main_thread.image_download_path, "%04d %s" % (int(album_info["page_id"]), album_title))
        else:
            album_path = os.path.join(self.main_thread.image_download_path, "%04d" % int(album_info["page_id"]))
        # 设置临时目录
        self.temp_path_list.append(album_path)
        for image_url in photo_pagination_response["image_url_list"]:
            self.main_thread_check()  # 检测主线程运行状态
            # 图片地址转义
            image_url = get_image_url(image_url)
            log.step(self.sub_path + " %s号图集《%s》 开始下载第%s张图片 %s" % (album_info["page_id"], album_info["album_title"], image_index, image_url))

            file_type = image_url.split(".")[-1]
            file_path = os.path.join(album_path, "%03d.%s" % (image_index, file_type))
            save_file_return = net.save_net_file(image_url, file_path)
            if save_file_return["status"] == 1:
                log.step(self.sub_path + " %s号图集《%s》 第%s张图片下载成功" % (album_info["page_id"], album_info["album_title"], image_index))
                image_index += 1
            else:
                log.error(self.sub_path + " %s号图集《%s》 第%s张图片 %s 下载失败，原因：%s" % (album_info["page_id"], album_info["album_title"], image_index, image_url, crawler.download_failre(save_file_return["code"])))

        # 图集内图片全部下载完毕
        self.temp_path_list = []  # 临时目录设置清除
        self.total_image_count += image_index - 1  # 计数累加
        self.account_info[1] = album_info["page_id"]  # 设置存档记录

    def run(self):
        try:
            # 获取所有可下载图集
            album_info_list = self.get_crawl_list()
            log.step(self.sub_path + " 需要下载的全部图集解析完毕，共%s个" % len(album_info_list))

            # 从最早的图集开始下载
            while len(album_info_list) > 0:
                album_info = album_info_list.pop()
                log.step(self.sub_path + " 开始解析%s号图集" % album_info["page_id"])
                self.crawl_album(album_info)
                self.main_thread_check()  # 检测主线程运行状态
        except SystemExit, se:
            if se.code == 0:
                log.step(self.sub_path + " 提前退出")
            else:
                log.error(self.sub_path + " 异常退出")
            # 如果临时目录变量不为空，表示某个图集正在下载中，需要把下载了部分的内容给清理掉
            self.clean_temp_path()
        except Exception, e:
            log.error(self.sub_path + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 保存最后的信息
        with self.thread_lock:
            tool.write_file("\t".join(self.account_info), self.main_thread.temp_save_data_path)
            self.main_thread.total_image_count += self.total_image_count
            self.main_thread.account_list.pop(self.sub_path)
        log.step(self.sub_path + " 下载完毕，总共获得%s张图片" % self.total_image_count)
        self.notify_main_thread()


if __name__ == "__main__":
    Gallery().main()
