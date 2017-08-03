# -*- coding:UTF-8  -*-
"""
7gogo图片&视频爬虫
https://7gogo.jp/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import os
import threading
import time
import traceback

ACCOUNTS = []
INIT_TARGET_ID = "99999"
MESSAGE_COUNT_PER_PAGE = 30
TOTAL_IMAGE_COUNT = 0
TOTAL_VIDEO_COUNT = 0
IMAGE_TEMP_PATH = ""
IMAGE_DOWNLOAD_PATH = ""
VIDEO_TEMP_PATH = ""
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_DOWNLOAD_IMAGE = True
IS_DOWNLOAD_VIDEO = True


# 获取指定页数的所有媒体信息
def get_one_page_media(account_name, target_id):
    media_pagination_url = "https://api.7gogo.jp/web/v2/talks/%s/images?targetId=%s&limit=%s&direction=PREV" % (account_name, target_id, MESSAGE_COUNT_PER_PAGE)
    media_pagination_response = net.http_request(media_pagination_url, json_decode=True)
    extra_info = {
        "is_error": False,  # 是不是格式不符合
        "media_info_list": [],  # 页面解析出的所有媒体信息列表
    }
    if media_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if robot.check_sub_key(("data",), media_pagination_response.json_data):
            for media_info in media_pagination_response.json_data["data"]:
                extra_media_info = {
                    "blog_id": None,  # 页面解析出的日志id
                    "blog_body": None,  # 页面解析出的日志内容
                    "json_data": media_info,  # 原始数据
                }
                if robot.check_sub_key(("post",), media_info) and robot.check_sub_key(("body", "postId"), media_info["post"]):
                    # 获取日志id
                    blog_id = str(media_info["post"]["postId"])
                    if robot.is_integer(blog_id):
                        extra_media_info["blog_id"] = blog_id
                    # 获取日志内容
                    extra_media_info["blog_body"] = media_info["post"]["body"]
                extra_info["media_info_list"].append(extra_media_info)
        else:
            extra_info["is_error"] = True
    media_pagination_response.extra_info = extra_info
    return media_pagination_response


class NanaGoGo(robot.Robot):
    def __init__(self):
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global VIDEO_TEMP_PATH
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_DOWNLOAD_IMAGE
        global IS_DOWNLOAD_VIDEO

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_DOWNLOAD_VIDEO: True,
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        IMAGE_TEMP_PATH = self.image_temp_path
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        VIDEO_TEMP_PATH = self.video_temp_path
        VIDEO_DOWNLOAD_PATH = self.video_download_path
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
                if robot.is_process_end() == 0:
                    time.sleep(10)
                else:
                    break

            # 提前结束
            if robot.is_process_end() > 0:
                break

            # 开始下载
            thread = Download(account_list[account_name], self.thread_lock)
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
        self.finish_task()

        # 重新排序保存存档文件
        robot.rewrite_save_file(NEW_SAVE_DATA_PATH, self.save_data_path)

        log.step("全部下载完毕，耗时%s秒，共计图片%s张，视频%s个" % (self.get_run_time(), TOTAL_IMAGE_COUNT, TOTAL_VIDEO_COUNT))


class Download(threading.Thread):
    def __init__(self, account_info, thread_lock):
        threading.Thread.__init__(self)
        self.account_info = account_info
        self.thread_lock = thread_lock

    def run(self):
        global TOTAL_IMAGE_COUNT
        global TOTAL_VIDEO_COUNT

        account_name = self.account_info[0]

        try:
            log.step(account_name + " 开始")

            image_count = 1
            video_count = 1
            target_id = INIT_TARGET_ID
            is_over = False
            first_post_id = None
            image_path = os.path.join(IMAGE_TEMP_PATH, account_name)
            video_path = os.path.join(VIDEO_TEMP_PATH, account_name)
            while not is_over:
                log.step(account_name + " 开始解析target id %s后的一页视频" % target_id)

                # 获取一页媒体信息
                media_pagination_response = get_one_page_media(account_name, target_id)
                if media_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                    log.error(account_name + " target id %s的媒体信息访问失败，原因：%s" % (target_id, robot.get_http_request_failed_reason(media_pagination_response.status)))
                    tool.process_exit()

                if media_pagination_response.extra_info["is_error"]:
                    log.error(account_name + " target id %s的媒体信息解析失败" % target_id)
                    tool.process_exit()

                # 如果为空，表示已经取完了
                if len(media_pagination_response.extra_info["media_info_list"]) == 0:
                    break

                for media_info in media_pagination_response.extra_info["media_info_list"]:
                    if media_info["blog_id"] is None:
                        log.error(account_name + " 媒体信息%s的日志id解析失败" % media_info["json_data"])
                        tool.process_exit()

                    # 检查是否达到存档记录
                    if int(media_info["blog_id"]) <= int(self.account_info[3]):
                        is_over = True
                        break

                    # 新的存档记录
                    if first_post_id is None:
                        first_post_id = media_info["blog_id"]

                    # 设置target id，取下一页图片
                    target_id = media_info["blog_id"]

                    log.step(account_name + " 开始解析日志%s" % media_info["blog_id"])
                    for blog_body in media_info["blog_body"]:
                        if not robot.check_sub_key(("bodyType",), blog_body):
                            log.error(account_name + " 媒体信息%s的bodyType解析失败" % media_info["json_data"])
                            tool.process_exit()

                        # bodyType = 1: text, bodyType = 3: image, bodyType = 8: video
                        body_type = int(blog_body["bodyType"])
                        if body_type == 1:  # 文本
                            pass
                        elif body_type == 2:  # 表情
                            pass
                        elif body_type == 3:  # 图片
                            if IS_DOWNLOAD_IMAGE:
                                if not robot.check_sub_key(("image",), blog_body):
                                    log.error(account_name + " 第%s张图片解析失败%s" % (image_count, blog_body))
                                    continue

                                image_url = str(blog_body["image"])
                                log.step(account_name + " 开始下载第%s张图片 %s" % (image_count, image_url))

                                file_type = image_url.split(".")[-1]
                                image_file_path = os.path.join(image_path, "%04d.%s" % (image_count, file_type))
                                save_file_return = net.save_net_file(image_url, image_file_path)
                                if save_file_return["status"] == 1:
                                    log.step(account_name + " 第%s张图片下载成功" % image_count)
                                    image_count += 1
                                else:
                                    log.error(account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_count, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
                        elif body_type == 7:  # 转发
                            pass
                        elif body_type == 8:  # video
                            if IS_DOWNLOAD_VIDEO:
                                if not robot.check_sub_key(("movieUrlHq",), blog_body):
                                    log.error(account_name + " 第%s个视频解析失败%s" % (video_count, blog_body))
                                    continue

                                video_url = str(blog_body["movieUrlHq"])
                                log.step(account_name + " 开始下载第%s个视频 %s" % (video_count, video_url))

                                file_type = video_url.split(".")[-1]
                                video_file_path = os.path.join(video_path, "%04d.%s" % (video_count, file_type))
                                save_file_return = net.save_net_file(video_url, video_file_path)
                                if save_file_return["status"] == 1:
                                    log.step(account_name + " 第%s个视频下载成功" % video_count)
                                    video_count += 1
                                else:
                                    log.error(account_name + " 第%s个视频 %s 下载失败，原因：%s" % (video_count, video_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
                        else:
                            log.error(account_name + " 第%s张图片、第%s个视频，未知bodytype %s, %s" % (image_count, video_count, body_type, blog_body))
                            tool.process_exit()

            # 排序
            if image_count > 1:
                log.step(account_name + " 图片开始从下载目录移动到保存目录")
                destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
                if robot.sort_file(image_path, destination_path, int(self.account_info[1]), 4):
                    log.step(account_name + " 图片从下载目录移动到保存目录成功")
                else:
                    log.error(account_name + " 创建图片保存目录 %s 失败" % destination_path)
                    tool.process_exit()
            if video_count > 1:
                log.step(account_name + " 视频开始从下载目录移动到保存目录")
                destination_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)
                if robot.sort_file(video_path, destination_path, int(self.account_info[2]), 4):
                    log.step(account_name + " 视频从下载目录移动到保存目录成功")
                else:
                    log.error(account_name + " 创建视频保存目录 %s 失败" % destination_path)
                    tool.process_exit()

            # 新的存档记录
            if first_post_id is not None:
                self.account_info[1] = str(int(self.account_info[1]) + image_count - 1)
                self.account_info[2] = str(int(self.account_info[2]) + video_count - 1)
                self.account_info[3] = first_post_id

            # 保存最后的信息
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            self.thread_lock.acquire()
            TOTAL_IMAGE_COUNT += image_count - 1
            TOTAL_VIDEO_COUNT += video_count - 1
            ACCOUNTS.remove(account_name)
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
    NanaGoGo().main()
