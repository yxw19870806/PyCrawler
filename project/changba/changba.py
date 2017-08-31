# -*- coding:UTF-8  -*-
"""
唱吧歌曲爬虫
http://changba.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import base64
import os
import re
import threading
import time
import traceback

ACCOUNTS = []
TOTAL_VIDEO_COUNT = 0
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""


# 获取账号首页页面
def get_account_index_page(account_id):
    account_index_url = "http://changba.com/u/%s" % account_id
    account_index_response = net.http_request(account_index_url, redirect=False)
    result = {
        "user_id": None,  # user id
    }
    if account_index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 获取user id
        user_id = tool.find_sub_string(account_index_response.data, "var userid = '", "'")
        if not robot.is_integer(user_id):
            raise robot.RobotException("页面截取userid失败\n%s" % account_index_response.data)
        result["user_id"] = str(user_id)
    elif account_index_response.status == 302 and account_index_response.getheader("Location") == "http://changba.com":
        raise robot.RobotException("账号不存在")
    else:
        raise robot.RobotException(robot.get_http_request_failed_reason(account_index_response.status))
    return result


# 获取指定页数的全部歌曲信息
# user_id -> 4306405
def get_one_page_audio(user_id, page_count):
    # http://changba.com/member/personcenter/loadmore.php?userid=4306405&pageNum=1
    audit_pagination_url = "http://changba.com/member/personcenter/loadmore.php?userid=%s&pageNum=%s" % (user_id, page_count - 1)
    audit_pagination_response = net.http_request(audit_pagination_url, json_decode=True)
    result = {
        "audio_info_list": [],  # 全部歌曲信息
    }
    if audit_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(audit_pagination_response.status))
    for audio_info in audit_pagination_response.json_data:
        extra_audio_info = {
            "audio_id": None,  # 歌曲id
            "audio_title": "",  # 歌曲标题
            "audio_key": None,  # 歌曲唯一key
            "type": None,  # 歌曲类型，0 MV，1/3 歌曲
        }
        # 获取歌曲id
        if not robot.check_sub_key(("workid",), audio_info):
            raise robot.RobotException("歌曲信息'workid'字段不存在\n%s" % audio_info)
        if not robot.is_integer(audio_info["workid"]):
            raise robot.RobotException("歌曲信息'workid'字段类型不正确\n%s" % audio_info)
        extra_audio_info["audio_id"] = str(audio_info["workid"])
        # 获取歌曲标题
        if not robot.check_sub_key(("songname",), audio_info):
            raise robot.RobotException("歌曲信息'songname'字段不存在\n%s" % audio_info)
        extra_audio_info["audio_title"] = str(audio_info["songname"].encode("UTF-8"))
        # 获取歌曲key
        if not robot.check_sub_key(("enworkid",), audio_info):
            raise robot.RobotException("歌曲信息'enworkid'字段不存在\n%s" % audio_info)
        extra_audio_info["audio_key"] = str(audio_info["enworkid"])
        # 获取歌曲类型
        if not robot.check_sub_key(("type",), audio_info):
            raise robot.RobotException("歌曲信息'type'字段不存在\n%s" % audio_info)
        if not robot.is_integer(audio_info["type"]):
            raise robot.RobotException("歌曲信息'type'字段类型不正确\n%s" % audio_info)
        if int(audio_info["type"]) not in (0, 1, 3):
            raise robot.RobotException("歌曲信息'type'字段范围不正确\n%s" % audio_info)
        extra_audio_info["type"] = int(audio_info["type"])
        result["audio_info_list"].append(extra_audio_info)
    return result


# 获取指定id的歌曲播放页
# audio_en_word_id => w-ptydrV23KVyIPbWPoKsA
def get_audio_play_page(audio_en_word_id, audio_type):
    audio_play_url = "http://changba.com/s/%s" % audio_en_word_id
    result = {
        "audio_url": None,  # 歌曲地址
        "is_delete": False,  # 是不是已经被删除
    }
    audio_play_response = net.http_request(audio_play_url)
    if audio_play_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(audio_play_response.status))
    if audio_play_response.data.find("该作品可能含有不恰当内容将不能显示。") > -1:
        result["is_delete"] = True
    else:
        # 获取歌曲地址
        if audio_type == 1 or audio_type == 3:
            audio_source_url = tool.find_sub_string(audio_play_response.data, 'var a="', '"')
            if not audio_source_url:
                raise robot.RobotException("页面截取歌曲原始地址失败\n%s" % audio_play_response.data)
            # 从JS处解析的规则
            special_find = re.findall("userwork/([abc])(\d+)/(\w+)/(\w+)\.mp3", audio_source_url)
            if len(special_find) == 0:
                result["audio_url"] = str(audio_source_url)
            elif len(special_find) == 1:
                e = int(special_find[0][1], 8)
                f = int(special_find[0][2], 16) / e / e
                g = int(special_find[0][3], 16) / e / e
                if "a" == special_find[0][0] and g % 1000 == f:
                    result["audio_url"] = "http://a%smp3.changba.com/userdata/userwork/%s/%g.mp3" % (e, f, g)
                else:
                    result["audio_url"] = "http://aliuwmp3.changba.com/userdata/userwork/%s.mp3" % g
            else:
                raise robot.RobotException("歌曲原始地址解密歌曲地址失败\n%s" % audio_source_url)
        # MV
        else:
            video_source_string = tool.find_sub_string(audio_play_response.data, "<script>jwplayer.utils.qn = '", "';</script>")
            if not video_source_string:
                raise robot.RobotException("页面截取歌曲加密地址失败\n%s" % audio_play_response.data)
            try:
                video_url = base64.b64decode(video_source_string)
            except TypeError:
                raise robot.RobotException("歌曲加密地址解密失败\n%s" % video_source_string)
            result["audio_url"] = video_url
    return result


class ChangBa(robot.Robot):
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
        total_video_count = 0

        try:
            log.step(account_name + " 开始")

            # 查找账号user id
            try:
                account_index_response = get_account_index_page(account_id)
            except robot.RobotException, e:
                log.error(account_name + " 主页解析失败，原因：%s" % e.message)
                raise

            page_count = 1
            unique_list = []
            audio_info_list = []
            is_over = False
            # 获取全部还未下载过需要解析的歌曲
            while not is_over:
                log.step(account_name + " 开始解析第%s页歌曲" % page_count)

                # 获取一页歌曲
                try:
                    audit_pagination_response = get_one_page_audio(account_index_response["user_id"], page_count)
                except robot.RobotException, e:
                    log.error(account_name + " 第%s页歌曲解析失败，原因：%s" % (page_count, e.message))
                    raise

                # 如果为空，表示已经取完了
                if len(audit_pagination_response["audio_info_list"]) == 0:
                    break

                log.trace(account_name + " 第%s页解析的全部歌曲：%s" % (page_count, audit_pagination_response["audio_info_list"]))

                # 寻找这一页符合条件的歌曲
                for audio_info in audit_pagination_response["audio_info_list"]:
                    # 新增歌曲导致的重复判断
                    if audio_info["audio_id"] in unique_list:
                        continue
                    else:
                        unique_list.append(audio_info["audio_id"])

                    # 检查是否达到存档记录
                    if int(audio_info["audio_id"]) > int(self.account_info[1]):
                        audio_info_list.append(audio_info)
                    else:
                        is_over = True
                        break

                if not is_over:
                    # 获取的歌曲数量少于1页的上限，表示已经到结束了
                    # 如果歌曲数量正好是页数上限的倍数，则由下一页获取是否为空判断
                    if len(audit_pagination_response["audio_info_list"]) < 20:
                        is_over = True
                    else:
                        page_count += 1

            log.step(account_name + " 需要下载的全部歌曲解析完毕，共%s首" % len(audio_info_list))

            # 从最早的歌曲开始下载
            while len(audio_info_list) > 0:
                audio_info = audio_info_list.pop()
                log.step(account_name + " 开始解析歌曲%s《%s》" % (audio_info["audio_key"], audio_info["audio_title"]))

                # 获取歌曲播放页
                try:
                    audio_play_response = get_audio_play_page(audio_info["audio_key"], audio_info["type"])
                except robot.RobotException, e:
                    log.error(account_name + " 歌曲%s《%s》解析失败，原因：%s" % (audio_info["audio_key"], audio_info["audio_title"], e.message))
                    raise

                if audio_play_response["is_delete"]:
                    log.error(account_name + " 歌曲%s《%s》异常，跳过" % (audio_info["audio_key"], audio_info["audio_title"]))
                    continue

                log.step(account_name + " 开始下载歌曲%s《%s》 %s" % (audio_info["audio_key"], audio_info["audio_title"], audio_play_response["audio_url"]))

                file_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name, "%s - %s.mp3" % (audio_info["audio_id"], robot.filter_text(audio_info["audio_title"])))
                save_file_return = net.save_net_file(audio_play_response["audio_url"], file_path)
                if save_file_return["status"] == 1:
                    log.step(account_name + " 歌曲%s《%s》下载成功" % (audio_info["audio_key"], audio_info["audio_title"]))
                else:
                    log.error(account_name + " 歌曲%s《%s》 %s 下载失败，原因：%s" % (audio_info["audio_key"], audio_info["audio_title"], audio_play_response["audio_url"], robot.get_save_net_file_failed_reason(save_file_return["code"])))
                # 歌曲下载完毕
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
        log.step(account_name + " 下载完毕，总共获得%s首歌曲" % total_video_count)


if __name__ == "__main__":
    ChangBa().main()
