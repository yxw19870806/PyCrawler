# -*- coding:UTF-8  -*-
"""
一直播图片&视频爬虫
http://www.yizhibo.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, robot, tool
import json
import os
import re
import threading
import time
import traceback

ACCOUNTS = []
TOTAL_IMAGE_COUNT = 0
TOTAL_VIDEO_COUNT = 0
GET_IMAGE_COUNT = 0
GET_VIDEO_COUNT = 0
IMAGE_TEMP_PATH = ""
IMAGE_DOWNLOAD_PATH = ""
VIDEO_TEMP_PATH = ""
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_SORT = True
IS_DOWNLOAD_IMAGE = True
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


# 获取指定账号的全部视频ID列表
def get_video_id_list(account_id):
    video_list_url = "http://www.yizhibo.com/member/personel/user_works?memberid=%s" % account_id
    index_return_code, index_page = tool.http_request(video_list_url)[:2]
    if index_return_code == 1:
        return re.findall('<div class="scid" style="display:none;">([^<]*?)</div>', index_page)
    return None


# 获取指定账号的全部图片地址列表
def get_image_url_list(account_id):
    video_list_url = "http://www.yizhibo.com/member/personel/user_photos?memberid=%s" % account_id
    index_return_code, index_page = tool.http_request(video_list_url)[:2]
    if index_return_code == 1:
        return re.findall('<img src="([^"]*)" alt="" class="index_img_main">', index_page)
    return None


# 根据video id获取指定视频的详细信息（上传时间、视频列表的下载地址等）
# video_id -> qxonW5XeZru03nUB
def get_video_info(video_id):
    # http://api.xiaoka.tv/live/web/get_play_live?scid=qxonW5XeZru03nUB
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
    return None


# 根据视频对应index.m3u8地址获取所有ts文件的下载地址
# link_url -> http://alcdn.hls.xiaoka.tv/2016103/a32/11d/qxonW5XeZru03nUB/index.m3u8
def get_ts_url_list(link_url):
    video_link_return_code, video_link_data = tool.http_request(link_url)[:2]
    if video_link_return_code == 1:
        ts_id_list = re.findall("([\S]*.ts)", video_link_data)
        prefix_url = link_url[:link_url.rfind("/") + 1]
        ts_file_list = []
        for ts_id in ts_id_list:
            ts_file_list.append(prefix_url + ts_id)
        return ts_file_list
    else:
        return None


# 将图片的二进制数据保存为本地文件
def save_image(image_byte, image_path):
    image_path = tool.change_path_encoding(image_path)
    image_file = open(image_path, "wb")
    image_file.write(image_byte)
    image_file.close()


# 将多个ts文件的地址保存为本地视频文件
def save_video(ts_file_list, file_path):
    file_path = tool.change_path_encoding(file_path)
    file_handle = open(file_path, "wb")
    for ts_file_url in ts_file_list:
        ts_file_return_code, ts_file_data = tool.http_request(ts_file_url)[:2]
        if ts_file_return_code == 1:
            file_handle.write(ts_file_data)
        else:
            return False
    file_handle.close()
    return True


class YiZhiBo(robot.Robot):
    def __init__(self):
        global GET_IMAGE_COUNT
        global GET_VIDEO_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global VIDEO_TEMP_PATH
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT
        global IS_DOWNLOAD_IMAGE
        global IS_DOWNLOAD_VIDEO

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_DOWNLOAD_VIDEO: True,
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        GET_IMAGE_COUNT = self.get_image_count
        GET_VIDEO_COUNT = self.get_video_count
        IMAGE_TEMP_PATH = self.image_temp_path
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        VIDEO_TEMP_PATH = self.video_temp_path
        VIDEO_DOWNLOAD_PATH = self.video_download_path
        IS_SORT = self.is_sort
        IS_DOWNLOAD_IMAGE = self.is_download_image
        IS_DOWNLOAD_VIDEO = self.is_download_video
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

    def main(self):
        global ACCOUNTS

        # 解析存档文件
        # account_id  video_count  last_video_time  image_count  last_image_time(account_name)
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0", "0", "0"])
        ACCOUNTS = account_list.keys()

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
        robot.rewrite_save_file(NEW_SAVE_DATA_PATH, self.save_data_path)

        print_step_msg("全部下载完毕，耗时%s秒，共计图片%s张，视频%s个" % (self.get_run_time(), TOTAL_IMAGE_COUNT, TOTAL_VIDEO_COUNT))


class Download(threading.Thread):
    def __init__(self, account_info):
        threading.Thread.__init__(self)
        self.account_info = account_info

    def run(self):
        global TOTAL_IMAGE_COUNT
        global TOTAL_VIDEO_COUNT

        account_id = self.account_info[0]
        if len(self.account_info) >= 6 and self.account_info[5]:
            account_name = self.account_info[5]
        else:
            account_name = self.account_info[0]

        try:
            print_step_msg(account_name + " 开始")

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if IS_SORT:
                image_path = os.path.join(IMAGE_TEMP_PATH, account_name)
                video_path = os.path.join(VIDEO_TEMP_PATH, account_name)
            else:
                image_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
                video_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)

            image_count = 1
            first_image_time = "0"
            need_make_image_dir = True
            while IS_DOWNLOAD_IMAGE:
                # 获取全部图片地址列表
                image_url_list = get_image_url_list(account_id)
                if image_url_list is None:
                    print_error_msg(account_name + " 图片列表解析错误")
                    break

                for image_url in list(image_url_list):
                    # 不使用缩略图
                    image_url = image_url.split("@")[0]
                    image_return_code, image_byte, image_response = tool.http_request(image_url)
                    if image_return_code != 1:
                        print_step_msg(account_name + " 第%s张图片下载失败" % image_count)
                        continue

                    # 获取图片的上传时间（字符串）
                    response_last_modified_time = tool.get_response_info(image_response.info(), "Last-Modified")
                    # 字符串转换为时间戳
                    image_created_time = tool.response_time_to_timestamp(response_last_modified_time)

                    # 检查是否已下载到前一次的图片
                    if int(image_created_time) <= int(self.account_info[4]):
                        break

                    # 将第一张图片的上传时间做为新的存档记录
                    if first_image_time == "0":
                        first_image_time = str(image_created_time)

                    print_step_msg(account_name + " 开始下载第%s张图片 %s" % (image_count, image_url))

                    # 第一张图片，创建目录
                    if need_make_image_dir:
                        if not tool.make_dir(image_path, 0):
                            print_error_msg(account_name + " 创建图片下载目录 %s 失败" % image_path)
                            tool.process_exit()
                        need_make_image_dir = False

                    file_type = image_url.split(".")[-1].split(":")[0]
                    image_file_path = os.path.join(image_path, "%04d.%s" % (image_count, file_type))
                    save_image(image_byte, image_file_path)
                    print_step_msg(account_name + " 第%s张图片下载成功" % image_count)
                    image_count += 1

                    # 达到配置文件中的下载数量，结束
                    if 0 < GET_IMAGE_COUNT < image_count:
                        break
                break

            # 视频
            video_count = 1
            first_video_time = "0"
            need_make_video_dir = True
            while IS_DOWNLOAD_VIDEO:
                # 获取全部视频ID列表
                video_id_list = get_video_id_list(account_id)
                if video_id_list is None:
                    print_error_msg(account_name + " 视频列表解析错误")
                    break

                for video_id in list(video_id_list):
                    # 获取视频的时间和下载地址
                    video_info = get_video_info(video_id)
                    if video_info is None:
                        print_error_msg(account_name + " 第%s个视频 %s 信息获取失败" % (video_count, video_id))
                        continue

                    # 检查是否已下载到前一次的视频
                    if int(video_info["data"]["createtime"]) <= int(self.account_info[2]):
                        break

                    # 将第一个视频的上传时间做为新的存档记录
                    if first_video_time == "0":
                        first_video_time = str(video_info["data"]["createtime"])

                    # m3u8文件的地址
                    link_url = str(video_info["data"]["linkurl"])
                    # 视频的真实下载地址列表
                    ts_url_list = get_ts_url_list(link_url)
                    if ts_url_list is None:
                        print_error_msg(account_name + " 第%s个视频下载地址列表 %s 获取失败" % (video_count, link_url))
                        continue

                    print_step_msg(account_name + " 开始下载第%s个视频 %s" % (video_count, ts_url_list))

                    # 第一个视频，创建目录
                    if need_make_video_dir:
                        if not tool.make_dir(video_path, 0):
                            print_error_msg(account_name + " 创建图片下载目录 %s 失败" % video_path)
                            tool.process_exit()
                        need_make_video_dir = False

                    video_file_path = os.path.join(video_path, "%04d.ts" % video_count)
                    if save_video(ts_url_list, video_file_path):
                        print_step_msg(account_name + " 第%s个视频下载成功" % video_count)
                        video_count += 1
                    else:
                        print_error_msg(account_name + " 第%s个视频 %s 下载失败" % (video_count, ts_url_list))

                    # 达到配置文件中的下载数量，结束
                    if 0 < GET_VIDEO_COUNT < video_count:
                        break
                break

            print_step_msg(account_name + " 下载完毕，总共获得%s张图片和%s个视频" % (image_count - 1, video_count - 1))

            # 排序
            if IS_SORT:
                if image_count > 1:
                    destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
                    if robot.sort_file(image_path, destination_path, int(self.account_info[3]), 4):
                        print_step_msg(account_name + " 图片从下载目录移动到保存目录成功")
                    else:
                        print_error_msg(account_name + " 创建图片保存目录 %s 失败" % destination_path)
                        tool.process_exit()
                if video_count > 1:
                    destination_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)
                    if robot.sort_file(video_path, destination_path, int(self.account_info[1]), 4):
                        print_step_msg(account_name + " 视频从下载目录移动到保存目录成功")
                    else:
                        print_error_msg(account_name + " 创建视频保存目录 %s 失败" % destination_path)
                        tool.process_exit()

            if first_image_time != "0":
                self.account_info[3] = str(int(self.account_info[3]) + image_count - 1)
                self.account_info[4] = first_image_time

            if first_video_time != "0":
                self.account_info[1] = str(int(self.account_info[1]) + video_count - 1)
                self.account_info[2] = first_video_time

            # 保存最后的信息
            threadLock.acquire()
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            TOTAL_IMAGE_COUNT += image_count - 1
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
            print_error_msg(account_name + " 未知异常")
            print_error_msg(str(e) + "\n" + str(traceback.format_exc()))


if __name__ == "__main__":
    YiZhiBo().main()
