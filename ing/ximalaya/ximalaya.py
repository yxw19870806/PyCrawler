# -*- coding:UTF-8  -*-
"""
喜马拉雅音频爬虫
http://www.ximalaya.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
from pyquery import PyQuery as pq
import os
import threading
import time
import traceback

ACCOUNTS = []
TOTAL_VIDEO_COUNT = 0
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""


# 获取指定页数的全部音频信息
def get_one_page_audio(account_id, page_count):
    # http://www.ximalaya.com/1014267/index_tracks?page=2
    audit_pagination_url = "http://www.ximalaya.com/%s/index_tracks" % account_id
    query_data = {"page": page_count}
    audit_pagination_response = net.http_request(audit_pagination_url, method="GET", fields=query_data, json_decode=True)
    result = {
        "audio_info_list": [],  # 页面解析出的音频信息列表
    }
    if audit_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(audit_pagination_response.status))
    if not robot.check_sub_key(("res", "html"), audit_pagination_response.json_data):
        raise robot.RobotException("返回数据'res'或'html'字段不存在\n%s" % audit_pagination_response.json_data)
    if audit_pagination_response.json_data["res"] is not True:
        raise robot.RobotException("返回数据'res'字段取值不正确\n%s" % audit_pagination_response.json_data)
    audio_list_selector = pq(audit_pagination_response.json_data["html"]).find("ul.body_list li.item")
    for audio_index in range(0, audio_list_selector.size()):
        audio_info = {
            "audio_id": None,  # 页面解析出的音频id
            "audio_title": "",  # 页面解析出的音频标题
        }
        audio_selector = audio_list_selector.eq(audio_index)
        # 获取音频id
        audio_id = audio_selector.find(".content_wrap").attr("sound_id")
        if not robot.is_integer(audio_id):
            raise robot.RobotException("音频信息匹配音频id失败\n%s" % audio_list_selector.html().encode("UTF-8"))
        audio_info["audio_id"] = str(audio_id)
        # 获取音频标题
        audio_title = audio_selector.find(".sound_title").attr("title")
        if not audio_title:
            raise robot.RobotException("音频信息匹配音频标题失败\n%s" % audio_list_selector.html().encode("UTF-8"))
        audio_info["audio_title"] = str(audio_title.encode("UTF-8").strip())
        result["audio_info_list"].append(audio_info)
    return result


# 获取指定id的音频播放页
# audio_id -> 16558983
def get_audio_info_page(audio_id):
    audio_info_url = "http://www.ximalaya.com/tracks/%s.json" % audio_id
    result = {
        "audio_url": None,  # 页面解析出的音频地址
    }
    audio_play_response = net.http_request(audio_info_url, method="GET", json_decode=True)
    if audio_play_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        print audio_play_response.json_data
    return result


class XiMaLaYa(robot.Robot):
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
        # account_id  last_audio_id
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

        log.step("全部下载完毕，耗时%s秒，共计音频%s首" % (self.get_run_time(), TOTAL_VIDEO_COUNT))


class Download(threading.Thread):
    def __init__(self, account_info, thread_lock):
        threading.Thread.__init__(self)
        self.account_info = account_info
        self.thread_lock = thread_lock

    def run(self):
        global TOTAL_VIDEO_COUNT

        account_id = self.account_info[0]
        if len(self.account_info) >= 3 and self.account_info[2]:
            account_name = self.account_info[2]
        else:
            account_name = self.account_info[0]
        total_video_count = 0

        try:
            log.step(account_name + " 开始")

            page_count = 1
            unique_list = []
            audio_info_list = []
            is_over = False
            # 获取全部还未下载过需要解析的音频
            while not is_over:
                log.step(account_name + " 开始解析第%s页音频" % page_count)

                # 获取一页音频
                try:
                    audit_pagination_response = get_one_page_audio(account_id, page_count)
                except robot.RobotException, e:
                    log.error("第%s页音频解析失败，原因：%s" % (page_count, e.message))
                    break

                # 如果为空，表示已经取完了
                if len(audit_pagination_response["audio_info_list"]) == 0:
                    break

                log.trace(account_name + " 第%s页解析的全部音频：%s" % (page_count, audit_pagination_response["audio_info_list"]))

                # 寻找这一页符合条件的媒体
                for audio_info in audit_pagination_response["audio_info_list"]:
                    # 新增音频导致的重复判断
                    if audio_info["audio_id"] in unique_list:
                        continue
                    else:
                        unique_list.append(audio_info["audio_id"])

                    # 检查是否达到存档记录
                    if audio_info["audio_id"] > int(self.account_info[1]):
                        audio_info_list.append(audio_info)
                    else:
                        is_over = True
                        break

                if not is_over:
                    # 获取的音频数量少于1页的上限，表示已经到结束了
                    # 如果音频数量正好是页数上限的倍数，则由下一页获取是否为空判断
                    if len(audit_pagination_response["audio_info_list"]) < 20:
                        is_over = True
                    else:
                        page_count += 1

            log.step(account_name + " 需要下载的全部音频解析完毕，共%s个" % len(audio_info_list))

            # 从最早的媒体开始下载
            while len(audio_info_list) > 0:
                audio_info = audio_info_list.pop()
                log.step(account_name + " 开始解析音频%s" % audio_info["audio_id"])

                # 获取音频播放页
                try:
                    audio_play_response = get_audio_info_page(audio_info["audio_id"])
                except robot.RobotException, e:
                    log.error("音频%s解析失败，原因：%s" % (page_count, e.message))
                    break

                audio_url = audio_play_response["audio_url"]
                audio_title = robot.filter_text(audio_info["audio_title"])
                log.step(account_name + " 开始下载音频%s《%s》 %s" % (audio_info["audio_id"], audio_title, audio_url))

                file_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name, "%s - %s.mp3" % (audio_info["audio_id"], audio_title))
                save_file_return = net.save_net_file(audio_url, file_path)
                if save_file_return["status"] == 1:
                    log.step(account_name + " 音频%s《%s》下载成功" % (audio_info["audio_id"], audio_title))
                else:
                    log.error(account_name + " 音频%s《%s》 %s 下载失败，原因：%s" % (audio_info["audio_id"], audio_title, audio_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
                    continue
                # 音频下载完毕
                total_video_count += 1  # 计数累加
                self.account_info[1] = audio_info["audio_id"]  # 设置存档记录
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
        log.step(account_name + " 下载完毕，总共获得%s首音频" % total_video_count)


if __name__ == "__main__":
    XiMaLaYa().main()
