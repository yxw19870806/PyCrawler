# -*- coding:UTF-8  -*-
"""
抖音视频爬虫
https://www.douyin.com
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import os
import threading
import time
import traceback

EACH_PAGE_VIDEO_COUNT = 21


# 获取指定页数的全部视频
def get_one_page_video(account_id, cursor_id):
    api_url = "https://www.douyin.com/aweme/v1/aweme/post/"
    query_data = {
        "user_id": account_id,
        "max_cursor": cursor_id,
        "count": EACH_PAGE_VIDEO_COUNT,
    }
    video_pagination_response = net.http_request(api_url, method="GET", fields=query_data, json_decode=True)
    result = {
        "is_over": False,  # 是不是最后一页视频
        "next_page_cursor_id": None,  # 下一页视频指针
        "video_info_list": [],  # 全部视频信息
    }
    if video_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(video_pagination_response.status))
    # 判断是不是最后一页
    if not crawler.check_sub_key(("has_more",), video_pagination_response.json_data):
        raise crawler.CrawlerException("返回信息'has_more'字段不存在\n%s" % video_pagination_response.json_data)
    result["is_over"] = video_pagination_response.json_data["has_more"] == 0
    # 判断是不是最后一页
    if not result["is_over"]:
        if not crawler.check_sub_key(("max_cursor",), video_pagination_response.json_data):
            raise crawler.CrawlerException("返回信息'max_cursor'字段不存在\n%s" % video_pagination_response.json_data)
        if not crawler.is_integer(video_pagination_response.json_data["max_cursor"]):
            raise crawler.CrawlerException("返回信息'max_cursor'字段类型不正确\n%s" % video_pagination_response.json_data)
        result["next_page_cursor_id"] = int(video_pagination_response.json_data["max_cursor"])
    # 获取全部视频id
    if not crawler.check_sub_key(("aweme_list",), video_pagination_response.json_data):
        raise crawler.CrawlerException("返回信息'aweme_list'字段不存在\n%s" % video_pagination_response.json_data)
    if not isinstance(video_pagination_response.json_data["aweme_list"], list):
        raise crawler.CrawlerException("返回信息'aweme_list'字段类型不正确\n%s" % video_pagination_response.json_data)
    for video_info in video_pagination_response.json_data["aweme_list"]:
        result_video_info = {
            "video_id": None, # 视频id
            "video_url": None, # 视频地址
        }
        # 获取视频id
        if not crawler.check_sub_key(("aweme_id",), video_info):
            raise crawler.CrawlerException("视频信息'aweme_id'字段不存在\n%s" % video_info)
        if not crawler.is_integer(video_info["aweme_id"]):
            raise crawler.CrawlerException("视频信息'aweme_id'字段类型不正确\n%s" % video_info)
        result_video_info["video_id"] = int(video_info["aweme_id"])
        # 获取视频地址
        if not crawler.check_sub_key(("video",), video_info):
            raise crawler.CrawlerException("视频信息'video'字段不存在\n%s" % video_info)
        if not crawler.check_sub_key(("play_addr",), video_info["video"]):
            raise crawler.CrawlerException("视频信息'play_addr'字段不存在\n%s" % video_info)
        if not crawler.check_sub_key(("url_list",), video_info["video"]["play_addr"]):
            raise crawler.CrawlerException("视频信息'url_list'字段不存在\n%s" % video_info)
        if not isinstance(video_info["video"]["play_addr"]["url_list"], list):
            raise crawler.CrawlerException("视频信息'url_list'字段类型不正确\n%s" % video_info)
        if len(video_info["video"]["play_addr"]["url_list"]) == 0:
            raise crawler.CrawlerException("视频信息'url_list'字段长度不正确\n%s" % video_info)
        result_video_info["video_url"] = str(video_info["video"]["play_addr"]["url_list"][0])
        result["video_info_list"].append(result_video_info)
    return result


class DouYin(crawler.Crawler):
    def __init__(self):
        sys_config = {
            crawler.SYS_DOWNLOAD_VIDEO: True,
        }
        crawler.Crawler.__init__(self, sys_config)

        # 解析存档文件
        # account_name account_id  last_video_id
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

        log.step("全部下载完毕，耗时%s秒，共计视频%s个" % (self.get_run_time(), self.total_video_count))


class Download(crawler.DownloadThread):
    def __init__(self, account_info, main_thread):
        crawler.DownloadThread.__init__(self, account_info, main_thread)
        self.account_id = self.account_info[0]
        if len(self.account_info) >= 4 and self.account_info[3]:
            self.account_name = self.account_info[3]
        else:
            self.account_name = self.account_info[0]
        log.step(self.account_name + " 开始")

    # 获取所有可下载视频
    def get_crawl_list(self):
        cursor_id = 0
        video_info_list = []
        is_over = False
        # 获取全部还未下载过需要解析的视频
        while not is_over:
            self.main_thread_check()  # 检测主线程运行状态
            log.step(self.account_name + " 开始解析cursor %s后的一页视频" % cursor_id)

            # 获取指定一页的视频信息
            try:
                video_pagination_response = get_one_page_video(self.account_info[1], cursor_id)
            except crawler.CrawlerException, e:
                log.error(self.account_name + " cursor %s后的一页视频解析失败，原因：%s" % (cursor_id, e.message))
                raise
            print video_pagination_response
            log.trace(self.account_name + " cursor %s后的一页视频：%s" % (cursor_id, video_pagination_response["video_info_list"]))

            # 寻找这一页符合条件的视频
            for video_info in video_pagination_response["video_info_list"]:
                # 检查是否达到存档记录
                if video_info["video_id"] > int(self.account_info[2]):
                    video_info_list.append(video_info)
                else:
                    is_over = True
                    break

            # 没有视频了
            if video_pagination_response["is_over"]:
                is_over = True
            else:
                cursor_id = video_pagination_response["next_page_cursor_id"]
        return video_info_list

    # 解析单个视频
    def crawl_video(self, video_info):
        log.step(self.account_name + " 开始下载视频%s %s" % (video_info["video_id"], video_info["video_url"]))
        file_path = os.path.join(self.main_thread.video_download_path, self.account_name, "%020d.mp4" % video_info["video_id"])
        save_file_return = net.save_net_file(video_info["video_url"], file_path)
        if save_file_return["status"] == 1:
            log.step(self.account_name + " 视频%s下载成功" % video_info["video_id"])
        else:
            log.error(self.account_name + " 视频%s %s 下载失败，原因：%s" % (video_info["video_id"], video_info["video_url"], crawler.download_failre(save_file_return["code"])))

        # 视频下载完毕
        self.account_info[1] = str(video_info["video_id"])  # 设置存档记录
        self.total_video_count += 1  # 计数累加

    def run(self):
        try:
            # 获取所有可下载视频
            video_id_list = self.get_crawl_list()
            log.step(self.account_name + " 需要下载的全部视频解析完毕，共%s个" % len(video_id_list))

            # 从最早的视频开始下载
            while len(video_id_list) > 0:
                video_id = video_id_list.pop()
                log.step(self.account_name + " 开始解析第%s个视频 %s" % (int(self.account_info[1]) + 1, video_id))
                self.crawl_video(video_id)
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
        log.step(self.account_name + " 下载完毕，总共获得%s个视频" % self.total_video_count)
        self.notify_main_thread()


if __name__ == "__main__":
    DouYin().main()
