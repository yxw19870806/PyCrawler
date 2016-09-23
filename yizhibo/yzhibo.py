# -*- coding:UTF-8  -*-
"""
微博图片&视频爬虫
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, robot, tool
import hashlib
import json
import os
import random
import re
import threading
import time
import traceback
import urllib2

ACCOUNTS = []
TOTAL_VIDEO_COUNT = 0
GET_VIDEO_COUNT = 0
VIDEO_TEMP_PATH = ""
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_SORT = True
IS_DOWNLOAD_VIDEO = True

threadLock = threading.Lock()


def trace(msg):
    threadLock.acquire()
    log.trace(msg)
    threadLock.release()


def print_error_msg(msg):
    threadLock.acquire()
    log.error(msg)
    threadLock.release()


def print_step_msg(msg):
    threadLock.acquire()
    log.step(msg)
    threadLock.release()


def get_video_id_list(account_id):
    video_list_url = "http://www.yizhibo.com/member/personel/user_works?memberid=%s" % account_id
    index_return_code, index_page = tool.http_request(video_list_url)[:2]
    if index_return_code == 1:
        return re.findall('<div class="scid" style="display:none;">([^<]*?)</div>', index_page)
    return None


def get_video_info(video_id):
    video_info_url = "http://api.xiaoka.tv/live/web/get_play_live?scid=%s" % video_id
    video_info_return_code, video_info_data = tool.http_request(video_info_url)[:2]
    if video_info_return_code == 1:
        try:
            video_info_data = json.loads(video_info_data)
        except ValueError:
            pass
        else:
            if robot.check_sub_key(("result", "data"), video_info_data) and int(video_info_data["result"]) == 1:
                if robot.check_sub_key(("createtime", "linkurl"), video_info_data["data"]):
                    return video_info_data
        print video_info_data
    return None


# 根据mindex.m3u8获取所有ts文件的下载地址
# http://alcdn.hls.xiaoka.tv/2016920/fb8/3b0/YJs4SLbXVC0msjWo/index.m3u8
def get_video_download_list(link_url):
    video_link_return_code, video_link_data = tool.http_request(link_url)[:2]
    if video_link_return_code == 1:
        ts_id_list = re.findall("([\d]*.ts)", video_link_data)
        prefix_url = link_url[:link_url.rfind("/") + 1]
        ts_file_list = []
        for ts_id in ts_id_list:
            ts_file_list.append(prefix_url + ts_id)
        return ts_file_list
    else:
        return None


# 将多个ts文件的地址保存为本地视频文件
def save_video(ts_file_list, file_path):
    file_handle = open(file_path, 'wb')
    for ts_file_url in ts_file_list:
        ts_file_return_code, ts_file_data = tool.http_request(ts_file_url)[:2]
        if ts_file_return_code == 1:
            file_handle.write(ts_file_data)
        else:
            return False
    file_handle.close()
    return True


class YiZhiBo(robot.Robot):
    def __init__(self, extra_config=None):
        global GET_VIDEO_COUNT
        global VIDEO_TEMP_PATH
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT
        global IS_DOWNLOAD_VIDEO

        robot.Robot.__init__(self, False, extra_config)

        # 设置全局变量，供子线程调用
        GET_VIDEO_COUNT = self.get_video_count
        VIDEO_TEMP_PATH = self.video_temp_path
        VIDEO_DOWNLOAD_PATH = self.video_download_path
        IS_SORT = self.is_sort
        IS_DOWNLOAD_VIDEO = self.is_download_video
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

        tool.print_msg("配置文件读取完成")

    def main(self):
        global ACCOUNTS

        if not self.is_download_video:
            print_error_msg("下载视频没有开启，请检查配置！")
            tool.process_exit()

        start_time = time.time()

        # 创建视频保存目录
        print_step_msg("创建视频根目录 %s" % VIDEO_DOWNLOAD_PATH)
        if not tool.make_dir(VIDEO_DOWNLOAD_PATH, 0):
            print_error_msg("创建视频根目录 %s 失败" % VIDEO_DOWNLOAD_PATH)
            tool.process_exit()

        # 寻找存档，如果没有结束进程
        account_list = {}
        if os.path.exists(self.save_data_path):
            # account_id  video_count last_video_time (account_name)
            account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0"])
            ACCOUNTS = account_list.keys()
        else:
            print_error_msg("存档文件 %s 不存在" % self.save_data_path)
            tool.process_exit()

        # 创建临时存档文件
        new_save_data_file = open(NEW_SAVE_DATA_PATH, "w")
        new_save_data_file.close()

        # 启用线程监控是否需要暂停其他下载线程
        process_control_thread = tool.ProcessControl()
        process_control_thread.setDaemon(True)
        process_control_thread.start()

        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for account_id in sorted(account_list.keys()):
            # 检查正在运行的线程数
            while threading.activeCount() >= self.thread_count + main_thread_count:
                if tool.is_process_end() == 0:
                    time.sleep(10)
                else:
                    break

            # 提前结束
            if tool.is_process_end() > 0:
                break

            # 开始下载
            thread = Download(account_list[account_id])
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
        account_list = robot.read_save_data(NEW_SAVE_DATA_PATH, 0, [])
        temp_list = [account_list[key] for key in sorted(account_list.keys())]
        tool.write_file(tool.list_to_string(temp_list), self.save_data_path, 2)
        os.remove(NEW_SAVE_DATA_PATH)

        duration_time = int(time.time() - start_time)
        print_step_msg("全部下载完毕，耗时%s秒，共计视频%s个" % (duration_time, TOTAL_VIDEO_COUNT))


class Download(threading.Thread):
    def __init__(self, account_info):
        threading.Thread.__init__(self)
        self.account_info = account_info

    def run(self):
        global TOTAL_VIDEO_COUNT

        account_id = self.account_info[0]
        if len(self.account_info) >= 3 and self.account_info[2]:
            account_name = self.account_info[2]
        else:
            account_name = self.account_info[0]

        try:
            print_step_msg(account_name + " 开始")

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if IS_SORT:
                video_path = os.path.join(VIDEO_TEMP_PATH, account_name)
            else:
                video_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)

            # 视频
            video_count = 1
            first_created_time = "0"
            need_make_video_dir = True
            if IS_DOWNLOAD_VIDEO:
                video_id_list = get_video_id_list(account_id)
                if video_id_list is not None:
                    for video_id in video_id_list:
                        # 获取视频的时间和下载地址
                        video_info = get_video_info(video_id)
                        if video_info is None:
                            print_error_msg(account_name + " 视频 %s 信息获取失败" % video_id)
                            break
                        # 检查是否已下载到前一次的图片
                        if int(video_info["data"]["createtime"]) <= int(self.account_info[1]):
                            break
                        if first_created_time == "0":
                            first_created_time = str(video_info["data"]["createtime"])
                        # 视频的真实下载地址列表
                        ts_file_list = get_video_download_list(str(video_info["data"]["linkurl"]))
                        if ts_file_list is None:
                            print_error_msg(account_name + " 视频下载地址列表 %s 获取失败" % video_info["data"]["linkurl"])
                            continue

                        # 第一个视频，创建目录
                        if need_make_video_dir:
                            if not tool.make_dir(video_path, 0):
                                print_error_msg(account_name + " 创建图片下载目录 %s 失败" % video_path)
                                tool.process_exit()
                            need_make_video_dir = False

                        video_file_path = os.path.join(video_path, "%04d.ts" % video_count)
                        print_step_msg(account_name + " 开始下载第%s个视频 %s" % (video_count, ts_file_list))
                        if save_video(ts_file_list, video_file_path):
                            print_step_msg(account_name + " 第%s个视频下载成功" % video_count)
                            video_count += 1
                        else:
                            print_error_msg(account_name + " 第%s个视频 %s 下载失败" % (video_count, ts_file_list))
                else:
                    print_error_msg(account_name + " 视频列表解析错误")

            image_count = 1

            print_step_msg(account_name + " 下载完毕，总共获得%s张图片和%s个视频" % (image_count - 1, video_count - 1))

            # 排序
            if IS_SORT:
                if video_count > 1:
                    destination_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)
                    if robot.sort_file(video_path, destination_path, int(self.account_info[3]), 4):
                        print_step_msg(account_name + " 视频从下载目录移动到保存目录成功")
                    else:
                        print_error_msg(account_name + " 创建视频保存目录 %s 失败" % destination_path)
                        tool.process_exit()

            if first_created_time != "0":
                self.account_info[1] = first_created_time
                self.account_info[2] = str(int(self.account_info[2]) + video_count - 1)

            # 保存最后的信息
            threadLock.acquire()
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            TOTAL_VIDEO_COUNT += video_count - 1
            ACCOUNTS.remove(account_id)
            threadLock.release()

            print_step_msg(account_name + " 完成")
        except SystemExit, se:
            if se.code == 0:
                print_step_msg(account_name + " 提前退出")
            else:
                print_error_msg(account_name + " 异常退出")
        except Exception, e:
            print_step_msg(account_name + " 未知异常")
            print_error_msg(str(e) + "\n" + str(traceback.format_exc()))


if __name__ == "__main__":
    YiZhiBo().main()
