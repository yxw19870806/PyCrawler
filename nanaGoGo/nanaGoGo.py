# -*- coding:utf-8  -*-
"""
7gogo图片&视频爬虫
https://7gogo.jp/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, robot, tool
import json
import os
import threading
import time
import traceback

ACCOUNTS = []
INIT_TARGET_ID = "99999"
MESSAGE_COUNT_PER_PAGE = 30
TOTAL_IMAGE_COUNT = 0
TOTAL_VIDEO_COUNT = 0
GET_IMAGE_COUNT = 0
IMAGE_TEMP_PATH = ""
IMAGE_DOWNLOAD_PATH = ""
VIDEO_TEMP_PATH = ""
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_SORT = True
IS_DOWNLOAD_IMAGE = True
IS_DOWNLOAD_VIDEO = True

threadLock = threading.Lock()


def print_error_msg(msg):
    threadLock.acquire()
    log.error(msg)
    threadLock.release()


def print_step_msg(msg):
    threadLock.acquire()
    log.step(msg)
    threadLock.release()


def trace(msg):
    threadLock.acquire()
    log.trace(msg)
    threadLock.release()


# 获取一页日志信息
def get_message_page_data(account_name, target_id):
    image_page_url = "https://api.7gogo.jp/web/v2/talks/%s/images" % account_name
    image_page_url += "?targetId=%s&limit=%s&direction=PREV" % (target_id, MESSAGE_COUNT_PER_PAGE)
    image_page_return_code, image_page_data = tool.http_request(image_page_url)[:2]
    if image_page_return_code == 1:
        try:
            image_page_data = json.loads(image_page_data)
        except ValueError:
            pass
        else:
            if robot.check_sub_key(("data",), image_page_data):
                return image_page_data["data"]
    return None


class NanaGoGo(robot.Robot):
    def __init__(self):
        global GET_IMAGE_COUNT
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
        # account_name  image_count  video_count  last_post_id
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0", "0"])
        ACCOUNTS = account_list.keys()

        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for account_name in sorted(account_list.keys()):
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
            thread = Download(account_list[account_name])
            thread.start()

            time.sleep(1)

        # 检查除主线程外的其他所有线程是不是全部结束了
        while threading.activeCount() > main_thread_count:
            time.sleep(10)

        # 未完成的数据保存
        if len(ACCOUNTS) > 0:
            new_save_data_file = open(NEW_SAVE_DATA_PATH, "a")
            for account_name in ACCOUNTS:
                new_save_data_file.write("\t".join(account_list[account_name]) + "\n")
            new_save_data_file.close()

        # 删除临时文件夹
        tool.remove_dir(IMAGE_TEMP_PATH)
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
            video_count = 1
            target_id = INIT_TARGET_ID
            first_post_id = "0"
            is_over = False
            need_make_image_dir = True
            need_make_video_dir = True

            while not is_over:
                # 获取一页日志信息
                message_page_data = get_message_page_data(account_name, target_id)
                if message_page_data is None:
                    print_error_msg(account_name + " 媒体列表解析异常")
                    tool.process_exit()
                # 没有了
                if len(message_page_data) == 0:
                    break

                for message_info in message_page_data:
                    if not robot.check_sub_key(("post",), message_info):
                        print_error_msg(account_name + " 媒体信息解析异常 %s" % message_info)
                        continue
                    if not robot.check_sub_key(("body", "postId"), message_info["post"]):
                        print_error_msg(account_name + " 媒体信息解析异常 %s" % message_info)
                        continue

                    target_id = message_info["post"]["postId"]
                    # 检查是否已下载到前一次的记录
                    if int(target_id) <= int(self.account_info[3]):
                        is_over = True
                        break

                    # 将第一个媒体的postId做为新的存档记录
                    if first_post_id == "0":
                        first_post_id = str(target_id)

                    for media_info in message_info["post"]["body"]:
                        if not robot.check_sub_key(("bodyType",), media_info):
                            print_error_msg(account_name + " 媒体列表bodyType解析异常")
                            continue

                        # bodyType = 1: text, bodyType = 3: image, bodyType = 8: video
                        body_type = int(media_info["bodyType"])
                        if body_type == 1:  # 文本
                            pass
                        elif body_type == 2:  # 表情
                            pass
                        elif body_type == 3:  # 图片
                            if IS_DOWNLOAD_IMAGE:
                                if not robot.check_sub_key(("image",), media_info):
                                    print_error_msg(account_name + " 第%s张图片解析异常%s" % (image_count, media_info))
                                    continue

                                image_url = str(media_info["image"])
                                print_step_msg(account_name + " 开始下载第%s张图片 %s" % (image_count, image_url))

                                # 第一张图片，创建目录
                                if need_make_image_dir:
                                    if not tool.make_dir(image_path, 0):
                                        print_error_msg(account_name + " 创建图片下载目录 %s 失败" % image_path)
                                        tool.process_exit()
                                    need_make_image_dir = False

                                file_type = image_url.split(".")[-1]
                                image_file_path = os.path.join(image_path, "%04d.%s" % (image_count, file_type))
                                if tool.save_net_file(image_url, image_file_path):
                                    print_step_msg(account_name + " 第%s张图片下载成功" % image_count)
                                    image_count += 1
                                else:
                                    print_error_msg(account_name + " 第%s张图片 %s 下载失败" % (image_count, image_url))
                        elif body_type == 8:  # video
                            if IS_DOWNLOAD_VIDEO:
                                if not robot.check_sub_key(("movieUrlHq",), media_info):
                                    print_error_msg(account_name + " 第%s个视频解析异常%s" % (video_count, media_info))
                                    continue

                                video_url = str(media_info["movieUrlHq"])
                                print_step_msg(account_name + " 开始下载第%s个视频 %s" % (video_count, video_url))

                                # 第一个视频，创建目录
                                if need_make_video_dir:
                                    if not tool.make_dir(video_path, 0):
                                        print_error_msg(account_name + " 创建视频下载目录 %s 失败" % video_path)
                                        tool.process_exit()
                                    need_make_video_dir = False

                                file_type = video_url.split(".")[-1]
                                video_file_path = os.path.join(video_path, "%04d.%s" % (video_count, file_type))
                                if tool.save_net_file(video_url, video_file_path):
                                    print_step_msg(account_name + " 第%s个视频下载成功" % video_count)
                                    video_count += 1
                                else:
                                    print_error_msg(account_name + " 第%s个视频 %s 下载失败" % (video_count, video_url))
                        elif body_type == 7:  # 转发
                            pass
                        else:
                            print_error_msg(account_name + " 第%s张图片、第%s个视频，未知bodytype %s, %s" % (image_count, video_count, body_type, media_info))

            # 排序
            if IS_SORT:
                if image_count > 1:
                    destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
                    if robot.sort_file(image_path, destination_path, int(self.account_info[1]), 4):
                        print_step_msg(account_name + " 图片从下载目录移动到保存目录成功")
                    else:
                        print_error_msg(account_name + " 创建图片保存目录 %s 失败" % destination_path)
                        tool.process_exit()
                if video_count > 1:
                    destination_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)
                    if robot.sort_file(video_path, destination_path, int(self.account_info[2]), 4):
                        print_step_msg(account_name + " 视频从下载目录移动到保存目录成功")
                    else:
                        print_error_msg(account_name + " 创建视频保存目录 %s 失败" % destination_path)
                        tool.process_exit()

            # 新的存档记录
            if first_post_id != "0":
                self.account_info[1] = str(int(self.account_info[1]) + image_count - 1)
                self.account_info[2] = str(int(self.account_info[2]) + video_count - 1)
                self.account_info[3] = first_post_id

            # 保存最后的信息
            threadLock.acquire()
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            TOTAL_IMAGE_COUNT += image_count - 1
            TOTAL_VIDEO_COUNT += video_count - 1
            ACCOUNTS.remove(account_name)
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
    NanaGoGo().main()
