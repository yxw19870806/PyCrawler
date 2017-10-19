# -*- coding:UTF-8  -*-
"""
微视视频爬虫
http://weishi.qq.com
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import os
import random
import threading
import time
import traceback

ACCOUNTS = []
VIDEO_COUNT_PER_PAGE = 5
TOTAL_VIDEO_COUNT = 0
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""


# 获取指定一页的视频信息
def get_one_page_video(account_id, page_time):
    video_pagination_url = "http://wsm.qq.com/weishi/t/other.php?uid=%s&reqnum=%s" % (account_id, VIDEO_COUNT_PER_PAGE)
    if page_time > 0:
        video_pagination_url += "&pageflag=02&pagetime=%s" % page_time
    else:
        video_pagination_url += "&pageflag=0"
    result = {
        "is_error": False,  # 是不是格式不符合
        "is_over": False,  # 是不是最后一页视频
        "video_info_list": [],  # 全部视频信息
    }
    header_list = {"Referer": "http://weishi.qq.com/"}
    video_pagination_response = net.http_request(video_pagination_url, header_list=header_list, json_decode=True)
    if video_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(video_pagination_response.status))
    if not robot.check_sub_key(("ret",), video_pagination_response.json_data):
        raise robot.RobotException("返回信息'ret'字段不存在\n%s" % video_pagination_response.json_data)
    if int(video_pagination_response.json_data["ret"]) != 0:
        if int(video_pagination_response.json_data["ret"]) == -6:
            raise robot.RobotException("账号不存在")
        else:
            raise robot.RobotException("返回信息'ret'字段取值不正确\n%s" % video_pagination_response.json_data)
    if not robot.check_sub_key(("data",), video_pagination_response.json_data):
        raise robot.RobotException("返回信息'data'字段不存在\n%s" % video_pagination_response.json_data)
    if not robot.check_sub_key(("info", "hasNext"), video_pagination_response.json_data["data"]):
        raise robot.RobotException("返回信息'info'或'hasNext'字段不存在\n%s" % video_pagination_response.json_data)
    for video_info in video_pagination_response.json_data["data"]["info"]:
        result_video_info = {
            "video_id": None,  # 视频id
            "video_part_id_list": [],  # 视频分集id
            "video_time": None,  # 视频上传时间
        }
        # 获取视频id
        if not robot.check_sub_key(("id",), video_info):
            raise robot.RobotException("视频信息'id'字段不存在\n%s" % video_info)
        result_video_info["video_id"] = str(video_info["id"])
        # 获取分集id
        if not robot.check_sub_key(("newvideos",), video_info):
            raise robot.RobotException("视频信息'newvideos'字段不存在\n%s" % video_info)
        if not isinstance(video_info["newvideos"], list):
            raise robot.RobotException("视频信息'newvideos'字段类型不正确\n%s" % video_info)
        if len(video_info["newvideos"]) == 0:
            raise robot.RobotException("视频信息'newvideos'字段长度不正确\n%s" % video_info)
        for video_part_info in video_info["newvideos"]:
            if not robot.check_sub_key(("vid",), video_part_info):
                raise robot.RobotException("视频分集信息'vid'字段不存在\n%s" % video_info)
            result_video_info["video_part_id_list"].append(str(video_part_info["vid"]))
        # 获取视频id
        if not robot.check_sub_key(("timestamp",), video_info):
            raise robot.RobotException("视频信息'timestamp'字段不存在\n%s" % video_info)
        if not robot.is_integer(video_info["timestamp"]):
            raise robot.RobotException("视频信息'timestamp'字段类型不正确\n%s" % video_info)
        result_video_info["video_time"] = int(video_info["timestamp"])
        result["video_info_list"].append(result_video_info)
    # 检测是否还有下一页
    result["is_over"] = bool(video_pagination_response.json_data["data"]["hasNext"])
    return result


# 根据视频id和vid获取视频下载地址
def get_video_info_page(video_vid, video_id):
    video_info_url = "http://wsi.weishi.com/weishi/video/downloadVideo.php?vid=%s&id=%s" % (video_vid, video_id)
    video_info_response = net.http_request(video_info_url, json_decode=True)
    result = {
        "is_error": False,  # 是不是格式不符合
        "video_url": "",  # 视频地址
    }
    if video_info_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(video_info_response.status))
    if not robot.check_sub_key(("data",), video_info_response.json_data):
        raise robot.RobotException("返回信息'data'字段不存在\n%s" % video_info_response.json_data)
    if not robot.check_sub_key(("url",), video_info_response.json_data["data"]):
        raise robot.RobotException("返回信息'url'字段不存在\n%s" % video_info_response.json_data)
    result["video_url"] = str(random.choice(video_info_response.json_data["data"]["url"]))
    return result


class WeiShi(robot.Robot):
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
        # account_id  video_count  last_video_time
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0"])
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
        temp_path_list = []

        try:
            log.step(account_name + " 开始")

            page_time = 0
            video_info_list = []
            is_over = False
            # 获取全部还未下载过需要解析的视频
            while not is_over:
                log.step(account_name + " 开始解析%s后的一页视频" % page_time)

                # 获取一页视频信息
                try:
                    video_pagination_response = get_one_page_video(account_id, page_time)
                except robot.RobotException, e:
                    log.error(account_name + " %s后的一页视频解析失败，原因：%s" % (page_time, e.message))
                    raise

                log.step(account_name + " %s后一页解析的全部视频：%s" % (page_time, video_pagination_response["video_info_list"]))

                # 寻找这一页符合条件的视频
                for video_info in video_pagination_response["video_info_list"]:
                    # 检查是否达到存档记录
                    if video_info["video_time"] > int(self.account_info[2]):
                        video_info_list.append(video_info)
                        # 设置下一页指针
                        page_time = video_info["video_time"]
                    else:
                        is_over = True
                        break

                if not is_over:
                    if video_pagination_response["is_over"]:
                        is_over = True

            # 从最早的视频开始下载
            while len(video_info_list) > 0:
                video_info = video_info_list.pop()
                video_index = int(self.account_info[1]) + 1
                # 单个视频存在多个分集
                for video_part_id in video_info["video_part_id_list"]:
                    log.step(account_name + " 开始解析视频%s" % video_part_id)
                    # 获取视频下载地址
                    try:
                        video_info_response = get_video_info_page(video_part_id, video_info["video_id"])
                    except robot.RobotException, e:
                        log.error(account_name + " 视频%s（%s）解析失败，原因：%s" % (video_part_id, video_info["video_id"], e.message))
                        raise
                    log.step(account_name + " 开始下载第%s个视频 %s" % (video_index, video_info_response["video_url"]))

                    file_type = video_info_response["video_url"].split(".")[-1].split("?")[0]
                    file_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name, "%04d.%s" % (video_index, file_type))
                    save_file_return = net.save_net_file(video_info_response["video_url"], file_path)
                    if save_file_return["status"] == 1:
                        temp_path_list.append(file_path)
                        log.step(account_name + " 第%s个视频下载成功" % video_index)
                        video_index += 1
                    else:
                        log.error(account_name + " 第%s个视频 %s 下载失败" % (video_index, video_info_response["video_url"]))
                # 视频全部下载完毕
                temp_path_list = []  # 临时目录设置清除
                total_video_count += (video_index - 1) - int(self.account_info[1])  # 计数累加
                self.account_info[1] = str(video_index - 1)  # 设置存档记录
                self.account_info[2] = str(video_info["video_time"])
        except SystemExit, se:
            if se.code == 0:
                log.step(account_name + " 提前退出")
            else:
                log.error(account_name + " 异常退出")
            # 如果临时目录变量不为空，表示某个视频正在下载中，需要把下载了部分的内容给清理掉
            if len(temp_path_list) > 0:
                for temp_path in temp_path_list:
                    tool.delete_dir_or_file(temp_path)
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
    WeiShi().main()
