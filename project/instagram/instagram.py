# -*- coding:UTF-8  -*-
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
import urllib

ACCOUNTS = []
IMAGE_COUNT_PER_PAGE = 12
QUERY_ID = "17859156310193001"
TOTAL_IMAGE_COUNT = 0
TOTAL_VIDEO_COUNT = 0
IMAGE_TEMP_PATH = ""
IMAGE_DOWNLOAD_PATH = ""
VIDEO_TEMP_PATH = ""
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_DOWNLOAD_IMAGE = True
IS_DOWNLOAD_VIDEO = True


# 根据账号名字获得账号id（字母账号->数字账号)
def get_account_index_page(account_name):
    account_index_url = "https://www.instagram.com/%s" % account_name
    account_index_response = net.http_request(account_index_url)
    result = {
        "is_delete": False,  # 账号是否存在
        "account_id": None,  # account id
    }
    if account_index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        account_id = tool.find_sub_string(account_index_response.data, '"profilePage_', '"')
        if not robot.is_integer(account_id):
            raise robot.RobotException("页面解析账号id失败\n%s" % account_index_response.data)
        result["account_id"] = account_id
    elif account_index_response.status == 404:
        result["is_delete"] = True
    else:
        raise robot.RobotException(robot.get_http_request_failed_reason(account_index_response.status))
    return result


# 获取指定页数的所有媒体
# account_id -> 490060609
def get_one_page_media(account_id, cursor):
    if cursor:
        media_pagination_url = "https://www.instagram.com/graphql/query/?query_id=%s&id=%s&first=%s&after=%s" % (QUERY_ID, account_id, IMAGE_COUNT_PER_PAGE, cursor)
    else:
        media_pagination_url = "https://www.instagram.com/graphql/query/?query_id=%s&id=%s&first=%s" % (QUERY_ID, account_id, IMAGE_COUNT_PER_PAGE)
    media_pagination_response = net.http_request(media_pagination_url, json_decode=True)
    result = {
        "media_info_list": [],  # 所有媒体信息
        "next_page_cursor": None,  # 下一页媒体信息的指针
    }
    # Too Many Requests
    if media_pagination_response.status == 429:
        time.sleep(60)
        return get_one_page_media(account_id, cursor)
    elif media_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if not robot.check_sub_key(("status", "data"), media_pagination_response.json_data):
            raise robot.RobotException("返回数据'status'或'data'字段不存在\n%s" % media_pagination_response.json_data)
        if not robot.check_sub_key(("user",), media_pagination_response.json_data["data"]):
            raise robot.RobotException("返回数据'user'字段不存在\n%s" % media_pagination_response.json_data)
        if not robot.check_sub_key(("edge_owner_to_timeline_media",), media_pagination_response.json_data["data"]["user"]):
            raise robot.RobotException("返回数据'edge_owner_to_timeline_media'字段不存在\n%s" % media_pagination_response.json_data)
        if not robot.check_sub_key(("page_info", "edges",), media_pagination_response.json_data["data"]["user"]["edge_owner_to_timeline_media"]):
            raise robot.RobotException("返回数据'page_info', 'edges'字段不存在\n%s" % media_pagination_response.json_data)
        if not robot.check_sub_key(("end_cursor", "has_next_page",), media_pagination_response.json_data["data"]["user"]["edge_owner_to_timeline_media"]["page_info"]):
            raise robot.RobotException("返回数据'end_cursor', 'has_next_page'字段不存在\n%s" % media_pagination_response.json_data)
        if not isinstance(media_pagination_response.json_data["data"]["user"]["edge_owner_to_timeline_media"]["edges"], list):
            raise robot.RobotException("返回数据'edges'字段类型不正确\n%s" % media_pagination_response.json_data)
        if len(media_pagination_response.json_data["data"]["user"]["edge_owner_to_timeline_media"]["edges"]) == 0:
            raise robot.RobotException("返回数据'edges'字段长度不正确\n%s" % media_pagination_response.json_data)
        media_node = media_pagination_response.json_data["data"]["user"]["edge_owner_to_timeline_media"]
        for media_info in media_node["edges"]:
            media_result = {
                "image_url": None,  # 图片地址
                "is_group": False,  # 是不是图片/视频组
                "is_video": False,  # 是不是视频
                "page_id": None,  # 媒体详情界面id
                "time": None,  # 媒体上传时间
            }
            if not robot.check_sub_key(("node",), media_info):
                raise robot.RobotException("媒体信息'node'字段不存在\n%s" % media_info)
            if not robot.check_sub_key(("display_url", "taken_at_timestamp", "__typename", "shortcode",), media_info["node"]):
                raise robot.RobotException("媒体信息'display_url', 'taken_at_timestamp', '__typename', 'shortcode'字段不存在\n%s" % media_info)
            # GraphImage 单张图片、GraphSidecar 多张图片、GraphVideo 视频
            if media_info["node"]["__typename"] not in ["GraphImage", "GraphSidecar", "GraphVideo"]:
                raise robot.RobotException("媒体信息'__typename'取值范围不正确\n%s" % media_info)
            # 获取图片地址
            media_result["image_url"] = str(media_info["node"]["display_url"])

            # 判断是不是图片/视频组
            media_result["is_group"] = media_info["node"]["__typename"] == "GraphSidecar"

            # 判断是否有视频
            media_result["is_video"] = media_info["node"]["__typename"] == "GraphVideo"

            # 获取图片上传时间
            media_result["time"] = str(int(media_info["node"]["taken_at_timestamp"]))

            # 获取媒体详情界面id
            media_result["page_id"] = str(media_info["node"]["shortcode"])

            result["media_info_list"].append(media_result)
        # 获取下一页的指针
        if media_node["page_info"]["has_next_page"]:
            result["next_page_cursor"] = str(media_node["page_info"]["end_cursor"])
    else:
        raise robot.RobotException(robot.get_http_request_failed_reason(media_pagination_response.status))
    return result


# 获取媒体详细页
def get_media_page(page_id):
    media_url = "https://www.instagram.com/p/%s/" % page_id
    media_response = net.http_request(media_url)
    result = {
        "image_url_list": [],  # 所有图片地址
        "video_url_list": [],  # 所有视频地址
    }
    if media_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        media_info_html = tool.find_sub_string(media_response.data, "window._sharedData = ", ";</script>")
        if not media_info_html:
            robot.RobotException("页面截取媒体信息失败\n%s" % media_response.data)
        try:
            media_info_data = json.loads(media_info_html)
        except ValueError:
            raise robot.RobotException("媒体信息加载失败\n%s" % media_info_html)
        if not robot.check_sub_key(("entry_data",), media_info_data):
            raise robot.RobotException("返回数据'entry_data'字段不存在\n%s" % media_info_data)
        if not robot.check_sub_key(("PostPage",), media_info_data["entry_data"]):
            raise robot.RobotException("返回数据'PostPage'字段不存在\n%s" % media_info_data)
        if not (isinstance(media_info_data["entry_data"]["PostPage"], list) and len(media_info_data["entry_data"]["PostPage"]) == 1):
            raise robot.RobotException("返回数据'PostPage'字段类型不正确\n%s" % media_info_data)
        if not robot.check_sub_key(("graphql",), media_info_data["entry_data"]["PostPage"][0]):
            raise robot.RobotException("返回数据'graphql'字段不存在\n%s" % media_info_data)
        if not robot.check_sub_key(("shortcode_media",), media_info_data["entry_data"]["PostPage"][0]["graphql"]):
            raise robot.RobotException("返回数据'shortcode_media'字段不存在\n%s" % media_info_data)
        if not robot.check_sub_key(("__typename",), media_info_data["entry_data"]["PostPage"][0]["graphql"]["shortcode_media"]):
            raise robot.RobotException("返回数据'__typename'字段不存在\n%s" % media_info_data)
        if media_info_data["entry_data"]["PostPage"][0]["graphql"]["shortcode_media"]["__typename"] not in ["GraphSidecar", "GraphVideo"]:
            raise robot.RobotException("返回数据'__typename'取值范围不正确\n%s" % media_info_data)
        media_info = media_info_data["entry_data"]["PostPage"][0]["graphql"]["shortcode_media"]
        # 多张图片/视频
        if media_info["__typename"] == "GraphSidecar":
            if not robot.check_sub_key(("edge_sidecar_to_children",), media_info):
                raise robot.RobotException("媒体信息'edge_sidecar_to_children'字段不存在\n%s" % media_info)
            if not robot.check_sub_key(("edges",), media_info["edge_sidecar_to_children"]):
                raise robot.RobotException("媒体信息'edges'字段不存在\n%s" % media_info)
            if len(media_info["edge_sidecar_to_children"]["edges"]) < 2:
                raise robot.RobotException("媒体信息'edges'长度不正确\n%s" % media_info)
            for edge in media_info["edge_sidecar_to_children"]["edges"]:
                if not robot.check_sub_key(("node",), edge):
                    raise robot.RobotException("媒体节点'node'字段不存在\n%s" % edge)
                if not robot.check_sub_key(("__typename", "display_url"), edge["node"]):
                    raise robot.RobotException("媒体节点'__typename'或'display_url'字段不存在\n%s" % edge)

                # 获取图片地址
                result["image_url_list"].append(str(edge["node"]["display_url"]))

                # 获取视频地址
                if edge["node"]["__typename"] == "GraphVideo":
                    if not robot.check_sub_key(("video_url",), edge["node"]):
                        raise robot.RobotException("视频节点'video_url'字段不存在\n%s" % edge)
                    result["video_url_list"].append(str(edge["node"]["video_url"]))
        # 视频
        elif media_info["__typename"] == "GraphVideo":
            # 获取视频地址
            if not robot.check_sub_key(("video_url",), media_info):
                raise robot.RobotException("视频信息'video_url'字段不存在\n%s" % media_info)
            result["video_url_list"].append(str(media_info["video_url"]))
    else:
        raise robot.RobotException(robot.get_http_request_failed_reason(media_response.status))
    return result


class Instagram(robot.Robot):
    def __init__(self, extra_config=None):
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
            robot.SYS_SET_PROXY: True,
        }
        robot.Robot.__init__(self, sys_config, extra_config)

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
        # account_name  account_id  image_count  video_count  last_created_time
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "", "0", "0", "0"])
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

            # 获取首页
            try:
                account_index_response = get_account_index_page(account_name)
            except robot.RobotException, e:
                log.error(account_name + " 首页访问失败，原因：%s" % e.message)
                raise

            if account_index_response["is_delete"]:
                log.error(account_name + " 账号不存在")
                tool.process_exit()

            if self.account_info[1] == "":
                self.account_info[1] = account_index_response["account_id"]
            else:
                if self.account_info[1] != account_index_response["account_id"]:
                    log.error(account_name + " account id 不符合，原账号已改名")
                    tool.process_exit()

            image_count = 1
            video_count = 1
            cursor = ""
            is_over = False
            first_created_time = None
            image_path = os.path.join(IMAGE_TEMP_PATH, account_name)
            video_path = os.path.join(VIDEO_TEMP_PATH, account_name)
            while not is_over:
                log.step(account_name + " 开始解析cursor '%s'的媒体信息" % cursor)

                # 获取指定时间后的一页媒体信息
                try:
                    media_pagination_response = get_one_page_media(account_index_response["account_id"], cursor)
                except robot.RobotException, e:
                    log.error(account_name + " cursor '%s'的媒体信息访问失败，原因：%s" % (cursor, e.message))
                    raise 

                log.trace(account_name + " cursor '%s'解析的所有媒体信息：%s" % (cursor, media_pagination_response["media_info_list"]))

                for media_info in media_pagination_response["media_info_list"]:
                    # 检查是否达到存档记录
                    if int(media_info["time"]) <= int(self.account_info[4]):
                        is_over = True
                        break

                    # 新的存档记录
                    if first_created_time is None:
                        first_created_time = media_info["time"]

                    log.step(account_name + " 开始解析媒体%s" % media_info["page_id"])

                    media_response = None
                    # 图片
                    if IS_DOWNLOAD_IMAGE:
                        # 多张图片
                        if media_info["is_group"]:
                            # 获取媒体详细页
                            try:
                                media_response = get_media_page(media_info["page_id"])
                            except robot.RobotException, e:
                                log.error(account_name + " 媒体%s的详细页访问失败，原因：%s" % (media_info["page_id"], e.message))
                                raise

                            image_url_list = media_response["image_url_list"]
                        # 单张图片 或者 视频的预览图片
                        else:
                            image_url_list = [media_info["image_url"]]

                        for image_url in image_url_list:
                            # 去除特效，获取原始路径
                            image_url_protocol, image_url_path = urllib.splittype(image_url)
                            image_url_host = urllib.splithost(image_url_path)[0]
                            image_url_name = image_url.split("/")[-1]
                            image_url = "%s://%s//%s" % (image_url_protocol, image_url_host, image_url_name)
                            log.step(account_name + " 开始下载第%s张图片 %s" % (image_count, image_url))

                            file_type = image_url.split(".")[-1]
                            image_file_path = os.path.join(image_path, "%04d.%s" % (image_count, file_type))
                            save_file_return = net.save_net_file(image_url, image_file_path)
                            if save_file_return["status"] == 1:
                                log.step(account_name + " 第%s张图片下载成功" % image_count)
                                image_count += 1
                            else:
                                log.error(account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_count, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

                    # 视频
                    if IS_DOWNLOAD_VIDEO and (media_info["is_group"] or media_info["is_video"]):
                        if media_response is None:
                            # 获取媒体详细页
                            try:
                                media_response = get_media_page(media_info["page_id"])
                            except robot.RobotException, e:
                                log.error(account_name + " 媒体%s的详细页访问失败，原因：%s" % (media_info["page_id"], e.message))
                                raise

                        for video_url in media_response["video_url_list"]:
                            log.step(account_name + " 开始下载第%s个视频 %s" % (video_count, video_url))

                            file_type = video_url.split(".")[-1]
                            video_file_path = os.path.join(video_path, "%04d.%s" % (video_count, file_type))
                            save_file_return = net.save_net_file(video_url, video_file_path)
                            if save_file_return["status"] == 1:
                                log.step(account_name + " 第%s个视频下载成功" % video_count)
                                video_count += 1
                            else:
                                log.error(account_name + " 第%s个视频 %s 下载失败，原因：%s" % (video_count, video_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

                if not is_over:
                    if media_pagination_response["next_page_cursor"] is None:
                        is_over = True
                    else:
                        cursor = media_pagination_response["next_page_cursor"]

            log.step(account_name + " 下载完毕，总共获得%s张图片和%s个视频" % (image_count - 1, video_count - 1))

            # 排序
            if image_count > 1:
                log.step(account_name + " 图片开始从下载目录移动到保存目录")
                destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
                if robot.sort_file(image_path, destination_path, int(self.account_info[2]), 4):
                    log.step(account_name + " 图片从下载目录移动到保存目录成功")
                else:
                    log.error(account_name + " 创建图片保存目录 %s 失败" % destination_path)
                    tool.process_exit()
            if video_count > 1:
                log.step(account_name + " 视频开始从下载目录移动到保存目录")
                destination_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)
                if robot.sort_file(video_path, destination_path, int(self.account_info[3]), 4):
                    log.step(account_name + " 视频从下载目录移动到保存目录成功")
                else:
                    log.error(account_name + " 创建视频保存目录 %s 失败" % destination_path)
                    tool.process_exit()

            # 新的存档记录
            if first_created_time is not None:
                self.account_info[2] = str(int(self.account_info[2]) + image_count - 1)
                self.account_info[3] = str(int(self.account_info[3]) + video_count - 1)
                self.account_info[4] = first_created_time

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
