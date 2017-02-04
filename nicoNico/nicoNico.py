# -*- coding:UTF-8  -*-
"""
模板
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, net, robot, tool
import json
import os
import re
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


# 获取所有的视频信息列表
# account_id => 15614906
def get_video_info_list(account_id):
    # http://www.nicovideo.jp/mylist/15614906#+page=1
    video_page_url = "http://www.nicovideo.jp/mylist/%s" % account_id
    video_page_response = net.http_request(video_page_url)
    if video_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        video_data = tool.find_sub_string(video_page_response.data, "Mylist.preload(%s," % account_id, ");").strip()
        try:
            video_data = json.loads(video_data)
        except ValueError:
            pass
        else:
            # 倒序排列，时间越晚的越前面
            video_data.reverse()
            return video_data
    return None


# 根据视频id，获取视频的下载地址
def get_video_url(video_id):
    return ""


class NicoNico(robot.Robot):
    def __init__(self):
        global GET_VIDEO_COUNT
        global VIDEO_TEMP_PATH
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT

        sys_config = {
            robot.SYS_DOWNLOAD_VIDEO: True,
            robot.SYS_SET_PROXY: True,
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
        # account_id  last_video_id
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "0"])
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
        if len(self.account_info) >= 3 and self.account_info[2]:
            account_name = self.account_info[2]
        else:
            account_name = self.account_info[0]

        try:
            log.step(account_name + " 开始")

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if IS_SORT:
                video_path = os.path.join(VIDEO_TEMP_PATH, account_name)
            else:
                video_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)

            # 获取视频信息列表
            video_info_list = get_video_info_list(account_id)
            if video_info_list is None:
                log.error(account_name + " 视频列表解析失败")
                tool.process_exit()

            video_count = 1
            first_video_id = "0"
            need_make_video_dir = True
            for video_info in video_info_list:
                if not robot.check_sub_key(("item_data",), video_info) or \
                        not robot.check_sub_key(("watch_id", "title"), video_info["item_data"]):
                    log.error(account_name + " 视频信息%s解析失败" % video_info)
                    tool.process_exit()

                # sm30043563
                video_id = str(video_info["item_data"]["watch_id"])

                # 过滤标题中不支持的字符
                video_title = robot.filter_text(video_info["item_data"]["title"])

                # 第一个视频，创建目录
                if need_make_video_dir:
                    if not tool.make_dir(video_path, 0):
                        log.error(account_name + " 创建图片下载目录 %s 失败" % video_path)
                        tool.process_exit()
                    need_make_video_dir = False

                # 获取视频下载地址
                video_url = get_video_url(video_id)
                log.step(account_name + " 开始下载第%s个视频 %s %s" % (video_count, video_id, video_url))
                print video_title
                print "%s %s" % (video_id, video_title)
                file_path = os.path.join(video_path, "%s %s.mp4" % (video_id, video_title))
                if tool.save_net_file(video_url, file_path):
                    log.step(account_name + " 第%s个视频下载成功" % video_count)
                    video_count += 1
                else:
                    log.error(account_name + " 第%s个视频 %s %s 下载失败" % (video_count, video_id, video_url))

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
            if first_video_id != "0":
                self.account_info[1] = first_video_id

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
    NicoNico().main()
