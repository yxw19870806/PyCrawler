# -*- coding:UTF-8  -*-
"""
V聊视频爬虫
http://www.vliaoapp.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import os
import threading
import time
import traceback
from common import *
import vLiaoCommon


# 获取一页视频
def get_one_page_video(account_id, page_count):
    video_pagination_url = "http://v3.vliao3.xyz/v%s/smallvideo/list" % vLiaoCommon.API_VERSION
    post_data = {
        "userId": vLiaoCommon.USER_ID,
        "userKey": vLiaoCommon.USER_KEY,
        "page": page_count,
        "vid": account_id,
    }
    video_pagination_response = net.http_request(video_pagination_url, method="POST", fields=post_data, json_decode=True)
    result = {
        "video_info_list": [],  # 全部视频信息
    }
    if video_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(video_pagination_response.status))
    # 判断是不是最后一页
    if not crawler.check_sub_key(("result",), video_pagination_response.json_data):
        raise crawler.CrawlerException("返回信息'result'字段不存在\n%s" % video_pagination_response.json_data)
    if video_pagination_response.json_data["result"] is False:
        if crawler.check_sub_key(("errorCode",), video_pagination_response.json_data) and video_pagination_response.json_data["errorCode"] == 3:
            raise crawler.CrawlerException("账号不存在")
    # 判断是不是最后一页
    if not crawler.check_sub_key(("maxPage",), video_pagination_response.json_data):
        raise crawler.CrawlerException("返回信息'maxPage'字段不存在\n%s" % video_pagination_response.json_data)
    if not crawler.is_integer(video_pagination_response.json_data["maxPage"]):
        raise crawler.CrawlerException("返回信息'maxPage'字段类型不正确\n%s" % video_pagination_response.json_data)
    result["is_over"] = int(video_pagination_response.json_data["maxPage"]) <= page_count
    # 获取全部视频id
    if not crawler.check_sub_key(("data",), video_pagination_response.json_data):
        raise crawler.CrawlerException("返回信息'data'字段不存在\n%s" % video_pagination_response.json_data)
    for video_info in video_pagination_response.json_data["data"]:
        result_video_info = {
            "video_id": None,  # 视频id
            "video_title": None,  # 视频id
        }
        # 获取视频id
        if not crawler.check_sub_key(("id",), video_info):
            raise crawler.CrawlerException("视频信息'id'字段不存在\n%s" % video_info)
        if not crawler.is_integer(video_info["id"]):
            raise crawler.CrawlerException("视频信息'id'字段类型不正确\n%s" % video_info)
        result_video_info["video_id"] = str(video_info["id"])
        # 获取视频标题
        if not crawler.check_sub_key(("title",), video_info):
            raise crawler.CrawlerException("视频信息'title'字段不存在\n%s" % video_info)
        result_video_info["video_title"] = str(video_info["title"].encode("UTF-8"))
        result["video_info_list"].append(result_video_info)
    return result


# 获取指定视频
def get_video_info_page(account_id, video_id):
    video_info_url = "http://v3.vliao3.xyz/v%s/smallvideo/one" % vLiaoCommon.API_VERSION
    post_data = {
        "userId": vLiaoCommon.USER_ID,
        "userKey": vLiaoCommon.USER_KEY,
        "videoId": video_id,
        "vid": account_id,
    }
    video_info_response = net.http_request(video_info_url, method="POST", fields=post_data, json_decode=True)
    result = {
        "video_url": None,  # 视频地址
    }
    if video_info_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(video_info_response.status))
    if not crawler.check_sub_key(("data",), video_info_response.json_data):
        raise crawler.CrawlerException("返回信息'data'字段不存在\n%s" % video_info_response.json_data)
    if not crawler.check_sub_key(("url",), video_info_response.json_data["data"]):
        raise crawler.CrawlerException("返回信息'url'字段不存在\n%s" % video_info_response.json_data)
    result["video_url"] = str(video_info_response.json_data["data"]["url"])
    return result


class VLiao(crawler.Crawler):
    def __init__(self):
        sys_config = {
            crawler.SYS_DOWNLOAD_VIDEO: True,
        }
        crawler.Crawler.__init__(self, sys_config)

        # 解析存档文件
        # account_id  video_id
        self.account_list = crawler.read_save_data(self.save_data_path, 0, ["", "0"])

        # 检测登录状态
        if not vLiaoCommon.check_login():
            log.error("没有检测到登录状态，退出程序")
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

        log.step("全部下载完毕，耗时%s秒，共计视频%s个" % (self.get_run_time(), self.total_video_count))


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
        page_count = 1
        video_info_list = []
        is_over = False
        # 获取全部还未下载过需要解析的视频
        while not is_over:
            self.main_thread_check()  # 检测主线程运行状态
            log.step(self.account_name + " 开始解析第%s页视频" % page_count)

            # 获取指定一页视频
            try:
                video_pagination_response = get_one_page_video(self.account_id, page_count)
            except crawler.CrawlerException, e:
                log.error(self.account_name + " 第%s页视频解析失败，原因：%s" % (page_count, e.message))
                raise

            log.trace(self.account_name + " 第%s页解析的全部视频：%s" % (page_count, video_pagination_response["video_info_list"]))

            # 寻找这一页符合条件的视频
            for video_info in video_pagination_response["video_info_list"]:
                # 检查是否达到存档记录
                if int(video_info["video_id"]) > int(self.account_info[1]):
                    video_info_list.append(video_info)
                else:
                    is_over = True
                    break

            # 没有视频了
            if video_pagination_response["is_over"]:
                is_over = True
            else:
                page_count += 1

        return video_info_list

    # 解析单个视频
    def crawl_video(self, video_info):
        # 获取指定视频
        try:
            video_info_response = get_video_info_page(self.account_id, video_info["video_id"])
        except crawler.CrawlerException, e:
            log.error(self.account_name + " 视频%s 《%s》解析失败，原因：%s" % (video_info["video_id"], video_info["video_title"], e.message))
            raise

        # 视频下载
        self.main_thread_check()  # 检测主线程运行状态
        log.step(self.account_name + " 开始下载视频 %s 《%s》" % (video_info["video_id"], video_info["video_title"]))
        video_title = path.filter_text(video_info["video_title"])
        video_file_path = os.path.join(self.main_thread.video_download_path, self.account_name, "%06d %s.mp4" % (int(video_info["video_id"]), video_title))
        save_file_return = net.save_net_file(video_info_response["video_url"], video_file_path)
        if save_file_return["status"] == 1:
            log.step(self.account_name + " 视频 %s 《%s》下载成功" % (video_info["video_id"], video_info["video_title"]))
        else:
            log.error(self.account_name + " 视频 %s 《%s》 %s 下载失败，原因：%s" % (video_info["video_id"], video_info["video_title"], video_info_response["video_url"], crawler.download_failre(save_file_return["code"])))
            return

        # 媒体内图片和视频全部下载完毕
        self.temp_path_list = []  # 临时目录设置清除
        self.total_video_count += 1  # 计数累加
        self.account_info[1] = video_info["video_id"]  # 设置存档记录

    def run(self):
        try:
            # 获取所有可下载视频
            video_info_list = self.get_crawl_list()
            log.step(self.account_name + " 需要下载的全部视频解析完毕，共%s个" % len(video_info_list))

            # 从最早的视频开始下载
            while len(video_info_list) > 0:
                video_info = video_info_list.pop()
                log.step(self.account_name + " 开始解析视频%s 《%s》" % (video_info["video_id"], video_info["video_title"]))
                self.crawl_video(video_info)
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
    VLiao().main()
