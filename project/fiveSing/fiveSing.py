# -*- coding:UTF-8  -*-
"""
5sing歌曲爬虫
http://5sing.kugou.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import base64
import json
import os
import re
import threading
import time
import traceback

ACCOUNTS = []
TOTAL_VIDEO_COUNT = 0
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""


# 获取指定页数的所有歌曲
# page_type 页面类型：yc - 原唱、fc - 翻唱
# account_id -> inory
def get_one_page_audio(account_id, page_type, page_count):
    # http://5sing.kugou.com/inory/yc/1.html
    audio_pagination_url = "http://5sing.kugou.com/%s/%s/%s.html" % (account_id, page_type, page_count)
    audio_pagination_response = net.http_request(audio_pagination_url)
    extra_info = {
        "audio_info_list": [],  # 所有歌曲信息
    }
    if audio_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 获取歌曲信息
        # 单首歌曲信息的格式：[歌曲id，歌曲标题]
        audio_info_list = re.findall('<a href="http://5sing.kugou.com/' + page_type + '/([\d]*).html" [\s|\S]*? title="([^"]*)">', audio_pagination_response.data)
        extra_info["audio_info_list"] = [map(str, key) for key in audio_info_list]
    else:
        raise robot.RobotException(robot.get_http_request_failed_reason(audio_pagination_response.status))
    audio_pagination_response.extra_info = extra_info
    return audio_pagination_response


# 获取指定id的歌曲播放页
def get_audio_play_page(audio_id, song_type):
    audio_play_url = "http://5sing.kugou.com/%s/%s.html" % (song_type, audio_id)
    audio_play_response = net.http_request(audio_play_url)
    extra_info = {
        "audio_url": None,  # 歌曲地址
    }
    if audio_play_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 获取歌曲地址
        audio_info_string = tool.find_sub_string(audio_play_response.data, '"ticket":', ",").strip().strip('"')
        if not audio_info_string:
            raise robot.RobotException("页面截取歌曲加密地址失败\n%s" % audio_play_response.data)
        try:
            audio_info = json.loads(base64.b64decode(audio_info_string))
        except TypeError:
            raise robot.RobotException("歌曲加密地址解密失败\n%s" % audio_info_string)
        except ValueError:
            raise robot.RobotException("歌曲加密地址解密失败\n%s" % audio_info_string)
        if not robot.check_sub_key(("file",), audio_info):
            raise robot.RobotException("歌曲信息'file'字段不存在\n%s" % audio_info)
        extra_info["audio_url"] = str(audio_info["file"])
    else:
        raise robot.RobotException(robot.get_http_request_failed_reason(audio_play_response.status))
    audio_play_response.extra_info = extra_info
    return audio_play_response


class FiveSing(robot.Robot):
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
        # account_id  last_yc_audio_id  last_fc_audio_id
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
        if len(self.account_info) >= 4 and self.account_info[3]:
            account_name = self.account_info[3]
        else:
            account_name = self.account_info[0]

        # 原创、翻唱
        audio_type_to_index_dict = {"yc": 1, "fc": 2}  # 存档文件里的下标
        audio_type_name_dict = {"yc": "原唱", "fc": "翻唱"}  # 显示名字
        try:
            log.step(account_name + " 开始")

            video_count = 1
            for audio_type in audio_type_to_index_dict.keys():
                audio_type_index = audio_type_to_index_dict[audio_type]
                audio_type_name = audio_type_name_dict[audio_type]

                page_count = 1
                unique_list = []
                is_over = False
                first_audio_id = None
                video_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name, audio_type)
                while not is_over:
                    log.step(account_name + " 开始解析第%s页%s歌曲" % (page_count, audio_type_name))

                    # 获取一页歌曲
                    try:
                        audio_pagination_response = get_one_page_audio(account_id, audio_type, page_count)
                    except robot.RobotException, e:
                        log.error(account_name + " 第%s页%s歌曲解析失败，原因：%s" % (page_count, audio_type_name, e.message))
                        first_audio_id = None  # 存档恢复
                        break

                    # 如果为空，表示已经取完了
                    if len(audio_pagination_response.extra_info["audio_info_list"]) == 0:
                        break

                    log.trace(account_name + " 第%s页%s解析的所有歌曲：%s" % (page_count, audio_type_name, audio_pagination_response.extra_info["audio_info_list"]))

                    for audio_info in audio_pagination_response.extra_info["audio_info_list"]:
                        audio_id = audio_info[0]
                        # 过滤标题中不支持的字符
                        audio_title = robot.filter_text(audio_info[1])

                        # 检查是否达到存档记录
                        if int(audio_id) <= int(self.account_info[audio_type_index]):
                            is_over = True
                            break

                        # 新的存档记录
                        if first_audio_id is None:
                            first_audio_id = audio_id

                        # 新增歌曲导致的重复判断
                        if audio_id in unique_list:
                            continue
                        else:
                            unique_list.append(audio_id)

                        # 获取歌曲的详情页
                        try:
                            audio_play_response = get_audio_play_page(audio_id, audio_type)
                        except robot.RobotException, e:
                            log.error(account_name + " %s歌曲%s《%s》播放页访问失败，原因：%s" % (audio_type_name, audio_id, audio_title, e.message))
                            is_over = True
                            first_audio_id = None  # 存档恢复
                            break

                        log.step(account_name + " 开始下载第%s首%s歌曲《%s》 %s" % (video_count, audio_type_name, audio_title, audio_play_response.extra_info["audio_url"]))

                        file_path = os.path.join(video_path, "%s - %s.mp3" % (audio_id, audio_title))
                        save_file_return = net.save_net_file(audio_play_response.extra_info["audio_url"], file_path)
                        if save_file_return["status"] == 1:
                            log.step(account_name + " 第%s首%s歌曲下载成功" % (video_count, audio_type_name))
                            video_count += 1
                        else:
                            log.error(account_name + " 第%s首%s歌曲《%s》%s下载失败，原因：%s" % (video_count, audio_type_name, audio_title, audio_play_response.extra_info["audio_url"], robot.get_save_net_file_failed_reason(save_file_return["code"])))

                    if not is_over:
                        # 获取的歌曲数量少于1页的上限，表示已经到结束了
                        # 如果歌曲数量正好是页数上限的倍数，则由下一页获取是否为空判断
                        if len(audio_pagination_response.extra_info["audio_info_list"]) < 20:
                            is_over = True
                        else:
                            page_count += 1

                # 新的存档记录
                if first_audio_id is not None:
                    self.account_info[audio_type_index] = first_audio_id

            log.step(account_name + " 下载完毕，总共获得%s首歌曲" % (video_count - 1))

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
    FiveSing().main()
