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


# 获取用户的suid，作为查找指定用户的视频页的凭证
# account_id -> mi9wmdhhof
def get_account_index_page(account_id):
    account_index_url = "http://www.miaopai.com/u/paike_%s/relation/follow.htm" % account_id
    account_index_response = net.http_request(account_index_url, method="GET")
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


# 获取指定页数的全部视频
# suid -> 0r9ewgQ0v7UoDptu
def get_one_page_video(suid, page_count):
    # http://www.miaopai.com/gu/u?page=1&suid=0r9ewgQ0v7UoDptu&fen_type=channel
    video_pagination_url = "http://www.miaopai.com/gu/u"
    query_data = {
        "page": page_count,
        "suid": suid,
        "fen_type": "channel",
    }
    video_pagination_response = net.http_request(video_pagination_url, method="GET", fields=query_data, json_decode=True)
    result = {
        "is_over": False,  # 是不是最后一页视频
        "video_id_list": [],  # 全部视频id
    }
    if video_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 判断是不是最后一页
        if not robot.check_sub_key(("isall",), video_pagination_response.json_data):
            raise robot.RobotException("返回信息'isall'字段不存在\n%s" % video_pagination_response.json_data)
        result["is_over"] = bool(video_pagination_response.json_data["isall"])
        # 获取全部视频id
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
    video_info_url = "http://gslb.miaopai.com/stream/%s.json" % video_id
    query_data = {"token": ""}
    video_info_response = net.http_request(video_info_url, method="GET", fields=query_data, json_decode=True)
    result = {
        "video_url_list": [],  # 视频地址
    }
    if video_info_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 获取视频地址
        if not robot.check_sub_key(("result",), video_info_response.json_data):
            raise robot.RobotException("返回信息'result'字段不存在\n%s" % video_info_response.json_data)
        # 存在多个CDN地址
        video_url_list = []
        for result in video_info_response.json_data["result"]:
            if robot.check_sub_key(("path", "host", "scheme"), result):
                video_url_list.append(str(result["scheme"]) + str(result["host"]) + str(result["path"]))
        if len(video_url_list) == 0:
            raise robot.RobotException("返回信息匹配视频地址失败\n%s" % video_info_response.json_data)
        result["video_url_list"] = video_url_list
    else:
        raise robot.RobotException(robot.get_http_request_failed_reason(video_info_response.status))
    return result


class MiaoPai(robot.Robot):
    def __init__(self):
        sys_config = {
            robot.SYS_DOWNLOAD_VIDEO: True,
        }
        robot.Robot.__init__(self, sys_config)

    def main(self):
        # 解析存档文件
        # account_id  video_count  last_video_url
        self.account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "", ""])

        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for account_id in sorted(self.account_list.keys()):
            # 检查正在运行的线程数
            if threading.activeCount() >= self.thread_count + main_thread_count:
                self.wait_sub_thread()

            # 提前结束
            if not self.is_running():
                break

            # 开始下载
            thread = Download(self.account_list[account_id], self)
            thread.start()

            time.sleep(1)

        # 检查除主线程外的其他所有线程是不是全部结束了
        while threading.activeCount() > main_thread_count:
            self.wait_sub_thread()

        # 未完成的数据保存
        if len(self.account_list) > 0:
            tool.write_file(tool.list_to_string(self.account_list.values()), self.temp_save_data_path)

        # 重新排序保存存档文件
        robot.rewrite_save_file(self.temp_save_data_path, self.save_data_path)

        log.step("全部下载完毕，耗时%s秒，共计视频%s个" % (self.get_run_time(), self.total_video_count))


class Download(robot.DownloadThread):
    def __init__(self, account_info, main_thread):
        robot.DownloadThread.__init__(self, account_info, main_thread)
        self.account_id = self.account_info[0]
        if len(self.account_info) >= 4 and self.account_info[3]:
            self.account_name = self.account_info[3]
        else:
            self.account_name = self.account_info[0]
        log.step(self.account_name + " 开始")

    # 获取所有可下载视频
    def get_crawl_list(self, user_id):
        page_count = 1
        video_id_list = []
        is_over = False
        # 获取全部还未下载过需要解析的视频
        while not is_over:
            self.main_thread_check()  # 检测主线程运行状态
            log.step(self.account_name + " 开始解析第%s页视频" % page_count)

            # 获取指定一页的视频信息
            try:
                video_pagination_response = get_one_page_video(user_id, page_count)
            except robot.RobotException, e:
                log.error(self.account_name + " 第%s页视频解析失败，原因：%s" % (page_count, e.message))
                raise

            log.trace(self.account_name + " 第%s页解析的全部视频：%s" % (page_count, video_pagination_response["video_id_list"]))

            # 寻找这一页符合条件的视频
            for video_id in video_pagination_response["video_id_list"]:
                # 检查是否达到存档记录
                if video_id != self.account_info[2]:
                    # 新增视频导致的重复判断
                    if video_id in video_id_list:
                        continue
                    else:
                        video_id_list.append(video_id)
                else:
                    is_over = True
                    break

            # 没有视频了
            if video_pagination_response["is_over"]:
                if self.account_info[2] != "":
                    log.error(self.account_name + " 没有找到上次下载的最后一个视频地址")
                is_over = True
            else:
                page_count += 1

    # 解析单个视频
    def crawl_video(self, video_id):
        # 获取视频下载地址
        try:
            video_info_response = get_video_info_page(video_id)
        except robot.RobotException, e:
            log.error(self.account_name + " 视频%s解析失败，原因：%s" % (video_id, e.message))
            raise

        video_index = int(self.account_info[1]) + 1
        file_path = os.path.join(self.main_thread.video_download_path, self.account_name, "%04d.mp4" % video_index)
        while len(video_info_response["video_url_list"]) > 0:
            self.main_thread_check()  # 检测主线程运行状态
            video_url = video_info_response["video_url_list"].pop(0)
            log.step(self.account_name + " 开始下载第%s个视频 %s" % (video_index, video_url))

            save_file_return = net.save_net_file(video_url, file_path)
            if save_file_return["status"] == 1:
                log.step(self.account_name + " 第%s个视频下载成功" % video_index)
                break
            else:
                error_message = self.account_name + " 第%s个视频 %s 下载失败，原因：%s" % (video_index, video_url, robot.get_save_net_file_failed_reason(save_file_return["code"]))
                if len(video_url) == 0:
                    log.error(error_message)
                else:
                    log.step(error_message)

        # 视频下载完毕
        self.account_info[1] = str(video_index)  # 设置存档记录
        self.account_info[2] = video_id  # 设置存档记录
        self.total_video_count += 1  # 计数累加

    def run(self):
        try:
            try:
                account_index_response = get_account_index_page(self.account_id)
            except robot.RobotException, e:
                log.error(self.account_name + " 首页解析失败，原因：%s" % e.message)
                raise

            # 获取所有可下载视频
            video_id_list = self.get_crawl_list(account_index_response["user_id"])
            log.step(self.account_name + " 需要下载的全部视频解析完毕，共%s个" % len(video_id_list))

            # 从最早的视频开始下载
            while len(video_id_list) > 0:
                video_id = video_id_list.pop()
                log.step(self.account_name + " 开始解析第%s个视频 %s" % (int(self.account_info[1]) + 1, video_id))
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
            tool.write_file("\t".join(self.account_info), self.main_thread.temp_save_data_path)
            self.main_thread.total_video_count += self.total_video_count
            self.main_thread.account_list.pop(self.account_id)
        log.step(self.account_name + " 下载完毕，总共获得%s个视频" % self.total_video_count)
        self.notify_main_thread()


if __name__ == "__main__":
    MiaoPai().main()
