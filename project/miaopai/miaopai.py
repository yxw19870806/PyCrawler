# -*- coding:UTF-8  -*-
"""
秒拍视频爬虫
http://www.miaopai.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import os
import re
import threading
import time
import traceback

ACCOUNTS = []
TOTAL_VIDEO_COUNT = 0
VIDEO_TEMP_PATH = ""
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""


# 获取用户的suid，作为查找指定用户的视频页的凭证
# account_id -> mi9wmdhhof
def get_account_index_page(account_id):
    account_index_url = "http://www.miaopai.com/u/paike_%s/relation/follow.htm" % account_id
    account_index_response = net.http_request(account_index_url)
    result = {
        "user_id": None,  # 账号user id
    }
    if account_index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(account_index_response.status))
    user_id = tool.find_sub_string(account_index_response.data, '<button class="guanzhu gz" suid="', '" heade="1" token="')
    if not user_id:
        raise robot.RobotException("页面截取user id失败\n%s" % account_index_response.data)
    result["user_id"] = user_id
    return result


# 获取指定页数的所有视频
# suid -> 0r9ewgQ0v7UoDptu
def get_one_page_video(suid, page_count):
    # http://www.miaopai.com/gu/u?page=1&suid=0r9ewgQ0v7UoDptu&fen_type=channel
    video_pagination_url = "http://www.miaopai.com/gu/u?page=%s&suid=%s&fen_type=channel" % (page_count, suid)
    video_pagination_response = net.http_request(video_pagination_url, json_decode=True)
    result = {
        "video_id_list": [],  # 所有视频id
        "is_over": False  # 是不是最后一页视频
    }
    if video_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 判断是不是最后一页
        if not robot.check_sub_key(("isall",), video_pagination_response.json_data):
            raise robot.RobotException("返回信息'isall'字段不存在\n%s" % video_pagination_response.json_data)
        result["is_over"] = bool(video_pagination_response.json_data["isall"])
        # 获取所有视频id
        if not robot.check_sub_key(("msg",), video_pagination_response.json_data):
            raise robot.RobotException("返回信息'msg'字段不存在\n%s" % video_pagination_response.json_data)
        video_id_list = re.findall('data-scid="([^"]*)"', video_pagination_response.json_data["msg"])
        if not result["is_over"] and len(video_id_list) == 0:
            raise robot.RobotException("页面匹配视频id失败\n%s" % video_pagination_response.json_data)
        result["video_id_list"] = map(str, video_id_list)
    else:
        raise robot.RobotException(robot.get_http_request_failed_reason(video_pagination_response.status))
    return result


# 获取指定id视频的详情页
def get_video_info_page(video_id):
    video_info_url = "http://gslb.miaopai.com/stream/%s.json?token=" % video_id
    video_info_response = net.http_request(video_info_url, json_decode=True)
    result = {
        "video_url": None,  # 视频地址
    }
    if video_info_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 获取视频地址
        if not robot.check_sub_key(("result",), video_info_response.json_data):
            raise robot.RobotException("返回信息'result'字段不存在\n%s" % video_info_response.json_data)
        # 存在多个CDN地址，任意一个匹配即可
        for result in video_info_response.json_data["result"]:
            if robot.check_sub_key(("path", "host", "scheme"), result):
                result["video_url"] = str(result["scheme"]) + str(result["host"]) + str(result["path"])
                break
        if result["video_url"] is None:
            raise robot.RobotException("返回信息匹配视频地址失败\n%s" % video_info_response.json_data)
    else:
        raise robot.RobotException(robot.get_http_request_failed_reason(video_info_response.status))
    return result


class MiaoPai(robot.Robot):
    def __init__(self):
        global VIDEO_TEMP_PATH
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH

        sys_config = {
            robot.SYS_DOWNLOAD_VIDEO: True,
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        VIDEO_TEMP_PATH = self.video_temp_path
        VIDEO_DOWNLOAD_PATH = self.video_download_path
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

    def main(self):
        global ACCOUNTS

        # 解析存档文件
        # account_id  video_count  last_video_url
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "", ""])
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

        log.step("全部下载完毕，耗时%s秒，共计视频%s个" % (self.get_run_time(), TOTAL_VIDEO_COUNT))


class Download(threading.Thread):
    def __init__(self, account_info, thread_lock):
        threading.Thread.__init__(self)
        self.account_info = account_info
        self.thread_lock = thread_lock

    def run(self):
        global TOTAL_VIDEO_COUNT

        account_id = self.account_info[0]
        if len(self.account_info) >= 4 and self.account_info[3]:
            account_name = self.account_info[3]
        else:
            account_name = self.account_info[0]
        total_video_count = 0

        try:
            log.step(account_name + " 开始")

            try:
                account_index_response = get_account_index_page(account_id)
            except robot.RobotException, e:
                log.error(account_name + " 首页解析失败，原因：%s" % e.message)
                raise

            page_count = 1
            unique_list = []
            video_id_list = []
            is_over = False
            # 获取全部还未下载过需要解析的视频
            while not is_over:
                log.step(account_name + " 开始解析第%s页视频" % page_count)

                # 获取指定一页的视频信息
                try:
                    video_pagination_response = get_one_page_video(account_index_response["user_id"], page_count)
                except robot.RobotException, e:
                    log.error(account_name + " 第%s页视频解析失败，原因：%s" % (page_count, e.message))
                    raise

                log.trace(account_name + " 第%s页解析的所有视频：%s" % (page_count, video_pagination_response["video_id_list"]))

                # 寻找这一页符合条件的视频
                for video_id in video_pagination_response["video_id_list"]:
                    # 新增视频导致的重复判断
                    if video_id in unique_list:
                        continue
                    else:
                        unique_list.append(video_id)

                    # 检查是否达到存档记录
                    if video_id != self.account_info[2]:
                        video_id_list.append(video_id)
                    else:
                        is_over = True
                        break

                # 没有视频了
                if video_pagination_response["is_over"]:
                    if self.account_info[2] != "":
                        log.error(account_name + " 没有找到上次下载的最后一个视频地址")
                    is_over = True
                else:
                    page_count += 1

            log.step(account_name + " 需要下载的全部视频解析完毕，共%s个" % len(video_id_list))

            # 从最早的视频开始下载
            while len(video_id_list) > 0:
                video_id = video_id_list.pop()
                video_index = int(self.account_info[1]) + 1
                log.step(account_name + " 开始解析第%s个视频 %s" % (video_index, video_id))

                # 获取视频下载地址
                try:
                    video_info_response = get_video_info_page(video_id)
                except robot.RobotException, e:
                    log.error(account_name + " 视频%s解析失败，原因：%s" % (video_id, e.message))
                    raise

                log.step(account_name + " 开始下载第%s个视频 %s" % (video_index, video_info_response["video_url"]))

                file_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name, "%04d.mp4" % video_index)
                save_file_return = net.save_net_file(video_info_response["video_url"], file_path)
                if save_file_return["status"] == 1:
                    log.step(account_name + " 第%s个视频下载成功" % video_index)
                else:
                    log.error(account_name + " 第%s个视频 %s 下载失败，原因：%s" % (video_index, video_info_response["video_url"], robot.get_save_net_file_failed_reason(save_file_return["code"])))
                # 视频下载完毕
                self.account_info[1] = str(video_index)  # 设置存档记录
                self.account_info[2] = video_id  # 设置存档记录
                total_video_count += 1  # 计数累加
        except SystemExit, se:
            if se.code == 0:
                log.step(account_name + " 提前退出")
            else:
                log.error(account_name + " 异常退出")
        except Exception, e:
            log.error(account_name + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 保存最后的信息
        self.thread_lock.acquire()
        tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
        TOTAL_VIDEO_COUNT += total_video_count
        ACCOUNTS.remove(account_id)
        self.thread_lock.release()
        log.step(account_name + " 下载完毕，总共获得%s个视频" % total_video_count)


if __name__ == "__main__":
    MiaoPai().main()
