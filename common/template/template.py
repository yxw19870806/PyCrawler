# -*- coding:UTF-8  -*-
"""
模板
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import json
import os
import re
import threading
import time
import traceback

ACCOUNTS = []
TOTAL_IMAGE_COUNT = 0
TOTAL_VIDEO_COUNT = 0
IMAGE_DOWNLOAD_PATH = ""
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_DOWNLOAD_IMAGE = True
IS_DOWNLOAD_VIDEO = True


# 获取一页日志
def get_one_page_blog(account_id, page_count):
    result = {
        "blog_id_list": [],  # 日志id
    }
    return result


# 获取指定日志
def get_blog_page(account_id, blog_id):
    result = {
        "image_url_list": [],  # 全部图片地址
        "video_url_list": [],  # 全部视频地址
    }
    return result


class Template(robot.Robot):
    def __init__(self):
        global IMAGE_DOWNLOAD_PATH
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_DOWNLOAD_IMAGE
        global IS_DOWNLOAD_VIDEO

        # todo 配置
        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_DOWNLOAD_VIDEO: True,
            robot.SYS_SET_PROXY: True,
            robot.SYS_NOT_CHECK_SAVE_DATA: True,
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        # todo 是否需要下载图片或视频
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        VIDEO_DOWNLOAD_PATH = self.video_download_path
        IS_DOWNLOAD_IMAGE = self.is_download_image
        IS_DOWNLOAD_VIDEO = self.is_download_video
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

    def main(self):
        global ACCOUNTS

        # todo 存档文件格式
        # 解析存档文件
        # account_id
        account_list = robot.read_save_data(self.save_data_path, 0, ["", ])
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

        # 重新排序保存存档文件
        robot.rewrite_save_file(NEW_SAVE_DATA_PATH, self.save_data_path)

        # todo 是否需要下载图片或视频
        log.step("全部下载完毕，耗时%s秒，共计图片%s张，视频%s个" % (self.get_run_time(), TOTAL_IMAGE_COUNT, TOTAL_VIDEO_COUNT))


class Download(threading.Thread):
    def __init__(self, account_info, thread_lock):
        threading.Thread.__init__(self)
        self.account_info = account_info
        self.thread_lock = thread_lock

    def run(self):
        global TOTAL_IMAGE_COUNT
        global TOTAL_VIDEO_COUNT

        account_id = self.account_info[0]
        # todo 是否有需要显示不同名字
        account_name = account_id
        total_image_count = 0
        total_video_count = 0
        temp_path_list = []

        try:
            log.step(account_name + " 开始")

            page_count = 1
            blog_id_list = []
            is_over = False
            # 获取全部还未下载过需要解析的日志
            while not is_over:
                log.step(account_name + " 开始解析第%s页日志" % page_count)

                # todo 一页日志解析规则
                # 获取指定时间后的一页日志
                try:
                    blog_pagination_response = get_one_page_blog(account_id, page_count)
                except robot.RobotException, e:
                    log.error(account_name + " 第%s页日志解析失败，原因：%s" % (page_count, e.message))
                    raise

                log.trace(account_name + " 第%s页解析的全部日志：%s" % (page_count, blog_pagination_response["blog_id_list"]))

                # 寻找这一页符合条件的媒体
                for blog_id in blog_pagination_response["blog_id_list"]:
                    # 检查是否达到存档记录
                    if int(blog_id) > int(self.account_info[3]):
                        blog_id_list.append(blog_id)
                    else:
                        is_over = True
                        break

            log.step(account_name + " 需要下载的全部日志解析完毕，共%s个" % len(blog_id_list))

            while len(blog_id_list) > 0:
                blog_id = blog_id_list.pop()
                log.step(account_name + " 开始解析日志%s" % blog_id)

                # todo 日志解析规则
                # 获取指定日志
                try:
                    blog_response = get_blog_page(account_id, blog_id)
                except robot.RobotException, e:
                    log.error(account_name + " 日志%s解析失败，原因：%s" % (blog_id, e.message))
                    raise

                # todo 图片下载逻辑
                # 图片下载
                image_index = self.account_info[1] + 1
                if IS_DOWNLOAD_IMAGE:
                    for image_url in blog_response["image_url_list"]:
                        log.step(account_name + " 开始下载第%s张图片 %s" % (image_index, image_url))

                        file_type = image_url.split(".")[-1]
                        image_file_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name, "%04d.%s" % (image_index, file_type))
                        save_file_return = net.save_net_file(image_url, image_file_path)
                        if save_file_return["status"] == 1:
                            # 设置临时目录
                            temp_path_list.append(image_file_path)
                            log.step(account_name + " 第%s张图片下载成功" % image_index)
                            image_index += 1
                        else:
                            log.error(account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_index, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

                # todo 视频下载逻辑
                # 视频下载
                video_index = self.account_info[2] + 1
                if IS_DOWNLOAD_VIDEO:
                    for video_url in blog_response["video_url_list"]:
                        log.step(account_name + " 开始下载第%s个视频 %s" % (video_index, video_url))

                        file_type = video_url.split(".")[-1]
                        video_file_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name, "%04d.%s" % (video_index, file_type))
                        save_file_return = net.save_net_file(video_url, video_file_path)
                        if save_file_return["status"] == 1:
                            # 设置临时目录
                            temp_path_list.append(video_file_path)
                            log.step(account_name + " 第%s个视频下载成功" % video_index)
                            video_index += 1
                        else:
                            log.error(account_name + " 第%s个视频 %s 下载失败，原因：%s" % (video_index, video_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

                # 媒体内图片和视频全部下载完毕
                temp_path_list = []  # 临时目录设置清除
                total_image_count += (image_index - 1) - int(self.account_info[1])  # 计数累加
                total_video_count += (video_index - 1) - int(self.account_info[2])  # 计数累加
                self.account_info[1] = str(image_index - 1)  # 设置存档记录
                self.account_info[2] = str(video_index - 1)  # 设置存档记录
                self.account_info[3] = ""  # 设置存档记录
        except SystemExit, se:
            if se.code == 0:
                log.step(account_name + " 提前退出")
            else:
                log.error(account_name + " 异常退出")
            # 如果临时目录变量不为空，表示某个日志正在下载中，需要把下载了部分的内容给清理掉
            if len(temp_path_list) > 0:
                for temp_path in temp_path_list:
                    path.delete_dir_or_file(temp_path)
        except Exception, e:
            log.error(account_name + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 保存最后的信息
        self.thread_lock.acquire()
        tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
        TOTAL_IMAGE_COUNT += total_image_count
        TOTAL_VIDEO_COUNT += total_video_count
        ACCOUNTS.remove(account_id)
        self.thread_lock.release()
        log.step(account_name + " 下载完毕，总共获得%s张图片和%s个视频" % (total_image_count, total_video_count))


if __name__ == "__main__":
    Template().main()
