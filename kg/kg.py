# -*- coding:UTF-8  -*-
"""
全面k歌歌曲爬虫
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, net, robot, tool
import os
import threading
import time
import traceback

ACCOUNTS = []
AUDIO_COUNT_PER_PAGE = 8
TOTAL_VIDEO_COUNT = 0
GET_VIDEO_COUNT = 0
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""


# 获取指定页数的一页歌曲信息
def get_one_page_audio(account_id, page_count):
    index_page_url = "http://kg.qq.com/cgi/kg_ugc_get_homepage?type=get_ugc&format=json&share_uid=%s&start=%s&num=%s" % (account_id, page_count, AUDIO_COUNT_PER_PAGE)
    index_page_response = net.http_request(index_page_url, json_decode=True)
    extra_info = {
        "audio_info_list": [],  # 页面解析出的歌曲信息列表
        "is_over": False,  # 是不是最后一页歌曲
    }
    if index_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if robot.check_sub_key(("data",), index_page_response.json_data) and robot.check_sub_key(("has_more", "ugclist"), index_page_response.json_data["data"]):
            for audio_info in index_page_response.json_data["data"]["ugclist"]:
                audio_extra_info = {
                    "audio_id": None,  # 页面解析出的歌曲id
                    "audio_key": None,  # 页面解析出的歌曲访问token
                    "audio_title": "",  # 页面解析出的歌曲标题
                    "audio_time": None,  # 页面解析出的歌曲上传时间
                    "json_data": audio_info,  # 原始数据
                }
                if robot.check_sub_key(("title", "shareid", "ksong_mid", "time"), audio_info):
                    audio_extra_info["audio_id"] = str(audio_info["ksong_mid"])
                    audio_extra_info["audio_key"] = str(audio_info["shareid"])
                    audio_extra_info["audio_title"] = str(audio_info["title"].encode("utf-8"))
                    if isinstance(audio_info["time"], int) or str(audio_info["time"]).isdigit():
                        audio_extra_info["audio_time"] = str(audio_info["time"])
                extra_info["audio_info_list"].append(audio_extra_info)
            extra_info["is_over"] = not bool(int(index_page_response.json_data["data"]["has_more"]))
    index_page_response.extra_info = extra_info
    return index_page_response


# 获取歌曲播放地址
def get_audio_play_page(audio_id):
    audio_play_page_url = "http://kg.qq.com/node/play?s=%s" % audio_id
    audio_play_page_response = net.http_request(audio_play_page_url)
    extra_info = {
        "audio_url": None,  # 页面解析出的歌曲地址
    }
    if audio_play_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        audio_url = tool.find_sub_string(audio_play_page_response.data, '"playurl":"', '"')
        if audio_url:
            extra_info["audio_url"] = audio_url
        else:
            audio_url = tool.find_sub_string(audio_play_page_response.data, '"playurl_video":"', '"')
            if audio_url:
                extra_info["audio_url"] = audio_url
    audio_play_page_response.extra_info = extra_info
    return audio_play_page_response


class KG(robot.Robot):
    def __init__(self):
        global GET_VIDEO_COUNT
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH

        sys_config = {
            robot.SYS_DOWNLOAD_VIDEO: True,
        }
        robot.Robot.__init__(self, sys_config, use_urllib3=True)

        # 设置全局变量，供子线程调用
        GET_VIDEO_COUNT = self.get_video_count
        VIDEO_DOWNLOAD_PATH = self.video_download_path
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

    def main(self):
        global ACCOUNTS

        # 解析存档文件
        # account_id
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

        # 删除临时文件夹
        self.finish_task()

        # 重新排序保存存档文件
        robot.rewrite_save_file(NEW_SAVE_DATA_PATH, self.save_data_path)

        log.step("全部下载完毕，耗时%s秒，共计歌曲%s首" % (self.get_run_time(), TOTAL_VIDEO_COUNT))


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

        try:
            log.step(account_name + " 开始")

            video_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)

            # 歌曲
            video_count = 1
            page_count = 1
            first_audio_time = "0"
            unique_list = []
            need_make_download_dir = True
            is_over = False
            while not is_over:
                log.step(account_name + " 开始解析第%s页歌曲" % page_count)

                # 获取一页歌曲
                index_page_response = get_one_page_audio(account_id, page_count)
                if index_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                    log.error(account_name + " 第%s页歌曲访问失败，原因：%s" % (page_count, robot.get_http_request_failed_reason(index_page_response.status)))
                    tool.process_exit()

                for audio_info in index_page_response.extra_info["audio_info_list"]:
                    if audio_info["audio_id"] is None:
                        log.error(account_name + " 歌曲信息%s的歌曲id解析失败" % audio_info["json_data"])
                        tool.process_exit()

                    if audio_info["audio_time"] is None:
                        log.error(account_name + " 歌曲信息%s的歌曲时间解析失败" % audio_info["json_data"])
                        tool.process_exit()

                    # 检查是否已下载到前一次的歌曲
                    if int(audio_info["audio_time"]) <= int(self.account_info[1]):
                        is_over = True
                        break

                    # 将第一首歌曲的id做为新的存档记录
                    if first_audio_time == "0":
                        first_audio_time = audio_info["audio_time"]

                    # 新增歌曲导致的重复判断
                    if audio_info["audio_id"] in unique_list:
                        continue
                    else:
                        unique_list.append(audio_info["audio_id"])

                    # 获取歌曲播放页
                    audio_play_page_response = get_audio_play_page(audio_info["audio_key"])
                    if audio_play_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                        log.error(account_name + " 歌曲%s《%s》播放页面访问失败，原因：%s" % (audio_info["audio_id"], audio_info["audio_title"], robot.get_http_request_failed_reason(audio_play_page_response.status)))
                        continue

                    if audio_play_page_response.extra_info["audio_url"] is None:
                        log.error(account_name + " 歌曲%s《%s》下载地址解析失败" % (audio_info["audio_key"], audio_info["audio_title"]))
                        continue

                    audio_url = audio_play_page_response.extra_info["audio_url"]
                    log.step(account_name + " 开始下载第%s首歌曲《%s》 %s" % (video_count, audio_info["audio_title"], audio_url))

                    # 第一首歌曲，创建目录
                    if need_make_download_dir:
                        if not tool.make_dir(video_path, 0):
                            log.error(account_name + " 创建歌曲下载目录 %s 失败" % video_path)
                            tool.process_exit()
                        need_make_download_dir = False

                    file_type = audio_url.split(".")[-1].split("?")[0]
                    file_path = os.path.join(video_path, "%s - %s.%s" % (audio_info["audio_id"], audio_info["audio_title"], file_type))
                    save_file_return = net.save_net_file(audio_url, file_path)
                    if save_file_return["status"] == 1:
                        log.step(account_name + " 第%s首歌曲下载成功" % video_count)
                        video_count += 1
                    else:
                        log.error(account_name + " 第%s首歌曲《%s》 %s 下载失败，原因：%s" % (video_count, audio_info["audio_title"], audio_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

                    # 达到配置文件中的下载数量，结束
                    if 0 < GET_VIDEO_COUNT < video_count:
                        is_over = True
                        break

                if index_page_response.extra_info["is_over"]:
                    is_over = True
                else:
                    page_count += 1

            log.step(account_name + " 下载完毕，总共获得%s首歌曲" % (video_count - 1))

            # 新的存档记录
            if first_audio_time != "0":
                self.account_info[1] = first_audio_time

            # 保存最后的信息
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            self.thread_lock.acquire()
            TOTAL_VIDEO_COUNT += video_count - 1
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
    KG().main()
