# -*- coding:UTF-8  -*-
"""
微视视频爬虫
http://weishi.qq.com
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, robot, tool
import json
import os
import random
import threading
import time
import traceback

ACCOUNTS = []
TOTAL_VIDEO_COUNT = 0
GET_VIDEO_COUNT = 0
VIDEO_TEMP_PATH = ""
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_SORT = True


# 获取账号指定一页的视频信息
def get_one_page_video_data(account_id, page_time):
    video_data_url = "http://wsm.qq.com/weishi/t/other.php?uid=%s&reqnum=5" % account_id
    if page_time > 0:
        video_data_url += "&pageflag=02&pagetime=%s" % page_time
    else:
        video_data_url += "&pageflag=0"
    header_list = {"Referer": 'http://weishi.qq.com/'}
    video_data_return_code, video_data = tool.http_request(video_data_url, None, header_list)[:2]
    if video_data_return_code == 1:
        try:
            video_data = json.loads(video_data)
        except ValueError:
            pass
        else:
            if robot.check_sub_key(("ret", "data"), video_data) and int(video_data["ret"]) == 0:
                if robot.check_sub_key(("info", "hasNext"), video_data["data"]):
                    return video_data["data"]
    return None


# 根据视频id和vid获取视频下载地址
def get_video_url(video_vid, video_id):
    video_info_url = "http://wsi.weishi.com/weishi/video/downloadVideo.php?vid=%s&id=%s" % (video_vid, video_id)
    video_info_page_return_code, video_info_page = tool.http_request(video_info_url)[:2]
    if video_info_page_return_code == 1:
        try:
            video_info_page = json.loads(video_info_page)
        except ValueError:
            pass
        else:
            if robot.check_sub_key(("data", ), video_info_page):
                if robot.check_sub_key(("url", ), video_info_page["data"]):
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
        robot.Robot.__init__(self, sys_config)

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
        tool.remove_dir(VIDEO_TEMP_PATH)

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
                # 获取一页视频信息
                video_data = get_one_page_video_data(account_id, page_time)
                if video_data is None:
                    log.error(account_name + " 视频列表获取失败")
                    tool.process_exit()

                for video_info in video_data["info"]:
                    if not robot.check_sub_key(("newvideos", "id", "timestamp"), video_info):
                        log.error(account_name + " 视频信息 %s 解析失败" % video_info)
                        continue

                    page_time = int(video_info["timestamp"])
                    # 检查是否已下载到前一次的视频
                    if page_time <= int(self.account_info[2]):
                        is_over = True
                        break

                    # 将第一个视频的上传时间做为新的存档记录
                    if first_video_time == "0":
                        first_video_time = str(page_time)

                    # todo 处理如果有多个视频
                    if len(video_info["newvideos"]) != 1:
                        log.error(account_name + " 视频信息 %s 发现多个视频下载信息" % video_info)
                        continue
                    if not robot.check_sub_key(("vid",), video_info["newvideos"][0]):
                        log.error(account_name + " 视频信息 %s 解析vid失败" % video_info)
                        continue

                    # 获取视频下载地址
                    video_url = get_video_url(video_info["newvideos"][0]["vid"], video_info["id"])
                    log.step(account_name + " 开始下载第%s个视频 %s" % (video_count, video_url))

                    # 第一个视频，创建目录
                    if need_make_video_dir:
                        if not tool.make_dir(video_path, 0):
                            log.error(account_name + " 创建图片下载目录 %s 失败" % video_path)
                            tool.process_exit()
                        need_make_video_dir = False

                    file_type = video_url.split(".")[-1].split("?")[0]
                    file_path = os.path.join(video_path, "%04d.%s" % (video_count, file_type))
                    if tool.save_net_file(video_url, file_path):
                        log.step(account_name + " 第%s个视频下载成功" % video_count)
                        video_count += 1
                    else:
                        log.error(account_name + " 第%s个视频 %s 下载失败" % (video_count, video_url))

                if not video_data["hasNext"]:
                    is_over = True

            log.step(account_name + " 下载完毕，总共获得%s个视频" % (video_count - 1))

            # 排序
            if IS_SORT:
                if first_video_time != "0":
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
