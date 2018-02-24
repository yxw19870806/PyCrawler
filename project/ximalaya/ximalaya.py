# -*- coding:UTF-8  -*-
"""
喜马拉雅歌曲爬虫
http://www.ximalaya.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
from pyquery import PyQuery as PQ
import os
import threading
import time
import traceback


# 获取指定页数的全部歌曲信息
def get_one_page_audio(account_id, page_count):
    # http://www.ximalaya.com/1014267/index_tracks?page=2
    audit_pagination_url = "http://www.ximalaya.com/%s/index_tracks" % account_id
    query_data = {"page": page_count}
    audit_pagination_response = net.http_request(audit_pagination_url, method="GET", fields=query_data, json_decode=True)
    result = {
        "audio_info_list": [],  # 页面解析出的歌曲信息列表
        "is_over": False,  # 是不是最后一页
    }
    if audit_pagination_response.status == 404:
        raise crawler.CrawlerException("账号不存在")
    elif audit_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(audit_pagination_response.status))
    if not crawler.check_sub_key(("res", "html"), audit_pagination_response.json_data):
        raise crawler.CrawlerException("返回数据'res'或'html'字段不存在\n%s" % audit_pagination_response.json_data)
    if audit_pagination_response.json_data["res"] is not True:
        raise crawler.CrawlerException("返回数据'res'字段取值不正确\n%s" % audit_pagination_response.json_data)
    # 获取歌曲信息
    audio_list_selector = PQ(audit_pagination_response.json_data["html"]).find("ul.body_list li.item")
    for audio_index in range(0, audio_list_selector.size()):
        audio_info = {
            "audio_id": None,  # 页面解析出的歌曲id
            "audio_title": "",  # 页面解析出的歌曲标题
        }
        audio_selector = audio_list_selector.eq(audio_index)
        # 获取歌曲id
        audio_id = audio_selector.find(".content_wrap").attr("sound_id")
        if not crawler.is_integer(audio_id):
            raise crawler.CrawlerException("歌曲信息匹配歌曲id失败\n%s" % audio_list_selector.html().encode("UTF-8"))
        audio_info["audio_id"] = str(audio_id)
        # 获取歌曲标题
        audio_title = audio_selector.find(".sound_title").attr("title")
        if not audio_title:
            raise crawler.CrawlerException("歌曲信息匹配歌曲标题失败\n%s" % audio_list_selector.html().encode("UTF-8"))
        audio_info["audio_title"] = str(audio_title.encode("UTF-8").strip())
        result["audio_info_list"].append(audio_info)
    # 判断是不是最后一页
    max_page_count = 1
    pagination_list_selector = PQ(audit_pagination_response.json_data["html"]).find(".pagingBar_wrapper a.pagingBar_page")
    for pagination_index in range(0, pagination_list_selector.size()):
        pagination_selector = pagination_list_selector.eq(pagination_index)
        data_page = pagination_selector.attr("data-page")
        if data_page is None:
            continue
        if not crawler.is_integer(data_page):
            raise crawler.CrawlerException("分页信息匹配失败\n%s" % audio_list_selector.html().encode("UTF-8"))
        max_page_count = max(max_page_count, int(data_page))
    result["is_over"] = page_count >= max_page_count
    return result


# 获取指定id的歌曲播放页
# audio_id -> 16558983
def get_audio_info_page(audio_id):
    audio_info_url = "http://www.ximalaya.com/tracks/%s.json" % audio_id
    result = {
        "audio_url": None,  # 页面解析出的歌曲地址
    }
    audio_play_response = net.http_request(audio_info_url, method="GET", json_decode=True)
    if audio_play_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(audio_play_response.status))
    if crawler.check_sub_key(("play_path_64",), audio_play_response.json_data):
        result["audio_url"] = str(audio_play_response.json_data["play_path_64"])
    elif crawler.check_sub_key(("play_path_32",), audio_play_response.json_data):
        result["audio_url"] = str(audio_play_response.json_data["play_path_32"])
    elif crawler.check_sub_key(("play_path",), audio_play_response.json_data):
        result["audio_url"] = str(audio_play_response.json_data["play_path"])
    else:
        raise crawler.CrawlerException("返回信息匹配音频地址失败\n%s" % audio_play_response.data)
    return result


class XiMaLaYa(crawler.Crawler):
    def __init__(self):
        sys_config = {
            crawler.SYS_DOWNLOAD_VIDEO: True,
        }
        crawler.Crawler.__init__(self, sys_config)

        # 解析存档文件
        # account_id  last_audio_id
        self.account_list = crawler.read_save_data(self.save_data_path, 0, ["", "0"])

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

        log.step("全部下载完毕，耗时%s秒，共计歌曲%s首" % (self.get_run_time(), self.total_video_count))


class Download(crawler.DownloadThread):
    def __init__(self, account_info, main_thread):
        crawler.DownloadThread.__init__(self, account_info, main_thread)
        self.account_id = self.account_info[0]
        if len(self.account_info) >= 3 and self.account_info[2]:
            self.account_name = self.account_info[2]
        else:
            self.account_name = self.account_info[0]
        self.total_video_count = 0
        log.step(self.account_name + " 开始")

    # 获取所有可下载歌曲
    def get_crawl_list(self):
        page_count = 1
        unique_list = []
        audio_info_list = []
        is_over = False
        # 获取全部还未下载过需要解析的歌曲
        while not is_over:
            log.step(self.account_name + " 开始解析第%s页歌曲" % page_count)

            # 获取一页歌曲
            try:
                audit_pagination_response = get_one_page_audio(self.account_id, page_count)
            except crawler.CrawlerException, e:
                log.error("第%s页歌曲解析失败，原因：%s" % (page_count, e.message))
                break

            log.trace(self.account_name + " 第%s页解析的全部歌曲：%s" % (page_count, audit_pagination_response["audio_info_list"]))

            # 寻找这一页符合条件的媒体
            for audio_info in audit_pagination_response["audio_info_list"]:
                # 检查是否达到存档记录
                if int(audio_info["audio_id"]) > int(self.account_info[1]):
                    # 新增歌曲导致的重复判断
                    if audio_info["audio_id"] in unique_list:
                        continue
                    else:
                        audio_info_list.append(audio_info)
                        unique_list.append(audio_info["audio_id"])
                else:
                    is_over = True
                    break

            if not is_over:
                if audit_pagination_response["is_over"]:
                    is_over = True
                else:
                    page_count += 1

        return audio_info_list

    # 解析单首歌曲
    def crawl_audio(self, audio_info):
        # 获取歌曲播放页
        try:
            audio_play_response = get_audio_info_page(audio_info["audio_id"])
        except crawler.CrawlerException, e:
            log.error("歌曲%s解析失败，原因：%s" % (audio_info["audio_id"], e.message))
            return

        audio_url = audio_play_response["audio_url"]
        audio_title = path.filter_text(audio_info["audio_title"])
        log.step(self.account_name + " 开始下载歌曲%s《%s》 %s" % (audio_info["audio_id"], audio_title, audio_url))

        file_type = audio_url.split(".")[-1]
        file_path = os.path.join(self.main_thread.video_download_path, self.account_name, "%09d - %s.%s" % (int(audio_info["audio_id"]), audio_title, file_type))
        save_file_return = net.save_net_file(audio_url, file_path)
        if save_file_return["status"] == 1:
            log.step(self.account_name + " 歌曲%s《%s》下载成功" % (audio_info["audio_id"], audio_title))
        else:
            log.error(self.account_name + " 歌曲%s《%s》 %s 下载失败，原因：%s" % (audio_info["audio_id"], audio_title, audio_url, crawler.download_failre(save_file_return["code"])))
            return

        # 歌曲下载完毕
        self.total_video_count += 1  # 计数累加
        self.account_info[1] = audio_info["audio_id"]  # 设置存档记录

    def run(self):
        try:
            # 获取所有可下载歌曲
            audio_info_list = self.get_crawl_list()
            log.step(self.account_name + " 需要下载的全部歌曲解析完毕，共%s个" % len(audio_info_list))

            # 从最早的媒体开始下载
            while len(audio_info_list) > 0:
                audio_info = audio_info_list.pop()
                log.step(self.account_name + " 开始解析歌曲%s" % audio_info["audio_id"])
                self.crawl_audio(audio_info)
                self.main_thread_check()  # 检测主线程运行状态
        except SystemExit, se:
            if se.code == 0:
                log.step(self.account_name + " 提前退出")
            else:
                log.error(self.account_name + " 异常退出")
        except Exception, e:
            log.error(self.account_name + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 保存最后的信息
        with self.thread_lock:
            tool.write_file("\t".join(self.account_info), self.main_thread.temp_save_data_path)
            self.main_thread.total_video_count += self.total_video_count
            self.main_thread.account_list.pop(self.account_id)
        log.step(self.account_name + " 下载完毕，总共获得%s首歌曲" % self.total_video_count)
        self.notify_main_thread()


if __name__ == "__main__":
    XiMaLaYa().main()
