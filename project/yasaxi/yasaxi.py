# -*- coding:UTF-8  -*-
"""
看了又看APP图片爬虫
http://share.yasaxi.com/share.html
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import yasaxiCommon
import os
import threading
import time
import traceback

ACCOUNTS = []
TOTAL_IMAGE_COUNT = 0
IMAGE_TEMP_PATH = ""
IMAGE_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""


# 获取指定页数的所有日志
def get_one_page_photo(account_id, cursor):
    photo_pagination_url = "https://api.yasaxi.com/statuses/user?userId=%s&cursor=%s&count=20" % (account_id, cursor)
    header_list = {
        "x-access-token": yasaxiCommon.ACCESS_TOKEN,
        "x-auth-token": yasaxiCommon.AUTH_TOKEN,
        "x-zhezhe-info": yasaxiCommon.ZHEZHE_INFO,
        "User-Agent": "User-Agent: Dalvik/1.6.0 (Linux; U; Android 4.4.2; Nexus 6 Build/KOT49H)",
    }
    extra_info = {
        "is_over": False,  # 是不是已经没有新的图片
        "is_error": False,  # 是不是格式不符合
        "next_page_cursor": None,  # 下一页图片的指针
        "status_list": [],  # 所有状态信息
    }
    photo_pagination_response = net.http_request(photo_pagination_url, header_list=header_list, is_random_ip=False, json_decode=True)
    if photo_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if (
            robot.check_sub_key(("meta",), photo_pagination_response.json_data) and
            robot.check_sub_key(("code",), photo_pagination_response.json_data["meta"]) and
            len(photo_pagination_response.json_data["meta"]["code"]) > 0
        ):
            if photo_pagination_response.json_data["meta"]["code"] == "NoMoreDataError":
                extra_info["is_over"] = True
            elif photo_pagination_response.json_data["meta"]["code"] == "TooManyRequests":
                time.sleep(30)
                return get_one_page_photo(account_id, cursor)
            else:
                extra_info["is_error"] = True
        elif robot.check_sub_key(("data", "next"), photo_pagination_response.json_data):
            for media_info in photo_pagination_response.json_data["data"]:
                media_extra_info = {
                    "id": None,  # 状态id
                    "image_url_list": [],  # 所有图片地址
                    "json_data": media_info,  # 原始数据
                }
                if robot.check_sub_key(("medias", "createAt", "statusId"), media_info):
                    is_error = False
                    # 获取图片地址
                    for media in media_info["medias"]:
                        # 带模糊效果的，XXXXX_b.webp
                        # https://s3-us-west-2.amazonaws.com/ysx.status.2/1080/baf196caa043a88ecf35a4652fa6017648aa5a02_b.webp?AWSAccessKeyId=AKIAJGLBMFWYTNLTZTOA&Expires=1498737886&Signature=%2F5Gmp5HRNXkGnlwJ2aulGfEqhh8%3D
                        # 原始图的，XXXXX.webp
                        # https://s3-us-west-2.amazonaws.com/ysx.status.2/1080/7ec8bccbbf0d618d67170f77054e3931220e3c14.webp?AWSAccessKeyId=AKIAJGLBMFWYTNLTZTOA&Expires=1498737886&Signature=9hvWk62TmAAPq67Rn577WU8NyYI%3D
                        if robot.check_sub_key(("origin", "downloadUrl", "thumb", "mediaType"), media) and robot.is_integer(media["mediaType"]):
                            if media["downloadUrl"]:
                                media_extra_info["image_url_list"].append(str(media["downloadUrl"]))
                            elif media["origin"]:
                                media_extra_info["image_url_list"].append(str(media["origin"]))
                            else:
                                # 视频，可能只有预览图
                                if int(media["mediaType"]) == 2:
                                    if media["thumb"]:
                                        media_extra_info["image_url_list"].append(str(media["thumb"]))
                                # 图片，不存在origin和downloadUrl，抛出异常
                                elif int(media["mediaType"]) == 1:
                                    is_error = True
                                    break
                                # 未知类型，抛出异常
                                else:
                                    is_error = True
                                    break
                        else:
                            is_error = True
                            break
                    # 获取状态id
                    if not is_error:
                        media_extra_info["id"] = str(media_info["statusId"])
                extra_info["status_list"].append(media_extra_info)
            if photo_pagination_response.json_data["next"] and robot.is_integer(photo_pagination_response.json_data["next"]):
                extra_info["next_page_cursor"] = int(photo_pagination_response.json_data["next"])
        else:
            extra_info["is_error"] = True
    photo_pagination_response.extra_info = extra_info
    return photo_pagination_response


class Yasaxi(robot.Robot):
    def __init__(self):
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_NOT_CHECK_SAVE_DATA: True,
        }
        robot.Robot.__init__(self, sys_config)

        # 服务器有请求数量限制，所以取消多线程
        self.thread_count = 1

        # 设置全局变量，供子线程调用
        IMAGE_TEMP_PATH = self.image_temp_path
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

    def main(self):
        global ACCOUNTS

        # 从文件中宏读取账号信息（访问token）
        if not yasaxiCommon.get_token_from_file():
            log.error("保存的账号信息读取失败")
            tool.process_exit()

        # 解析存档文件
        # account_id  status_id
        account_list = robot.read_save_data(self.save_data_path, 0, ["", ""])
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

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), TOTAL_IMAGE_COUNT))


class Download(threading.Thread):
    def __init__(self, account_info, thread_lock):
        threading.Thread.__init__(self)
        self.account_info = account_info
        self.thread_lock = thread_lock

    def run(self):
        global TOTAL_IMAGE_COUNT

        account_id = self.account_info[0]
        account_name = self.account_info[2]

        try:
            log.step(account_name + " 开始")

            image_count = 1
            cursor = 0
            is_over = False
            first_status_id = None
            image_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
            while not is_over:
                log.step(account_name + " 开始解析cursor '%s'的图片" % cursor)

                photo_pagination_response = get_one_page_photo(account_id, cursor)
                if photo_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                    log.error(account_name + " cursor '%s'的图片访问失败，原因：%s" % (cursor, robot.get_http_request_failed_reason(photo_pagination_response.status)))
                    tool.process_exit()

                if photo_pagination_response.extra_info["is_over"]:
                    break

                if photo_pagination_response.extra_info["is_error"]:
                    log.error(account_name + " cursor '%s'的图片信息%s解析失败" % (cursor, photo_pagination_response.json_data))
                    tool.process_exit()

                for status_info in photo_pagination_response.extra_info["status_list"]:
                    if status_info["id"] is None:
                        log.error(account_name + " 状态%s解析失败" % status_info["json_data"])
                        tool.process_exit()

                    # 检查是否达到存档记录
                    if status_info["id"] == self.account_info[1]:
                        is_over = True
                        break

                    # 新的存档记录
                    if first_status_id is None:
                        first_status_id = status_info["id"]

                    log.step(account_name + " 开始解析状态%s的图片" % status_info["id"])

                    for image_url in status_info["image_url_list"]:
                        file_name_and_type = image_url.split("?")[0].split("/")[-1]
                        resolution = image_url.split("?")[0].split("/")[-2]
                        file_name = file_name_and_type.split(".")[0]
                        file_type = file_name_and_type.split(".")[1]
                        if file_name[-2:] != "_b" and resolution == "1080":
                            image_file_path = os.path.join(image_path, "origin/%s.%s" % (file_name, file_type))
                        else:
                            image_file_path = os.path.join(image_path, "other/%s.%s" % (file_name, file_type))
                        log.step(account_name + " 开始下载第%s张图片 %s" % (image_count, image_url))
                        save_file_return = net.save_net_file(image_url, image_file_path)
                        if save_file_return["status"] == 1:
                            log.step(account_name + " 第%s张图片下载成功" % image_count)
                            image_count += 1
                        else:
                            log.error(account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_count, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

                if not is_over:
                    if photo_pagination_response.extra_info["next_page_cursor"]:
                        cursor = photo_pagination_response.extra_info["next_page_cursor"]
                    else:
                        is_over = True

            log.step(account_name + " 下载完毕，总共获得%s张图片" % (image_count - 1))

            # 新的存档记录
            if first_status_id is not None:
                self.account_info[1] = first_status_id

            # 保存最后的信息
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            self.thread_lock.acquire()
            TOTAL_IMAGE_COUNT += image_count - 1
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
    Yasaxi().main()
