# -*- coding:UTF-8  -*-
"""
Vine视频爬虫
https://vine.co/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import os
import threading
import time
import traceback

ACCOUNT_LIST = {}
TOTAL_VIDEO_COUNT = 0
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""


# 获取用户首页
def get_account_index_page(account_id):
    if not robot.is_integer(account_id):
        # 获取账号id
        account_vanity_url = "https://vine.co/api/users/profiles/vanity/%s" % account_id
        account_vanity_response = net.http_request(account_vanity_url, method="GET", json_decode=True)
        if account_vanity_response.status == 404:
            raise robot.RobotException("账号不存在")
        elif account_vanity_response.status != net.HTTP_RETURN_CODE_SUCCEED:
            raise robot.RobotException("账号ID页，%s" % robot.get_http_request_failed_reason(account_vanity_response.status))
        if not robot.check_sub_key(("data",), account_vanity_response.json_data):
            raise robot.RobotException("账号ID页返回信息'data'字段不存在\n%s" % account_vanity_response.json_data)
        if not robot.check_sub_key(("userIdStr",), account_vanity_response.json_data["data"]):
            raise robot.RobotException("账号ID页返回信息'userIdStr'字段不存在\n%s" % account_vanity_response.json_data)
        account_id = account_vanity_response.json_data["data"]["userIdStr"]
    # 获取账号详情
    account_profile_url = "https://archive.vine.co/profiles/%s.json" % account_id
    result = {
        "video_id_list": [],  # 日志id
    }
    account_profile_response = net.http_request(account_profile_url, method="GET", json_decode=True)
    if account_profile_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException("账号详情页，%s" % robot.get_http_request_failed_reason(account_profile_response.status))
    if not robot.check_sub_key(("private", "postCount", "posts"), account_profile_response.json_data):
        raise robot.RobotException("账号详情页返回信息'private'、'postCount'或'posts'字段不存在\n%s" % account_profile_response.json_data)
    if not robot.is_integer(account_profile_response.json_data["private"]) or int(account_profile_response.json_data["private"]) != 0:
        raise robot.RobotException("账号详情页非公开\n%s" % account_profile_response.json_data)
    if not robot.is_integer(account_profile_response.json_data["postCount"]):
        raise robot.RobotException("账号详情页返回信息'postCount'字段类型不正确\n%s" % account_profile_response.json_data)
    if not isinstance(account_profile_response.json_data["posts"], list):
        raise robot.RobotException("账号详情页返回信息'posts'字段类型不正确\n%s" % account_profile_response.json_data)
    if int(account_profile_response.json_data["postCount"]) != len(account_profile_response.json_data["posts"]):
        raise robot.RobotException("账号详情页视频数量解析错误\n%s" % account_profile_response.json_data)
    result["video_id_list"] = map(str, account_profile_response.json_data["posts"])
    return result


# 获取指定日志
def get_video_page(video_id):
    # https://archive.vine.co/posts/iUQV3w3mJMV.json
    video_page_url = "https://archive.vine.co/posts/%s.json" % video_id
    video_page_response = net.http_request(video_page_url, method="GET", json_decode=True)
    result = {
        "is_skip": False,  # 是否跳过
        "video_url": None,  # 视频地址
        "video_id": 0,  # 视频id（数字）
    }
    if video_page_response.status == 403:
        result["is_skip"] = True
    elif video_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(video_page_response.status))
    else:
        if not robot.check_sub_key(("postId", "videoUrl", "videoDashUrl"), video_page_response.json_data):
            raise robot.RobotException("返回信息'postId'、'videoUrl'或'videoDashUrl'字段不存在\n%s" % video_page_response.json_data)
        if not robot.is_integer(video_page_response.json_data["postId"]):
            raise robot.RobotException("返回信息'postId'字段类型不正确\n%s" % video_page_response.json_data)
        # 获取视频地址
        result["video_url"] = str(video_page_response.json_data["videoUrl"])
        # 获取视频id（数字）
        result["video_id"] = video_page_response.json_data["postId"]
    return result


class Vine(robot.Robot):
    def __init__(self):
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH

        sys_config = {
            robot.SYS_DOWNLOAD_VIDEO: True,
            robot.SYS_SET_PROXY: True,
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        VIDEO_DOWNLOAD_PATH = self.video_download_path
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

    def main(self):
        global ACCOUNT_LIST

        # 解析存档文件
        # account_id  video_count video_string_id  video_number_id
        ACCOUNT_LIST = robot.read_save_data(self.save_data_path, 0, ["", "0", "", "0"])

        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for account_id in sorted(ACCOUNT_LIST.keys()):
            # 检查正在运行的线程数
            if threading.activeCount() >= self.thread_count + main_thread_count:
                self.wait_sub_thread()

            # 提前结束
            if not self.is_running():
                break

            # 开始下载
            thread = Download(ACCOUNT_LIST[account_id], self)
            thread.start()

            time.sleep(1)

        # 检查除主线程外的其他所有线程是不是全部结束了
        while threading.activeCount() > main_thread_count:
            self.wait_sub_thread()

        # 未完成的数据保存
        if len(ACCOUNT_LIST) > 0:
            tool.write_file(tool.list_to_string(ACCOUNT_LIST.values()), NEW_SAVE_DATA_PATH)

        # 重新排序保存存档文件
        robot.rewrite_save_file(NEW_SAVE_DATA_PATH, self.save_data_path)

        log.step("全部下载完毕，耗时%s秒，共计视频%s个" % (self.get_run_time(), TOTAL_VIDEO_COUNT))


class Download(robot.DownloadThread):
    is_find = False  # 是不是有找到上次存档文件所指的视频id

    def __init__(self, account_info, main_thread):
        robot.DownloadThread.__init__(self, account_info, main_thread)
        self.account_id = self.account_info[0]
        if len(self.account_info) >= 5 and self.account_info[4]:
            self.account_name = self.account_info[4]
        else:
            self.account_name = self.account_info[0]
        self.total_video_count = 0
        log.step(self.account_name + " 开始")

    # 获取所有可下载视频
    def get_crawl_list(self):
        # 获取账号信息，包含全部视频
        try:
            account_index_page_response = get_account_index_page(self.account_id)
        except robot.RobotException, e:
            log.error(self.account_name + " 账号首页解析失败，原因：%s" % e.message)
            raise

        video_id_list = []
        # 是否有根据视频id找到上一次的记录
        if self.account_info[2] == "":
            self.is_find = True
        # 寻找符合条件的视频
        for video_id in account_index_page_response["video_id_list"]:
            # 检查是否达到存档记录
            if video_id != self.account_info[2]:
                video_id_list.append(video_id)
            else:
                self.is_find = True
                break

        return video_id_list

    # 解析单个视频
    def crawl_video(self, video_id):
        # 获取指定视频信息
        try:
            video_response = get_video_page(video_id)
        except robot.RobotException, e:
            log.error(self.account_name + " 视频%s解析失败，原因：%s" % (video_id, e.message))
            raise

        # 是否需要跳过，比如没有权限访问
        if video_response["is_skip"]:
            log.step(self.account_name + " 视频%s跳过" % video_response["video_id"])
            return

        # 如果解析需要下载的视频时没有找到上次的记录，表示存档所在的视频已被删除，则判断数字id
        if not self.is_find:
            if video_response["video_id"] < int(self.account_info[3]):
                log.step(self.account_name + " 视频%s跳过" % video_id)
                return
            else:
                self.is_find = True

        self.main_thread_check()  # 检测主线程运行状态
        video_index = int(self.account_info[1]) + 1
        log.step(self.account_name + " 开始下载第%s个视频 %s" % (video_index, video_response["video_url"]))

        file_type = video_response["video_url"].split("?")[0].split(".")[-1]
        video_file_path = os.path.join(VIDEO_DOWNLOAD_PATH, self.account_name, "%04d.%s" % (video_index, file_type))
        save_file_return = net.save_net_file(video_response["video_url"], video_file_path)
        if save_file_return["status"] == 1:
            # 设置临时目录
            log.step(self.account_name + " 第%s个视频下载成功" % video_index)
        else:
            log.error(self.account_name + " 第%s个视频 %s 下载失败，原因：%s" % (video_index, video_response["video_url"], robot.get_save_net_file_failed_reason(save_file_return["code"])))

        # 媒体内图片和视频全部下载完毕
        self.total_video_count += 1  # 计数累加
        self.account_info[1] = str(video_index)  # 设置存档记录
        self.account_info[2] = video_id  # 设置存档记录
        self.account_info[3] = str(video_response["video_id"])  # 设置存档记录

    def run(self):
        try:
            video_id_list = self.get_crawl_list()
            log.step(self.account_name + " 需要下载的全部视频解析完毕，共%s个" % len(video_id_list))
            if not self.is_find:
                log.step(self.account_name + " 存档所在视频已删除，需要在下载时进行过滤")

            while len(video_id_list) > 0:
                video_id = video_id_list.pop()
                log.step(self.account_name + " 开始解析视频%s" % video_id)
                self.crawl_video(video_id)
                self.main_thread_check()  # 检测主线程运行状态
        except SystemExit, se:
            if se.code == 0:
                log.step(self.account_name + " 提前退出")
            else:
                log.error(self.account_name + " 异常退出")
        except Exception, e:
            log.error(self.account_name + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 保存最后的信息
        with self.thread_lock:
            global TOTAL_VIDEO_COUNT
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            TOTAL_VIDEO_COUNT += self.total_video_count
            ACCOUNT_LIST.pop(self.account_id)
        log.step(self.account_name + " 下载完毕，总共获得%s个视频" % self.total_video_count)
        self.notify_main_thread()


if __name__ == "__main__":
    Vine().main()
