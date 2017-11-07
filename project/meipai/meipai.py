# -*- coding:UTF-8  -*-
"""
美拍视频爬虫
http://www.meipai.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import base64
import os
import threading
import time
import traceback

ACCOUNTS = []
VIDEO_COUNT_PER_PAGE = 20  # 每次请求获取的视频数量
TOTAL_VIDEO_COUNT = 0
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""


# 获取指定页数的全部视频
def get_one_page_video(account_id, page_count):
    # http://www.meipai.com/users/user_timeline?uid=22744352&page=1&count=20&single_column=1
    video_pagination_url = "http://www.meipai.com/users/user_timeline"
    query_data = {
        "uid": account_id,
        "page": page_count,
        "count": VIDEO_COUNT_PER_PAGE,
        "single_column": 1,
    }
    video_pagination_response = net.http_request(video_pagination_url, method="GET", fields=query_data, json_decode=True)
    result = {
        "is_error": False,  # 是不是格式不符合
        "video_info_list": [],  # 全部视频信息
    }
    if video_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(video_pagination_response.status))
    if not robot.check_sub_key(("medias",), video_pagination_response.json_data):
        raise robot.RobotException("返回数据'medias'字段不存在\n%s" % video_pagination_response.json_data)
    for media_data in video_pagination_response.json_data["medias"]:
        # 历史直播，跳过
        if robot.check_sub_key(("lives",), media_data):
            continue
        result_video_info = {
            "video_id": None,  # 视频id
            "video_url": None,  # 视频下载地址
        }
        # 获取视频id
        if not robot.check_sub_key(("id",), media_data):
            raise robot.RobotException("视频信息'id'字段不存在\n%s" % media_data)
        result_video_info["video_id"] = str(media_data["id"])
        # 获取视频下载地址
        if not robot.check_sub_key(("video",), media_data):
            raise robot.RobotException("视频信息'video'字段不存在\n%s" % media_data)
        # 破解于播放器swf文件中com.meitu.cryptography.meipai.Default.decode
        loc1 = get_hex(str(media_data["video"]))
        loc2 = get_dec(loc1["hex"])
        loc3 = sub_str(loc1["str"], loc2["pre"])
        video_url_string = sub_str(loc3, get_pos(loc3, loc2["tail"]))
        try:
            video_url = base64.b64decode(video_url_string)
        except TypeError:
            raise robot.RobotException("加密视频地址解密失败\n%s\n%s" % (str(media_data["video"]), video_url_string))
        if video_url.find("http") != 0:
            raise robot.RobotException("加密视频地址解密失败\n%s\n%s" % (str(media_data["video"]), video_url_string))
        result_video_info["video_url"] = video_url
        result["video_info_list"].append(result_video_info)
    return result


def get_hex(arg1):
    return {"str": arg1[4:], "hex": reduce(lambda x, y: y + x, arg1[0:4])}


def get_dec(arg1):
    loc1 = str(int(arg1, 16))
    return {"pre": [int(loc1[0]), int(loc1[1])], "tail": [int(loc1[2]), int(loc1[3])]}


def sub_str(arg1, arg2):
    loc1 = arg1[:arg2[0]]
    loc2 = arg1[arg2[0]: arg2[0] + arg2[1]]
    return loc1 + arg1[arg2[0]:].replace(loc2, "", 1)


def get_pos(arg1, arg2):
    arg2[0] = len(arg1) - arg2[0] - arg2[1]
    return arg2


class MeiPai(robot.Robot):
    def __init__(self):
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH

        sys_config = {
            robot.SYS_DOWNLOAD_VIDEO: True,
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        VIDEO_DOWNLOAD_PATH = self.video_download_path
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

    def main(self):
        global ACCOUNTS

        # 解析存档文件
        # account_id  video_count  last_video_url
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0", ""])
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

        log.step("全部下载完毕，耗时%s秒，共计视频%s个" % (self.get_run_time(), TOTAL_VIDEO_COUNT))


class Download(robot.DownloadThread):
    def __init__(self, account_info, thread_lock):
        robot.DownloadThread.__init__(self, account_info, thread_lock)

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

            page_count = 1
            unique_list = []
            video_info_list = []
            is_over = False
            # 获取全部还未下载过需要解析的视频
            while not is_over:
                log.step(account_name + " 开始解析第%s页视频" % page_count)

                # 获取一页视频
                try:
                    video_pagination_response = get_one_page_video(account_id, page_count)
                except robot.RobotException, e:
                    log.error("第%s页视频解析失败，原因：%s" % (page_count, e.message))
                    raise

                # 已经没有视频了
                if len(video_pagination_response["video_info_list"]) == 0:
                    break

                log.trace(account_name + " 第%s页解析的全部视频：%s" % (page_count, video_pagination_response["video_info_list"]))

                # 寻找这一页符合条件的视频
                for video_info in video_pagination_response["video_info_list"]:
                    # 新增视频导致的重复判断
                    if video_info["video_id"] in unique_list:
                        continue
                    else:
                        unique_list.append(video_info["video_id"])

                    # 检查是否达到存档记录
                    if int(video_info["video_id"]) > int(self.account_info[2]):
                        video_info_list.append(video_info)
                    else:
                        is_over = True
                        break

                if not is_over:
                    if len(video_pagination_response["video_info_list"]) >= VIDEO_COUNT_PER_PAGE:
                        page_count += 1
                    else:
                        # 获取的数量小于请求的数量，已经没有剩余视频了
                        is_over = True

            log.step("需要下载的全部视频解析完毕，共%s个" % len(video_info_list))

            # 从最早的视频开始下载
            while len(video_info_list) > 0:
                video_info = video_info_list.pop()
                video_index = int(self.account_info[1]) + 1
                log.step(account_name + " 开始下载第%s个视频 %s" % (video_index, video_info["video_url"]))

                file_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name, "%04d.mp4" % video_index)
                save_file_return = net.save_net_file(video_info["video_url"], file_path)
                if save_file_return["status"] == 1:
                    log.step(account_name + " 第%s个视频下载成功" % video_index)
                else:
                    log.error(account_name + " 第%s个视频 %s 下载失败，原因：%s" % (video_index, video_info["video_url"], robot.get_save_net_file_failed_reason(save_file_return["code"])))
                # 视频下载完毕
                self.account_info[1] = str(video_index)  # 设置存档记录
                self.account_info[2] = video_info["video_id"]  # 设置存档记录
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
    MeiPai().main()
