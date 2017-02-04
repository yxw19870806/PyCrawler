# -*- coding:UTF-8  -*-
"""
5sing歌曲爬虫
http://5sing.kugou.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, net, robot, tool
import os
import re
import threading
import time
import traceback

ACCOUNTS = []
TOTAL_VIDEO_COUNT = 0
GET_VIDEO_COUNT = 0
GET_PAGE_COUNT = 0
VIDEO_TEMP_PATH = ""
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
COOKIE_INFO = {"5sing_auth": ""}


# 获取指定页数的所有歌曲
# page_type 页面类型：yc - 原唱、fc - 翻唱
# account_id -> inory
def get_one_page_audio(account_id, page_type, page_count):
    # http://5sing.kugou.com/inory/yc/1.html
    index_page_url = "http://5sing.kugou.com/%s/%s/%s.html" % (account_id, page_type, page_count)
    index_page_response = net.http_request(index_page_url)
    extra_info = {
        "audio_info_list": [],  # 页面解析出的歌曲信息列表
    }
    if index_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 获取页面中所有的歌曲信息列表
        # 单首歌曲信息的格式：[歌曲id，歌曲标题]
        audio_info_list = re.findall('<a href="http://5sing.kugou.com/' + page_type + '/([\d]*).html" [\s|\S]*? title="([^"]*)">', index_page_response.data)
        extra_info["audio_info_list"] = [map(str, key) for key in audio_info_list]
    index_page_response.extra_info = extra_info
    return index_page_response


# 获取指定id的歌曲详情页
def get_audio_info_page(audio_id, song_type):
    # http://service.5sing.kugou.com/song/getPermission?songId=15663426&songType=fc
    audio_info_page_url = "http://service.5sing.kugou.com/song/getPermission?songId=%s&songType=%s" % (audio_id, song_type)
    header_list = {"Cookie": "5sing_auth=%s" % COOKIE_INFO["5sing_auth"]}
    audio_info_page_response = net.http_request(audio_info_page_url, header_list=header_list, json_decode=True)
    extra_info = {
        "audio_url": None,  # 页面解析出的歌曲下载地址
    }
    if audio_info_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if robot.check_sub_key(("data",), audio_info_page_response.json_data) and robot.check_sub_key(("fileName",), audio_info_page_response.json_data["data"]):
            extra_info["audio_url"] = str(audio_info_page_response.json_data["data"]["fileName"])
    audio_info_page_response.extra_info = extra_info
    return audio_info_page_response


class FiveSing(robot.Robot):
    def __init__(self):
        global GET_VIDEO_COUNT
        global GET_PAGE_COUNT
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global COOKIE_INFO

        sys_config = {
            robot.SYS_DOWNLOAD_VIDEO: True,
            robot.SYS_GET_COOKIE: {".kugou.com": ("5sing_auth",)},
        }
        robot.Robot.__init__(self, sys_config, use_urllib3=True)

        # 设置全局变量，供子线程调用
        GET_VIDEO_COUNT = self.get_video_count
        GET_PAGE_COUNT = self.get_page_count
        VIDEO_DOWNLOAD_PATH = self.video_download_path
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)
        COOKIE_INFO["5sing_auth"] = self.cookie_value["5sing_auth"]

    def main(self):
        global ACCOUNTS

        if not COOKIE_INFO["5sing_auth"]:
            log.error("cookie获取失败，请查看浏览器内的登录状态")
            tool.process_exit()

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
        global GET_PAGE_COUNT

        account_id = self.account_info[0]
        if len(self.account_info) >= 4 and self.account_info[3]:
            account_name = self.account_info[3]
        else:
            account_name = self.account_info[0]

        # 原创、翻唱
        audio_type_to_index = {"yc": 1, "fc": 2}  # 存档文件里的下标
        audio_type_name = {"yc": "原唱", "fc": "翻唱"}  # 显示名字
        try:
            log.step(account_name + " 开始")

            video_count = 1
            for audio_type in audio_type_to_index.keys():
                video_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name, audio_type)

                page_count = 1
                first_audio_id = "0"
                unique_list = []
                is_over = False
                need_make_download_dir = True
                while not is_over:
                    log.step(account_name + " 开始解析第%s页歌曲" % page_count)

                    # 获取一页歌曲
                    index_page_response = get_one_page_audio(account_id, audio_type, page_count)
                    if index_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                        log.error(account_name + " 第%s页%s歌曲访问失败，原因：%s" % (page_count, audio_type_name[audio_type], robot.get_http_request_failed_reason(index_page_response.status)))
                        first_audio_id = "0"  # 存档恢复
                        break

                    # 如果为空，表示已经取完了
                    if len(index_page_response.extra_info["audio_info_list"]) == 0:
                        break

                    log.trace(account_name + " 第%s页%s歌曲解析的所有歌曲：%s" % (page_count, audio_type_name[audio_type], index_page_response.extra_info["audio_info_list"]))

                    for audio_info in index_page_response.extra_info["audio_info_list"]:
                        audio_id = audio_info[0]
                        # 过滤标题中不支持的字符
                        audio_title = robot.filter_text(audio_info[1])

                        # 检查是否已下载到前一次的歌曲
                        if int(audio_id) <= int(self.account_info[audio_type_to_index[audio_type]]):
                            is_over = True
                            break

                        # 将第一首歌曲的id做为新的存档记录
                        if first_audio_id == "0":
                            first_audio_id = audio_id

                        # 新增歌曲导致的重复判断
                        if audio_id in unique_list:
                            continue
                        else:
                            unique_list.append(audio_id)

                        # 获取歌曲的详情页
                        audio_info_page_response = get_audio_info_page(audio_id, audio_type_to_index[audio_type])
                        if audio_info_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                            log.error(account_name + " %s歌曲%s《%s》详情页访问失败，原因：%s" % (audio_type_name[audio_type], audio_id, audio_title, robot.get_http_request_failed_reason(index_page_response.status)))
                            continue

                        # 获取歌曲
                        audio_url = audio_info_page_response.extra_info["audio_url"]
                        if not audio_url:
                            log.step(account_name + " %s歌曲%s《%s》暂不提供下载地址" % (audio_type_name[audio_type], audio_id, audio_title))
                            continue

                        log.step(account_name + " 开始下载第%s首%s歌曲《%s》%s" % (video_count, audio_type_name[audio_type], audio_title, audio_url))

                        # 第一首歌曲，创建目录
                        if need_make_download_dir:
                            if not tool.make_dir(video_path, 0):
                                log.error(account_name + " 创建%s歌曲下载目录 %s 失败" % (audio_type_name[audio_type], video_path))
                                tool.process_exit()
                            need_make_download_dir = False

                        file_path = os.path.join(video_path, "%s - %s.mp3" % (audio_id, audio_title))
                        save_file_return = net.save_net_file(audio_url, file_path)
                        if save_file_return["status"] == 1:
                            log.step(account_name + " 第%s首%s歌曲下载成功" % (video_count, audio_type_name[audio_type]))
                            video_count += 1
                        else:
                            log.error(account_name + " 第%s首%s歌曲《%s》%s下载失败，原因：%s" % (video_count, audio_type_name[audio_type], audio_title, audio_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

                        # 达到配置文件中的下载数量，结束
                        if 0 < GET_VIDEO_COUNT < video_count:
                            is_over = True
                            break

                    if not is_over:
                        # 达到配置文件中的下载页数，结束
                        if 0 < GET_PAGE_COUNT <= page_count:
                            is_over = True
                        # 获取的歌曲数量少于1页的上限，表示已经到结束了
                        # 如果歌曲数量正好是页数上限的倍数，则由下一页获取是否为空判断
                        elif len(index_page_response.extra_info["audio_info_list"]) < 20:
                            is_over = True
                        else:
                            page_count += 1

                # 新的存档记录
                if first_audio_id != "0":
                    self.account_info[audio_type_to_index[audio_type]] = first_audio_id

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
