# -*- coding:UTF-8  -*-
"""
PR社APP图片&视频爬虫
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
POST_COUNT_PER_PAGE = 10  # 每次获取的作品数量（貌似无效）
TOTAL_IMAGE_COUNT = 0
TOTAL_VIDEO_COUNT = 0
IMAGE_DOWNLOAD_PATH = ""
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_DOWNLOAD_IMAGE = True
IS_DOWNLOAD_VIDEO = True
IS_STEP_INVALID_RESOURCE = False


# 获取指定时间后的一页作品
def get_one_page_post(account_id, timestamp):
    post_pagination_url = "https://api.prpr.tinydust.cn/v3/posts/old"
    query_data = {
        "timestamp": timestamp,
        "userId": account_id,
        "limit": POST_COUNT_PER_PAGE,
    }
    index_response = net.http_request(post_pagination_url, method="GET", fields=query_data, json_decode=True)
    result = {
        "post_info_list": [],  # 全部作品信息
    }
    if index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(index_response.status))
    if not robot.check_sub_key(("code",), index_response.json_data):
        raise robot.RobotException("返回信息'code'字段不存在\n%s" % index_response.json_data)
    if not robot.is_integer(index_response.json_data["code"]):
        raise robot.RobotException("返回信息'code'字段类型不正确\n%s" % index_response.json_data)
    if int(index_response.json_data["code"]) != 200:
        raise robot.RobotException("返回信息'code'字段取值不正确\n%s" % index_response.json_data)
    if not robot.check_sub_key(("result",), index_response.json_data):
        raise robot.RobotException("返回信息'result'字段不存在\n%s" % index_response.json_data)
    for post_info in index_response.json_data["result"]:
        result_post_info = {
            "post_id": None,  # 作品id
            "post_time": None,  # 作品时间
        }
        if not robot.check_sub_key(("_id",), post_info):
            raise robot.RobotException("作品信息'_id'字段不存在\n%s" % post_info)
        result_post_info["post_id"] = str(post_info["_id"])
        if not robot.check_sub_key(("createdAt",), post_info):
            raise robot.RobotException("作品信息'createdAt'字段不存在\n%s" % post_info)
        if not robot.is_integer(post_info["createdAt"]):
            raise robot.RobotException("作品信息'createdAt'字段类型不正确\n%s" % post_info)
        result_post_info["post_time"] = int(post_info["createdAt"])
        result["post_info_list"].append(result_post_info)
    return result


# 获取指定作品
def get_post_page(post_id):
    index_url = "https://api.prpr.tinydust.cn/v3/posts/%s" % post_id
    index_response = net.http_request(index_url, method="GET", json_decode=True)
    result = {
        "image_url_list": [],  # 全部图片地址
        "video_url_list": [],  # 全部视频地址
    }
    if index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(index_response.status))
    if not robot.check_sub_key(("code",), index_response.json_data):
        raise robot.RobotException("返回信息'code'字段不存在\n%s" % index_response.json_data)
    if not robot.is_integer(index_response.json_data["code"]):
        raise robot.RobotException("返回信息'code'字段类型不正确\n%s" % index_response.json_data)
    if int(index_response.json_data["code"]) != 200:
        raise robot.RobotException("返回信息'code'字段取值不正确\n%s" % index_response.json_data)
    if not robot.check_sub_key(("result",), index_response.json_data):
        raise robot.RobotException("返回信息'result'字段不存在\n%s" % index_response.json_data)
    if not robot.check_sub_key(("pictures", "imageCount", "videoCount"), index_response.json_data["result"]):
        raise robot.RobotException("返回信息'pictures'、'imageCount'或'videoCount'字段不存在\n%s" % index_response.json_data)
    for media_info in index_response.json_data["result"]["pictures"]:
        if not robot.check_sub_key(("url",), media_info):
            raise robot.RobotException("返回信息'url'字段不存在\n%s" % media_info)
        if not robot.check_sub_key(("type",), media_info):
            raise robot.RobotException("返回信息'type'字段不存在\n%s" % media_info)
        if not robot.is_integer(media_info["type"]):
            raise robot.RobotException("返回信息'type'字段类型不正确\n%s" % media_info)
        media_type = int(media_info["type"])
        if media_type == 0:
            result["image_url_list"].append(str(media_info["url"]))
        elif media_type == 1:
            if media_info["url"][0] != "?":
                result["video_url_list"].append(str(media_info["url"]))
            else:
                if not robot.check_sub_key(("thum",), media_info):
                    raise robot.RobotException("返回信息'thum'字段不存在\n%s" % media_info)
                result["image_url_list"].append(str(media_info["thum"]))
        else:
            raise robot.RobotException("返回信息'type'字段取值不正确\n%s" % media_info)
    return result


# 检测下载得文件是否有效
def check_invalid(file_path):
    if file_path.split(".")[-1] == "png" and os.path.getsize(file_path) < 102400:
        if tool.get_file_md5(file_path) in ["76d8988358e84e123a126d736be4bc44", "0d527d84f1150d002998cb67ec271de5", "2423c99718385d789cec3e6c1c1020db",
                                            "0764beb3d521b9b420d365f6ee6d453b", "1ba2863db2ac7296d73818be890ef378", "7a9abea08bc47d3a64f87eebdd533dcd",
                                            "23e0a284d4fa44c222bf41d3cb58b241", "483ec66794f1dfa02d634c4745fd4ded", "dd77da050fc0bcf79d22d35deb1019bd"]:
            return True
    return False


class PrPr(robot.Robot):
    def __init__(self):
        global IMAGE_DOWNLOAD_PATH
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_DOWNLOAD_IMAGE
        global IS_DOWNLOAD_VIDEO
        global IS_STEP_INVALID_RESOURCE

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_DOWNLOAD_VIDEO: True,
            robot.SYS_APP_CONFIG: (os.path.realpath("config.ini"), ("IS_STEP_INVALID_RESOURCE", False, 2)),
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        VIDEO_DOWNLOAD_PATH = self.video_download_path
        IS_DOWNLOAD_IMAGE = self.is_download_image
        IS_DOWNLOAD_VIDEO = self.is_download_video
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)
        IS_STEP_INVALID_RESOURCE = self.app_config["IS_STEP_INVALID_RESOURCE"]

    def main(self):
        global ACCOUNTS

        # 解析存档文件
        # account_id last_post_time
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

        # 重新排序保存存档文件
        robot.rewrite_save_file(NEW_SAVE_DATA_PATH, self.save_data_path)

        log.step("全部下载完毕，耗时%s秒，共计图片%s张，视频%s个" % (self.get_run_time(), TOTAL_IMAGE_COUNT, TOTAL_VIDEO_COUNT))


class Download(robot.DownloadThread):
    def __init__(self, account_info, thread_lock):
        robot.DownloadThread.__init__(self, account_info, thread_lock)

    def run(self):
        global TOTAL_IMAGE_COUNT
        global TOTAL_VIDEO_COUNT

        account_id = self.account_info[0]
        if len(self.account_info) > 2 and self.account_info[2]:
            account_name = self.account_info[2]
        else:
            account_name = account_id
        total_image_count = 0
        total_video_count = 0
        temp_path_list = []

        try:
            log.step(account_name + " 开始")

            page_count = 1
            post_id_list = []
            is_over = False
            timestamp = int(time.time() * 1000)
            # 获取全部还未下载过需要解析的作品
            while not is_over:
                log.step(account_name + " 开始解析%s后一页的作品" % timestamp)
                # 获取一页作品
                try:
                    post_pagination_response = get_one_page_post(account_id, timestamp)
                except robot.RobotException, e:
                    log.error(account_name + " 首页解析失败，原因：%s" % e.message)
                    raise

                log.trace(account_name + " 第%s页解析的全部作品：%s" % (page_count, post_pagination_response["post_info_list"]))

                # 寻找这一页符合条件的媒体
                for post_info in post_pagination_response["post_info_list"]:
                    # 检查是否达到存档记录
                    if post_info["post_time"] > int(self.account_info[1]):
                        post_id_list.append(post_info)
                        # 设置下一页指针
                        timestamp = post_info["post_time"]
                    else:
                        is_over = True
                        break

                if not is_over:
                    if len(post_pagination_response["post_info_list"]) < POST_COUNT_PER_PAGE:
                        is_over = True

            log.step(account_name + " 需要下载的全部作品解析完毕，共%s个" % len(post_id_list))

            while len(post_id_list) > 0:
                post_info = post_id_list.pop()
                log.step(account_name + " 开始解析作品%s" % post_info["post_id"])

                # 获取指定作品
                try:
                    blog_response = get_post_page(post_info["post_id"])
                except robot.RobotException, e:
                    log.error(account_name + " 作品%s解析失败，原因：%s" % (post_info["post_id"], e.message))
                    raise

                # 图片下载
                image_index = 1
                if IS_DOWNLOAD_IMAGE:
                    for image_url in blog_response["image_url_list"]:
                        log.step(account_name + " 作品%s 开始下载第%s张图片 %s" % (post_info["post_id"], image_index, image_url))

                        origin_image_url, file_param = image_url.split("?", 1)
                        file_name_and_type = origin_image_url.split("/")[-1]
                        if file_param.find("/blur/") >= 0:
                            image_file_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name, "blur", file_name_and_type)
                        else:
                            image_file_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name, "other", file_name_and_type)
                        save_file_return = net.save_net_file(image_url, image_file_path, need_content_type=True)
                        if save_file_return["status"] == 1:
                            if check_invalid(save_file_return["file_path"]):
                                path.delete_dir_or_file(save_file_return["file_path"])
                                error_message = account_name + " 作品%s 第%s张图 %s 无效，已删除" % (post_info["post_id"], image_index, image_url)
                                if IS_STEP_INVALID_RESOURCE:
                                    log.step(error_message)
                                else:
                                    log.error(error_message)
                            else:
                                # 设置临时目录
                                temp_path_list.append(image_file_path)
                                log.step(account_name + " 作品%s 第%s张图片 下载成功" % (post_info["post_id"], image_index))
                                image_index += 1
                        else:
                            log.error(account_name + " 作品%s 第%s张图片 %s 下载失败，原因：%s" % (post_info["post_id"], image_index, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

                # 视频下载
                video_index = 1
                if IS_DOWNLOAD_VIDEO:
                    for video_url in blog_response["video_url_list"]:
                        log.step(account_name + " 作品%s 开始下载第%s个视频 %s" % (post_info["post_id"], video_index, video_url))

                        video_file_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name, "%s_%02d.mp4" % (post_info["post_id"], video_index))
                        save_file_return = net.save_net_file(video_url, video_file_path, need_content_type=True)
                        if save_file_return["status"] == 1:
                            if check_invalid(save_file_return["file_path"]):
                                path.delete_dir_or_file(save_file_return["file_path"])
                                error_message = account_name + " 作品%s 第%s个视频 %s 无效，已删除" % (post_info["post_id"], video_index, video_url)
                                if IS_STEP_INVALID_RESOURCE:
                                    log.step(error_message)
                                else:
                                    log.error(error_message)
                            else:
                                # 设置临时目录
                                temp_path_list.append(video_file_path)
                                log.step(account_name + " 作品%s 第%s个视频下载成功" % (post_info["post_id"], video_index))
                                video_index += 1
                        else:
                            log.error(account_name + " 作品%s 第%s个视频 %s 下载失败，原因：%s" % (post_info["post_id"], video_index, video_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

                # 媒体内图片和视频全部下载完毕
                temp_path_list = []  # 临时目录设置清除
                total_image_count += (image_index - 1)  # 计数累加
                total_video_count += (video_index - 1)  # 计数累加
                self.account_info[1] = str(post_info["post_time"])  # 设置存档记录
        except SystemExit, se:
            if se.code == 0:
                log.step(account_name + " 提前退出")
            else:
                log.error(account_name + " 异常退出")
            # 如果临时目录变量不为空，表示某个作品正在下载中，需要把下载了部分的内容给清理掉
            if len(temp_path_list) > 0:
                for temp_path in temp_path_list:
                    path.delete_dir_or_file(temp_path)
        except Exception, e:
            log.error(account_name + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 保存最后的信息
        with self.thread_lock:
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            TOTAL_IMAGE_COUNT += total_image_count
            TOTAL_VIDEO_COUNT += total_video_count
            ACCOUNTS.remove(account_id)
        log.step(account_name + " 下载完毕，总共获得%s张图片和%s个视频" % (total_image_count, total_video_count))


if __name__ == "__main__":
    PrPr().main()
