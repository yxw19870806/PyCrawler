# -*- coding:UTF-8  -*-
"""
微视视频爬虫
http://weishi.qq.com
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, net, robot, tool
import json
import os
import random
import threading
import time
import traceback

ACCOUNTS = []
VIDEO_COUNT_PER_PAGE = 5
TOTAL_VIDEO_COUNT = 0
GET_VIDEO_COUNT = 0
VIDEO_TEMP_PATH = ""
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_SORT = True


# 获取指定一页的视频信息
def get_one_page_video_data(account_id, page_time):
    index_page_url = "http://wsm.qq.com/weishi/t/other.php?uid=%s&reqnum=%s" % (account_id, VIDEO_COUNT_PER_PAGE)
    if page_time > 0:
        index_page_url += "&pageflag=02&pagetime=%s" % page_time
    else:
        index_page_url += "&pageflag=0"
    extra_info = {
        "is_error": False,  # 是不是格式不符合
        "video_info_list": [],  # 页面解析出的视频信息列表
        "is_over": False,  # 是不是最后一页视频
    }
    header_list = {"Referer": "http://weishi.qq.com/"}
    index_page_response = net.http_request(index_page_url, header_list=header_list, json_decode=True)
    if index_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if (
            robot.check_sub_key(("ret", "data"), index_page_response.json_data) and
            int(index_page_response.json_data["ret"]) == 0 and
            robot.check_sub_key(("info", "hasNext"), index_page_response.json_data["data"])
        ):
            for video_info in index_page_response.json_data["data"]["info"]:
                extra_video_info = {
                    "video_id": None,  # 视频id
                    "video_part_id_list": [],  # 视频分集id
                    "video_time": None,  # 视频上传时间
                    "json_data": video_info,  # 原始数据
                }
                if robot.check_sub_key(("newvideos", "id", "timestamp"), video_info):
                    # 获取视频id
                    extra_video_info["video_id"] = str(video_info["id"])
                    # 获取分集id
                    video_part_id_list = []
                    for video_part_info in video_info["newvideos"]:
                        if robot.check_sub_key(("vid",), video_part_info):
                            video_part_id_list.append(str(video_part_info["vid"]))
                        else:
                            video_part_id_list = []
                            break
                    extra_video_info["video_part_id_list"] = video_part_id_list
                    # 获取视频上传时间
                    if isinstance(video_info["timestamp"], int) or str(video_info["timestamp"]).isdigit():
                        extra_video_info["video_time"] = int(video_info["timestamp"])
                extra_info["video_info_list"].append(extra_video_info)
            # 检测是否还有下一页
            extra_info["is_over"] = bool(index_page_response.json_data["data"]["hasNext"])
        else:
            extra_info["is_error"] = True
    index_page_response.extra_info = extra_info
    return index_page_response


# 根据视频id和vid获取视频下载地址
def get_video_url(video_vid, video_id):
    video_info_url = "http://wsi.weishi.com/weishi/video/downloadVideo.php?vid=%s&id=%s" % (video_vid, video_id)
    video_info_page_response = net.http_request(video_info_url)
    if video_info_page_response.status == 200:
        try:
            video_info_page = json.loads(video_info_page_response.data)
        except ValueError:
            pass
        else:
            if robot.check_sub_key(("data",), video_info_page):
                if robot.check_sub_key(("url",), video_info_page["data"]):
                    return str(random.choice(video_info_page["data"]["url"]))
    return None


class WeiShi(robot.Robot):
    def __init__(self):
        global GET_VIDEO_COUNT
        global VIDEO_TEMP_PATH
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT

        sys_config = {
            robot.SYS_DOWNLOAD_VIDEO: True,
        }
        robot.Robot.__init__(self, sys_config, use_urllib3=True)

        # 设置全局变量，供子线程调用
        GET_VIDEO_COUNT = self.get_video_count
        VIDEO_TEMP_PATH = self.video_temp_path
        VIDEO_DOWNLOAD_PATH = self.video_download_path
        IS_SORT = self.is_sort
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

    def main(self):
        global ACCOUNTS

        # 解析存档文件
        # account_id  video_count  last_video_time
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0"])
        ACCOUNTS = account_list.keys()

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

        # 删除临时文件夹
        self.finish_task()

        # 重新排序保存存档文件
        robot.rewrite_save_file(NEW_SAVE_DATA_PATH, self.save_data_path)

        log.step("全部下载完毕，耗时%s秒，共计视频%s个" % (self.get_run_time(), TOTAL_VIDEO_COUNT))


class Download(threading.Thread):
    def __init__(self, account_info, thread_lock):
        threading.Thread.__init__(self)
        self.account_info = account_info
        self.thread_lock = thread_lock

    def run(self):
        global TOTAL_VIDEO_COUNT

        account_id = self.account_info[0]
        if len(self.account_info) >= 4 and self.account_info[3]:
            account_name = self.account_info[3]
        else:
            account_name = self.account_info[0]

        try:
            log.step(account_name + " 开始")

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if IS_SORT:
                video_path = os.path.join(VIDEO_TEMP_PATH, account_name)
            else:
                video_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)

            video_count = 1
            page_time = 0
            first_video_time = "0"
            need_make_video_dir = True
            is_over = False
            while not is_over:
                log.step(account_name + " 开始解析第%s页视频" % video_count)

                # 获取一页视频信息
                index_page_response = get_one_page_video_data(account_id, page_time)
                if index_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                    log.error(account_name + " %s后的一页视频访问失败，原因：%s" % (page_time, robot.get_http_request_failed_reason(index_page_response.status)))
                    tool.process_exit()

                if index_page_response.extra_info["is_error"]:
                    log.error(account_name + " %s后的一页视频信息%s解析失败" % (page_time, index_page_response.json_data))
                    tool.process_exit()

                for video_info in index_page_response.extra_info["video_info_list"]:
                    if video_info["video_id"] is None:
                        log.error(account_name + " 第%s个视频信息%s的视频id解析失败" % (video_count, video_info["json_data"]))
                        tool.process_exit()

                    if len(video_info["video_part_id_list"]) == 0:
                        log.error(account_name + " 第%s个视频信息%s的视频分集id解析失败" % (video_count, video_info["json_data"]))
                        tool.process_exit()

                    if video_info["video_time"] is None:
                        log.error(account_name + " 第%s个视频信息%s的视频时间解析失败" % (video_count, video_info["json_data"]))
                        tool.process_exit()

                    # 检查是否已下载到前一次的视频
                    if video_info["video_time"] <= int(self.account_info[2]):
                        is_over = True
                        break

                    # 将第一个视频的上传时间做为新的存档记录
                    if first_video_time == "0":
                        first_video_time = str(video_info["video_time"])

                    for video_part_id in video_info["video_part_id_list"]:
                        # 获取视频下载地址
                        video_url = get_video_url(video_part_id, video_info["video_id"])
                        log.step(account_name + " 开始下载第%s个视频 %s" % (video_count, video_url))

                        # 第一个视频，创建目录
                        if need_make_video_dir:
                            if not tool.make_dir(video_path, 0):
                                log.error(account_name + " 创建图片下载目录 %s 失败" % video_path)
                                tool.process_exit()
                            need_make_video_dir = False

                        file_type = video_url.split(".")[-1].split("?")[0]
                        file_path = os.path.join(video_path, "%04d.%s" % (video_count, file_type))
                        save_file_return = net.save_net_file(video_url, file_path)
                        if save_file_return["status"] == 1:
                            log.step(account_name + " 第%s个视频下载成功" % video_count)
                            video_count += 1
                        else:
                            log.error(account_name + " 第%s个视频 %s 下载失败" % (video_count, video_url))

                    # 达到配置文件中的下载数量，结束
                    if 0 < GET_VIDEO_COUNT < video_count:
                        is_over = True
                        break

                    page_time = video_info["video_time"]

                if not is_over:
                    if index_page_response.extra_info["is_over"]:
                        is_over = True

            log.step(account_name + " 下载完毕，总共获得%s个视频" % (video_count - 1))

            # 排序
            if IS_SORT and video_count > 1:
                log.step(account_name + " 视频开始从下载目录移动到保存目录")
                destination_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)
                if robot.sort_file(video_path, destination_path, int(self.account_info[3]), 4):
                    log.step(account_name + " 视频从下载目录移动到保存目录成功")
                else:
                    log.error(account_name + " 创建视频保存目录 %s 失败" % destination_path)
                    tool.process_exit()

            # 新的存档记录
            if first_video_time != "0":
                self.account_info[3] = str(int(self.account_info[3]) + video_count - 1)
                self.account_info[4] = first_video_time

            # 保存最后的信息
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            self.thread_lock.acquire()
            TOTAL_VIDEO_COUNT += video_count - 1
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
    WeiShi().main()
