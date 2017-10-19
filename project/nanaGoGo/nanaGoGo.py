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
IMAGE_DOWNLOAD_PATH = ""
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_DOWNLOAD_IMAGE = True
IS_DOWNLOAD_VIDEO = True


# 获取指定页数的全部媒体信息
def get_one_page_media(account_name, target_id):
    media_pagination_url = "https://api.7gogo.jp/web/v2/talks/%s/images?targetId=%s&limit=%s&direction=PREV" % (account_name, target_id, MESSAGE_COUNT_PER_PAGE)
    media_pagination_response = net.http_request(media_pagination_url, json_decode=True)
    result = {
        "media_info_list": [],  # 全部媒体信息
    }
    if media_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if not robot.check_sub_key(("data",), media_pagination_response.json_data):
            raise robot.RobotException("返回信息'data'字段不存在\n%s" % media_pagination_response.json_data)
        if not isinstance(media_pagination_response.json_data["data"], list):
            raise robot.RobotException("返回信息'data'字段类型不正确\n%s" % media_pagination_response.json_data)
        for media_info in media_pagination_response.json_data["data"]:
            result_media_info = {
                "blog_id": None,  # 日志id
                "image_url_list": [],  # 全部图片地址
                "video_url_list": [],  # 全部视频地址
            }
            if not robot.check_sub_key(("post",), media_info):
                raise robot.RobotException("媒体信息'post'字段不存在\n%s" % media_info)
            # 获取日志id
            if not robot.check_sub_key(("postId",), media_info["post"]):
                raise robot.RobotException("媒体信息'postId'字段不存在\n%s" % media_info)
            if not robot.is_integer(media_info["post"]["postId"]):
                raise robot.RobotException("媒体信息'postId'类型不正确n%s" % media_info)
            result_media_info["blog_id"] = str(media_info["post"]["postId"])
            # 获取日志内容
            if not robot.check_sub_key(("body",), media_info["post"]):
                raise robot.RobotException("媒体信息'body'字段不存在\n%s" % media_info)
            for blog_body in media_info["post"]["body"]:
                if not robot.check_sub_key(("bodyType",), blog_body):
                    raise robot.RobotException("媒体信息'bodyType'字段不存在\n%s" % blog_body)
                if not robot.is_integer(blog_body["bodyType"]):
                    raise robot.RobotException("媒体信息'bodyType'字段类型不正确\n%s" % blog_body)
                # bodyType = 1: text, bodyType = 3: image, bodyType = 8: video
                body_type = int(blog_body["bodyType"])
                if body_type == 1:  # 文本
                    continue
                elif body_type == 2:  # 表情
                    continue
                elif body_type == 3:  # 图片
                    if not robot.check_sub_key(("image",), blog_body):
                        raise robot.RobotException("媒体信息'image'字段不存在\n%s" % blog_body)
                    result_media_info["image_url_list"].append(str(blog_body["image"]))
                elif body_type == 7:  # 转发
                    continue
                elif body_type == 8:  # video
                    if not robot.check_sub_key(("movieUrlHq",), blog_body):
                        raise robot.RobotException("媒体信息'movieUrlHq'字段不存在\n%s" % blog_body)
                    result_media_info["video_url_list"].append(str(blog_body["movieUrlHq"]))
                else:
                    raise robot.RobotException("媒体信息'bodyType'字段取值不正确\n%s" % blog_body)
            result["media_info_list"].append(result_media_info)
    elif target_id == INIT_TARGET_ID and media_pagination_response.status == 400:
        raise robot.RobotException("talk不存在")
    else:
        raise robot.RobotException(robot.get_http_request_failed_reason(media_pagination_response.status))
    return result


class NanaGoGo(robot.Robot):
    def __init__(self):
        global IMAGE_DOWNLOAD_PATH
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
        IMAGE_DOWNLOAD_PATH = self.image_download_path
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
        total_image_count = 0
        total_video_count = 0
        temp_path_list = []

        try:
            log.step(account_name + " 开始")

            target_id = INIT_TARGET_ID
            media_info_list = []
            is_over = False
            # 获取全部还未下载过需要解析的日志
            while not is_over:
                log.step(account_name + " 开始解析target id %s后的一页媒体" % target_id)

                # 获取一页媒体信息
                try:
                    media_pagination_response = get_one_page_media(account_name, target_id)
                except robot.RobotException, e:
                    log.error(account_name + " target id %s的一页媒体信息解析失败，原因：%s" % (target_id, e.message))
                    raise

                # 如果为空，表示已经取完了
                if len(media_pagination_response["media_info_list"]) == 0:
                    break

                log.trace(account_name + " target id %s解析的全部媒体：%s" % (target_id, media_pagination_response["media_info_list"]))

                # 寻找这一页符合条件的日志
                for media_info in media_pagination_response["media_info_list"]:
                    # 检查是否达到存档记录
                    if int(media_info["blog_id"]) > int(self.account_info[3]):
                        media_info_list.append(media_info)
                        # 设置下一页指针
                        target_id = media_info["blog_id"]
                    else:
                        is_over = True
                        break

            log.step(account_name + " 需要下载的全部媒体解析完毕，共%s个" % len(media_info_list))

            # 从最早的日志开始下载
            while len(media_info_list) > 0:
                media_info = media_info_list.pop()
                log.step(account_name + " 开始解析日%s" % media_info["blog_id"])

                # 图片下载
                image_index = int(self.account_info[1]) + 1
                if IS_DOWNLOAD_IMAGE:
                    for image_url in media_info["image_url_list"]:
                        log.step(account_name + " 开始下载第%s张图片 %s" % (image_index, image_url))

                        file_type = image_url.split(".")[-1]
                        image_file_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name, "%04d.%s" % (image_index, file_type))
                        save_file_return = net.save_net_file(image_url, image_file_path)
                        if save_file_return["status"] == 1:
                            temp_path_list.append(image_file_path)
                            log.step(account_name + " 第%s张图片下载成功" % image_index)
                            image_index += 1
                        else:
                            log.error(account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_index, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

                # 视频下载
                video_index = int(self.account_info[2]) + 1
                if IS_DOWNLOAD_VIDEO:
                    for video_url in media_info["video_url_list"]:
                        log.step(account_name + " 开始下载第%s个视频 %s" % (video_index, video_url))

                        file_type = video_url.split(".")[-1]
                        video_file_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name, "%04d.%s" % (video_index, file_type))
                        save_file_return = net.save_net_file(video_url, video_file_path)
                        if save_file_return["status"] == 1:
                            temp_path_list.append(video_file_path)
                            log.step(account_name + " 第%s个视频下载成功" % video_index)
                            video_index += 1
                        else:
                            log.error(account_name + " 第%s个视频 %s 下载失败，原因：%s" % (video_index, video_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

                # 日志内图片和视频全部下载完毕
                temp_path_list = []  # 临时目录设置清除
                total_image_count += (image_index - 1) - int(self.account_info[1])  # 计数累加
                total_video_count += (video_index - 1) - int(self.account_info[2])  # 计数累加
                self.account_info[1] = str(image_index - 1)  # 设置存档记录
                self.account_info[2] = str(video_index - 1)  # 设置存档记录
                self.account_info[3] = str(media_info["blog_id"])
        except SystemExit, se:
            if se.code == 0:
                log.step(account_name + " 提前退出")
            else:
                log.error(account_name + " 异常退出")
            # 如果临时目录变量不为空，表示某个媒体正在下载中，需要把下载了部分的内容给清理掉
            if len(temp_path_list) > 0:
                for temp_path in temp_path_list:
                    tool.delete_dir_or_file(temp_path)
        except Exception, e:
            log.error(account_name + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 保存最后的信息
        self.thread_lock.acquire()
        tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
        TOTAL_IMAGE_COUNT += total_image_count
        TOTAL_VIDEO_COUNT += total_video_count
        ACCOUNTS.remove(account_name)
        self.thread_lock.release()
        log.step(account_name + " 下载完毕，总共获得%s张图片，%s个视频" % (total_image_count, total_video_count))


if __name__ == "__main__":
    NanaGoGo().main()
