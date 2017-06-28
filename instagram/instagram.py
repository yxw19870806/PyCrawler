# -*- coding:utf-8  -*-
"""
Instagram图片&视频爬虫
https://www.instagram.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import json
import os
import threading
import time
import traceback

ACCOUNTS = []
IMAGE_COUNT_PER_PAGE = 12
QUERY_ID = "17859156310193001"
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


# 根据账号名字获得账号id（字母账号->数字账号)
def get_index_page(account_name):
    index_page_url = "https://www.instagram.com/%s" % account_name
    index_page_response = net.http_request(index_page_url)
    extra_info = {
        "account_id": None,  # 页面解析出的account id
    }
    if index_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        account_id = tool.find_sub_string(index_page_response.data, '"profilePage_', '"')
        if account_id and robot.is_integer(account_id):
            extra_info["account_id"] = account_id
    index_page_response.extra_info = extra_info
    return index_page_response


# 获取指定页数的所有媒体
# account_id -> 490060609
def get_one_page_media(account_id, cursor):
    if cursor:
        query_page_url = "https://www.instagram.com/graphql/query/?query_id=%s&id=%s&first=%s&after=%s" % (QUERY_ID, account_id, IMAGE_COUNT_PER_PAGE, cursor)
    else:
        query_page_url = "https://www.instagram.com/graphql/query/?query_id=%s&id=%s&first=%s" % (QUERY_ID, account_id, IMAGE_COUNT_PER_PAGE)
    while True:
        media_page_response = net.http_request(query_page_url, json_decode=True)
        extra_info = {
            "is_error": False,  # 是不是格式不符合
            "media_info_list": [],  # 页面解析出的媒体信息列表
            "next_page_cursor": None,  # 页面解析出的下一页媒体信息的指针
        }
        # Too Many Requests
        if media_page_response.status == 429:
            time.sleep(30)
            continue
        elif media_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
            if (
                robot.check_sub_key(("status", "data"), media_page_response.json_data) and
                robot.check_sub_key(("user",), media_page_response.json_data["data"]) and
                robot.check_sub_key(("edge_owner_to_timeline_media",), media_page_response.json_data["data"]["user"]) and
                robot.check_sub_key(("page_info", "edges"), media_page_response.json_data["data"]["user"]["edge_owner_to_timeline_media"]) and
                robot.check_sub_key(("end_cursor", "has_next_page"), media_page_response.json_data["data"]["user"]["edge_owner_to_timeline_media"]["page_info"])
            ):
                if len(media_page_response.json_data["data"]["user"]["edge_owner_to_timeline_media"]["edges"]) > 0:
                    media_node = media_page_response.json_data["data"]["user"]["edge_owner_to_timeline_media"]
                    for media_info in media_node["edges"]:
                        media_extra_info = {
                            "image_url": None,  # 页面解析出的图片下载地址
                            "is_image_group": False,  # 是不是图片组
                            "is_video": False,  # 是不是视频
                            "page_id": None,  # 页面解析出的媒体详情界面id
                            "time": None,  # 页面解析出的媒体上传时间
                            "json_data": media_info,  # 原始数据
                        }
                        if (
                            robot.check_sub_key(("node",), media_info) and
                            robot.check_sub_key(("display_url", "taken_at_timestamp", "__typename", "shortcode"), media_info["node"])
                        ):
                            # GraphImage 单张图片、GraphSidecar 多张图片、GraphVideo 视频
                            if media_info["node"]["__typename"] not in ["GraphImage", "GraphSidecar", "GraphVideo"]:
                                extra_info["is_error"] = True
                                break
                            # 获取图片下载地址
                            media_extra_info["image_url"] = str(media_info["node"]["display_url"])
                            # 是不是图片组
                            media_extra_info["is_image_group"] = media_info["node"]["__typename"] == "GraphSidecar"
                            # 检测是否有视频
                            media_extra_info["is_video"] = media_info["node"]["__typename"] == "GraphVideo"
                            # 获取图片上传时间
                            media_extra_info["time"] = str(int(media_info["node"]["taken_at_timestamp"]))
                            # 获取媒体id
                            media_extra_info["page_id"] = str(media_info["node"]["shortcode"])
                        else:
                            extra_info["is_error"] = True
                            break
                        extra_info["media_info_list"].append(media_extra_info)
                    # 获取下一页的指针
                    if media_node["page_info"]["has_next_page"]:
                        extra_info["next_page_cursor"] = str(media_node["page_info"]["end_cursor"])
            else:
                extra_info["is_error"] = True
        media_page_response.extra_info = extra_info
        return media_page_response


# 获取媒体详细页
def get_media_page(page_id):
    media_page_url = "https://www.instagram.com/p/%s/" % page_id
    media_page_response = net.http_request(media_page_url)
    extra_info = {
        "is_error": True,  # 是不是格式不符合
        "image_url_list": [],  # 页面解析出的所有图片下载地址
        "video_url": "",  # 页面解析出的视频下载地址
        "json_data": None,  # 页面解析出的视频下载地址
    }
    if media_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        try:
            media_info_data = json.loads(tool.find_sub_string(media_page_response.data, "window._sharedData = ", ";</script>"))
            extra_info["json_data"] = media_info_data
        except ValueError:
            media_info_data = {}
        if (
            robot.check_sub_key(("entry_data",), media_info_data) and
            robot.check_sub_key(("PostPage",), media_info_data["entry_data"]) and
            len(media_info_data["entry_data"]["PostPage"]) == 1 and
            robot.check_sub_key(("graphql",), media_info_data["entry_data"]["PostPage"][0]) and
            robot.check_sub_key(("shortcode_media",), media_info_data["entry_data"]["PostPage"][0]["graphql"]) and
            robot.check_sub_key(("__typename",), media_info_data["entry_data"]["PostPage"][0]["graphql"]["shortcode_media"])
        ):
            media_info = media_info_data["entry_data"]["PostPage"][0]["graphql"]["shortcode_media"]
            # 多张图片
            if media_info["__typename"] == "GraphSidecar":
                if (
                    robot.check_sub_key(("edge_sidecar_to_children",), media_info) and
                    robot.check_sub_key(("edges",), media_info["edge_sidecar_to_children"]) and
                    len(media_info["edge_sidecar_to_children"]["edges"]) >= 2
                ):
                    extra_info["is_error"] = False
                    # 获取图片地址
                    for edge in media_info["edge_sidecar_to_children"]["edges"]:
                        if (
                            robot.check_sub_key(("node",), edge) and
                            robot.check_sub_key(("__typename", "display_url"), edge["node"]) and
                            edge["node"]["__typename"] == "GraphImage"
                        ):
                            extra_info["image_url_list"].append(str(edge["node"]["display_url"]))
                        else:
                            extra_info["is_error"] = True
                            break
            # 视频
            elif media_info["__typename"] == "GraphVideo":
                # 获取视频地址
                if robot.check_sub_key(("video_url",), media_info):
                    extra_info["is_error"] = False
                    extra_info["video_url"] = str(media_info["video_url"])
        media_page_response.extra_info = extra_info
    return media_page_response


class Instagram(robot.Robot):
    def __init__(self, extra_config=None):
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
            robot.SYS_SET_PROXY: True,
        }
        robot.Robot.__init__(self, sys_config, extra_config)

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
        # account_name  image_count  video_count  last_created_time
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

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if IS_SORT:
                image_path = os.path.join(IMAGE_TEMP_PATH, account_name)
                video_path = os.path.join(VIDEO_TEMP_PATH, account_name)
            else:
                image_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
                video_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)

            # 获取首页
            account_page_response = get_index_page(account_name)
            if account_page_response.status == 404:
                log.error(account_name + " 账号不存在")
                tool.process_exit()
            elif account_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                log.error(account_name + " 首页访问失败，原因：%s" % robot.get_http_request_failed_reason(account_page_response.status))
                tool.process_exit()

            if account_page_response.extra_info["account_id"] is None:
                log.error(account_name + " account id解析失败")
                tool.process_exit()

            image_count = 1
            video_count = 1
            cursor = ""
            first_created_time = "0"
            is_over = False
            need_make_image_dir = True
            need_make_video_dir = True
            while not is_over:
                log.step(account_name + " 开始解析cursor '%s'的媒体信息" % cursor)

                # 获取指定时间后的一页媒体信息
                index_page_response = get_one_page_media(account_page_response.extra_info["account_id"], cursor)
                if index_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                    log.error(account_name + " cursor '%s'的媒体信息访问失败，原因：%s" % (cursor, robot.get_http_request_failed_reason(index_page_response.status)))
                    tool.process_exit()

                if index_page_response.extra_info["is_error"]:
                    log.error(account_name + " cursor '%s'的媒体信息%s解析失败" % (cursor, index_page_response.json_data))
                    tool.process_exit()

                log.trace(account_name + " cursor '%s'解析的所有媒体信息：%s" % (cursor, index_page_response.extra_info["media_info_list"]))

                for media_info in index_page_response.extra_info["media_info_list"]:
                    # 检查是否已下载到前一次的图片
                    if int(media_info["time"]) <= int(self.account_info[3]):
                        is_over = True
                        break

                    # 将第一张图片的上传时间做为新的存档记录
                    if first_created_time == "0":
                        first_created_time = media_info["time"]

                    # 图片
                    if IS_DOWNLOAD_IMAGE:
                        # 多张图片
                        if media_info["is_image_group"]:
                            # 获取媒体详细页
                            media_page_response = get_media_page(media_info["page_id"])
                            if media_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                                log.error(account_name + " 媒体%s的详细页访问失败，原因：%s" % (media_info["page_id"], robot.get_http_request_failed_reason(index_page_response.status)))
                                tool.process_exit()

                            if media_page_response.extra_info["is_error"]:
                                if media_page_response.extra_info["json_data"] is None:
                                    log.error(account_name + " 媒体%s的详细页解析失败" % media_info["page_id"])
                                else:
                                    log.error(account_name + " 媒体信息%s解析失败" % media_page_response.extra_info["json_data"])
                                tool.process_exit()

                            image_url_list = media_page_response.extra_info["image_url_list"]
                        # 单张图片 或者 视频的预览图片
                        else:
                            if media_info["image_url"] is None:
                                log.error(account_name + " 媒体信息%s解析失败" % media_info["json_data"])
                                tool.process_exit()

                            image_url_list = [media_info["image_url"]]

                        for image_url in image_url_list:
                            log.step(account_name + " 开始下载第%s张图片 %s" % (image_count, image_url))

                            # 第一张图片，创建目录
                            if need_make_image_dir:
                                if not tool.make_dir(image_path, 0):
                                    log.error(account_name + " 创建图片下载目录 %s 失败" % image_path)
                                    tool.process_exit()
                                need_make_image_dir = False

                            file_type = image_url.split(".")[-1]
                            image_file_path = os.path.join(image_path, "%04d.%s" % (image_count, file_type))
                            save_file_return = net.save_net_file(image_url, image_file_path)
                            if save_file_return["status"] == 1:
                                log.step(account_name + " 第%s张图片下载成功" % image_count)
                                image_count += 1
                            else:
                                log.error(account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_count, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

                    # 视频
                    while IS_DOWNLOAD_VIDEO and media_info["is_video"]:
                        # 获取媒体详细页
                        media_page_response = get_media_page(media_info["page_id"])
                        if media_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                            log.error(account_name + " 媒体%s的详细页访问失败，原因：%s" % (media_info["page_id"], robot.get_http_request_failed_reason(index_page_response.status)))
                            tool.process_exit()

                        if media_page_response.extra_info["is_error"]:
                            if media_page_response.extra_info["json_data"] is None:
                                log.error(account_name + " 媒体%s的详细页解析失败" % media_info["page_id"])
                            else:
                                log.error(account_name + " 媒体信息%s解析失败" % media_page_response.extra_info["json_data"])
                            tool.process_exit()

                        video_url = media_page_response.extra_info["video_url"]
                        log.step(account_name + " 开始下载第%s个视频 %s" % (video_count, video_url))

                        # 第一个视频，创建目录
                        if need_make_video_dir:
                            if not tool.make_dir(video_path, 0):
                                log.error(account_name + " 创建视频下载目录 %s 失败" % video_path)
                                tool.process_exit()
                            need_make_video_dir = False

                        file_type = video_url.split(".")[-1]
                        video_file_path = os.path.join(video_path, "%04d.%s" % (video_count, file_type))
                        save_file_return = net.save_net_file(video_url, video_file_path)
                        if save_file_return["status"] == 1:
                            log.step(account_name + " 第%s个视频下载成功" % video_count)
                            video_count += 1
                        else:
                            log.error(account_name + " 第%s个视频 %s 下载失败，原因：%s" % (video_count, video_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
                        break

                    # 达到配置文件中的下载数量，结束
                    if 0 < GET_IMAGE_COUNT < image_count:
                        is_over = True
                        break
                    if 0 < GET_VIDEO_COUNT < video_count:
                        is_over = True
                        break

                if not is_over:
                    if index_page_response.extra_info["next_page_cursor"] is None:
                        is_over = True
                    else:
                        cursor = index_page_response.extra_info["next_page_cursor"]

            log.step(account_name + " 下载完毕，总共获得%s张图片和%s个视频" % (image_count - 1, video_count - 1))

            # 排序
            if IS_SORT:
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
            if first_created_time != "0":
                self.account_info[1] = str(int(self.account_info[1]) + image_count - 1)
                self.account_info[2] = str(int(self.account_info[2]) + video_count - 1)
                self.account_info[3] = first_created_time

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
    Instagram().main()
