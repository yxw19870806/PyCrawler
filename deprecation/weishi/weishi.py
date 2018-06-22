# -*- coding:UTF-8  -*-
"""
微视视频爬虫
http://weishi.qq.com
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import os
import random
import threading
import time
import traceback
from common import *

VIDEO_COUNT_PER_PAGE = 5


# 获取指定一页的视频信息
def get_one_page_video(account_id, page_time):
    video_pagination_url = "http://wsm.qq.com/weishi/t/other.php"
    query_data = {
        "uid": account_id,
        "reqnum": VIDEO_COUNT_PER_PAGE,
    }
    if page_time > 0:
        query_data["pageflag"] = "02"
        query_data["pagetime"] = page_time
    else:
        query_data["pageflag"] = "0"
    result = {
        "is_over": False,  # 是不是最后一页视频
        "video_info_list": [],  # 全部视频信息
    }
    header_list = {"Referer": "http://weishi.qq.com/"}
    video_pagination_response = net.http_request(video_pagination_url, method="GET", fields=query_data, header_list=header_list, json_decode=True)
    if video_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(video_pagination_response.status))
    if not crawler.check_sub_key(("ret",), video_pagination_response.json_data):
        raise crawler.CrawlerException("返回信息'ret'字段不存在\n%s" % video_pagination_response.json_data)
    if int(video_pagination_response.json_data["ret"]) != 0:
        if int(video_pagination_response.json_data["ret"]) == -6:
            raise crawler.CrawlerException("账号不存在")
        else:
            raise crawler.CrawlerException("返回信息'ret'字段取值不正确\n%s" % video_pagination_response.json_data)
    if not crawler.check_sub_key(("data",), video_pagination_response.json_data):
        raise crawler.CrawlerException("返回信息'data'字段不存在\n%s" % video_pagination_response.json_data)
    if not crawler.check_sub_key(("info", "hasNext"), video_pagination_response.json_data["data"]):
        raise crawler.CrawlerException("返回信息'info'或'hasNext'字段不存在\n%s" % video_pagination_response.json_data)
    for video_info in video_pagination_response.json_data["data"]["info"]:
        result_video_info = {
            "video_id": None,  # 视频id
            "video_part_id_list": [],  # 视频分集id
            "video_time": None,  # 视频上传时间
        }
        # 获取视频id
        if not crawler.check_sub_key(("id",), video_info):
            raise crawler.CrawlerException("视频信息'id'字段不存在\n%s" % video_info)
        result_video_info["video_id"] = str(video_info["id"])
        # 获取分集id
        if not crawler.check_sub_key(("newvideos",), video_info):
            raise crawler.CrawlerException("视频信息'newvideos'字段不存在\n%s" % video_info)
        if not isinstance(video_info["newvideos"], list):
            raise crawler.CrawlerException("视频信息'newvideos'字段类型不正确\n%s" % video_info)
        if len(video_info["newvideos"]) == 0:
            raise crawler.CrawlerException("视频信息'newvideos'字段长度不正确\n%s" % video_info)
        for video_part_info in video_info["newvideos"]:
            if not crawler.check_sub_key(("vid",), video_part_info):
                raise crawler.CrawlerException("视频分集信息'vid'字段不存在\n%s" % video_info)
            result_video_info["video_part_id_list"].append(str(video_part_info["vid"]))
        # 获取视频id
        if not crawler.check_sub_key(("timestamp",), video_info):
            raise crawler.CrawlerException("视频信息'timestamp'字段不存在\n%s" % video_info)
        if not crawler.is_integer(video_info["timestamp"]):
            raise crawler.CrawlerException("视频信息'timestamp'字段类型不正确\n%s" % video_info)
        result_video_info["video_time"] = int(video_info["timestamp"])
        result["video_info_list"].append(result_video_info)
    # 检测是否还有下一页
    result["is_over"] = bool(video_pagination_response.json_data["data"]["hasNext"])
    return result


# 根据视频id和vid获取视频下载地址
def get_video_info_page(video_vid, video_id):
    video_info_url = "http://wsi.weishi.com/weishi/video/downloadVideo.php?vid=%s&id=%s" % (video_vid, video_id)
    video_info_response = net.http_request(video_info_url, method="GET", json_decode=True)
    result = {
        "video_url": "",  # 视频地址
    }
    if video_info_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(video_info_response.status))
    if not crawler.check_sub_key(("data",), video_info_response.json_data):
        raise crawler.CrawlerException("返回信息'data'字段不存在\n%s" % video_info_response.json_data)
    if not crawler.check_sub_key(("url",), video_info_response.json_data["data"]):
        raise crawler.CrawlerException("返回信息'url'字段不存在\n%s" % video_info_response.json_data)
    result["video_url"] = str(random.choice(video_info_response.json_data["data"]["url"]))
    return result


class WeiShi(crawler.Crawler):
    def __init__(self):
        sys_config = {
            crawler.SYS_DOWNLOAD_VIDEO: True,
        }
        crawler.Crawler.__init__(self, sys_config)

        # 解析存档文件
        # account_id  video_count  last_video_time
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

    def run(self):
        account_id = self.account_info[0]
        if len(self.account_info) >= 4 and self.account_info[3]:
            account_name = self.account_info[3]
        else:
            account_name = self.account_info[0]
        total_video_count = 0
        temp_path_list = []

        try:
            log.step(account_name + " 开始")

            page_time = 0
            video_info_list = []
            is_over = False
            # 获取全部还未下载过需要解析的视频
            while not is_over:
                self.main_thread_check()  # 检测主线程运行状态
                log.step(account_name + " 开始解析%s后的一页视频" % page_time)

                # 获取一页视频信息
                try:
                    video_pagination_response = get_one_page_video(account_id, page_time)
                except crawler.CrawlerException, e:
                    log.error(account_name + " %s后的一页视频解析失败，原因：%s" % (page_time, e.message))
                    raise

                log.step(account_name + " %s后一页解析的全部视频：%s" % (page_time, video_pagination_response["video_info_list"]))

                # 寻找这一页符合条件的视频
                for video_info in video_pagination_response["video_info_list"]:
                    # 检查是否达到存档记录
                    if video_info["video_time"] > int(self.account_info[2]):
                        video_info_list.append(video_info)
                        # 设置下一页指针
                        page_time = video_info["video_time"]
                    else:
                        is_over = True
                        break

                if not is_over:
                    if video_pagination_response["is_over"]:
                        is_over = True

            # 从最早的视频开始下载
            while len(video_info_list) > 0:
                video_info = video_info_list.pop()
                video_index = int(self.account_info[1]) + 1
                # 单个视频存在多个分集
                for video_part_id in video_info["video_part_id_list"]:
                    self.main_thread_check()  # 检测主线程运行状态
                    log.step(account_name + " 开始解析视频%s" % video_part_id)
                    # 获取视频下载地址
                    try:
                        video_info_response = get_video_info_page(video_part_id, video_info["video_id"])
                    except crawler.CrawlerException, e:
                        log.error(account_name + " 视频%s（%s）解析失败，原因：%s" % (video_part_id, video_info["video_id"], e.message))
                        raise
                    log.step(account_name + " 开始下载第%s个视频 %s" % (video_index, video_info_response["video_url"]))

                    file_type = video_info_response["video_url"].split(".")[-1].split("?")[0]
                    file_path = os.path.join(self.main_thread.video_download_path, account_name, "%04d.%s" % (video_index, file_type))
                    save_file_return = net.save_net_file(video_info_response["video_url"], file_path)
                    if save_file_return["status"] == 1:
                        temp_path_list.append(file_path)
                        log.step(account_name + " 第%s个视频下载成功" % video_index)
                        video_index += 1
                    else:
                        log.error(account_name + " 第%s个视频 %s 下载失败" % (video_index, video_info_response["video_url"]))
                # 视频全部下载完毕
                temp_path_list = []  # 临时目录设置清除
                total_video_count += (video_index - 1) - int(self.account_info[1])  # 计数累加
                self.account_info[1] = str(video_index - 1)  # 设置存档记录
                self.account_info[2] = str(video_info["video_time"])
        except SystemExit, se:
            if se.code == 0:
                log.step(account_name + " 提前退出")
            else:
                log.error(account_name + " 异常退出")
            # 如果临时目录变量不为空，表示某个视频正在下载中，需要把下载了部分的内容给清理掉
            if len(temp_path_list) > 0:
                for temp_path in temp_path_list:
                    path.delete_dir_or_file(temp_path)
        except Exception, e:
            log.error(account_name + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 保存最后的信息
        with self.thread_lock:
            tool.write_file("\t".join(self.account_info), self.main_thread.temp_save_data_path)
            self.main_thread.total_video_count += total_video_count
            self.main_thread.account_list.pop(account_id)
        log.step(account_name + " 下载完毕，总共获得%s个视频" % total_video_count)
        self.notify_main_thread()


if __name__ == "__main__":
    WeiShi().main()
