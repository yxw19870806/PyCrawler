# -*- coding:UTF-8  -*-
"""
Youtube视频爬虫
https://www.youtube.com
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import json
import os
import threading
import time
import traceback
import urllib

ACCOUNT_LIST = {}
TOTAL_VIDEO_COUNT = 0
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
COOKIE_INFO = {}


# 获取用户首页
def get_one_page_video(account_id, token):
    # token = "4qmFsgJAEhhVQ2xNXzZHRU9razY2STFfWWJTUFFqSWcaJEVnWjJhV1JsYjNNZ0FEZ0JZQUZxQUhvQk1yZ0JBQSUzRCUzRA%3D%3D"
    result = {
        "video_id_list": [],  # 全部视频id
        "next_page_token": None,  # 下一页token
    }
    if token == "":
        # todo 更好的分辨方法
        if len(account_id) == 24:
            index_url = "https://www.youtube.com/channel/%s/videos" % account_id
        else:
            index_url = "https://www.youtube.com/user/%s/videos" % account_id
        index_response = net.http_request(index_url, method="GET")
        if index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
            raise robot.RobotException(robot.get_http_request_failed_reason(index_response.status))
        script_data_html = tool.find_sub_string(index_response.data, 'window["ytInitialData"] =', ";\n").strip()
        if not script_data_html:
            raise robot.RobotException("页面截取视频信息失败\n%s" % index_response.data)
        try:
            script_data = json.loads(script_data_html)
        except ValueError:
            raise robot.RobotException("视频信息加载失败\n%s" % script_data_html)
        try:
            temp_data = script_data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][1]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]
            video_list_data = temp_data["itemSectionRenderer"]["contents"][0]["gridRenderer"]
        except KeyError:
            raise robot.RobotException("视频信息格式不正确\n%s" % script_data)
    else:
        query_url = "https://www.youtube.com/browse_ajax"
        query_data = {"ctoken": token}
        header_list = {
            "x-youtube-client-name": "1",
            "x-youtube-client-version": "2.20171207",
        }
        video_pagination_response = net.http_request(query_url, method="GET", fields=query_data, header_list=header_list, json_decode=True)
        if video_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
            raise robot.RobotException(robot.get_http_request_failed_reason(video_pagination_response.status))
        try:
            video_list_data = video_pagination_response.json_data[1]["response"]["continuationContents"]["gridContinuation"]
        except KeyError:
            raise robot.RobotException("视频信息格式不正确\n%s" % video_pagination_response.json_data)
    if not robot.check_sub_key(("items",), video_list_data):
        raise robot.RobotException("视频列表信息'items'字段不存在\n%s" % video_list_data)
    for item in video_list_data["items"]:
        if not robot.check_sub_key(("gridVideoRenderer",), item):
            raise robot.RobotException("视频信息'gridVideoRenderer'字段不存在\n%s" % item)
        if not robot.check_sub_key(("videoId",), item["gridVideoRenderer"]):
            raise robot.RobotException("视频信息'gridVideoRenderer'字段不存在\n%s" % item)
        result["video_id_list"].append(str(item["gridVideoRenderer"]["videoId"]))
    # 获取下一页token
    try:
        result["next_page_token"] = str(video_list_data["continuations"][0]["nextContinuationData"]["continuation"])
    except KeyError:
        pass
    return result


# 获取指定视频
def get_video_page(video_id):
    # https://www.youtube.com/watch?v=GCOSw4WSXqU
    video_play_url = "https://www.youtube.com/watch"
    query_data = {"v": video_id}
    # 强制使用英语

    video_play_response = net.http_request(video_play_url, method="GET", fields=query_data, cookies_list=COOKIE_INFO)
    result = {
        "video_time": None,  # 视频上传时间
        "video_url": None,  # 视频地址
    }
    # 获取视频地址
    if video_play_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(video_play_response.status))
    video_info_string = tool.find_sub_string(video_play_response.data, "ytplayer.config = ", ";ytplayer.load = ").strip()
    if not video_info_string:
        raise robot.RobotException("页面截取视频信息失败\n%s" % video_play_response.data)
    try:
        video_info_data = json.loads(video_info_string)
    except KeyError:
        raise robot.RobotException("视频信息格式不正确\n%s" % video_info_string)
    if not robot.check_sub_key(("args",), video_info_data):
        raise robot.RobotException("视频信息'args'字段不存在\n%s" % video_info_data)
    if not robot.check_sub_key(("url_encoded_fmt_stream_map",), video_info_data["args"]):
        raise robot.RobotException("视频信息'url_encoded_fmt_stream_map'字段不存在\n%s" % video_info_data["args"])
    max_video_resolution = 0
    for sub_url_encoded_fmt_stream_map in video_info_data["args"]["url_encoded_fmt_stream_map"].split(","):
        video_resolution = video_url = signature = None
        is_skip = False
        for sub_param in sub_url_encoded_fmt_stream_map.split("&"):
            key, value = str(sub_param).split("=")
            if key == "type":  # 视频类型
                video_type = urllib.unquote(value)
                if video_type.find("video/mp4") == 0:
                    pass  # 只要mp4类型的
                elif video_type.find("video/webm") == 0 or video_type.find("video/3gpp") == 0:
                    is_skip = True  # 跳过
                    break
                else:
                    log.error("unknown video type " + video_type)
            elif key == "quality":  # 视频画质
                if value == "small":
                    video_resolution = 240
                elif value == "medium":
                    video_resolution = 360
                elif value[:2] == "hd" and robot.is_integer(value[2:]):
                    video_resolution = int(value[2:])
                else:
                    log.error("unknown video quality " + value)
            elif key == "url":
                video_url = urllib.unquote(value)
            elif key == "s":
                signature = decrypt_signature(value)
            elif key == "sig":
                signature = value
        if is_skip:
            continue
        if video_url is None or video_url is None:
            log.error("unknown video param" + video_info_string)
            continue
        if video_resolution > max_video_resolution:
            max_video_resolution = video_resolution
            if signature is not None:
                video_url += "&signature=" + str(signature)
            result["video_url"] = video_url
    if result["video_url"] is None:
        raise robot.RobotException("视频地址解析错误\n%s" % video_info_string)
    # 获取视频发布时间
    video_time_string = tool.find_sub_string(video_play_response.data, '"dateText":{"simpleText":"', '"},').strip()
    if not video_time_string:
        video_time_string = tool.find_sub_string(video_play_response.data, '<strong class="watch-time-text">', '</strong>').strip()
    if not video_time_string:
        raise robot.RobotException("页面截取视频发布时间错误\n%s" % video_play_response.data)
    # 英语
    if video_time_string.find("Published on") >= 0:
        video_time_string = video_time_string.replace("Published on", "").strip()
        try:
            video_time = time.strptime(video_time_string, "%b %d, %Y")
        except ValueError:
            raise robot.RobotException("视频发布时间文本格式不正确\n%s" % video_time_string)
    # 中文
    elif video_time_string.find("发布") >= 0:
        video_time_string = video_time_string.replace("发布", "").strip()
        try:
            video_time = time.strptime(video_time_string, "%Y年%m月%d日")
        except ValueError:
            raise robot.RobotException("视频发布时间文本格式不正确\n%s" % video_time_string)
    else:
        raise robot.RobotException("未知语言的时间格式\n%s" % video_time_string)
    result["video_time"] = int(time.mktime(video_time))
    return result


# 部分版权视频需要的signature字段取值
# 解析自/yts/jsbin/player-vfl4OEYh9/en_US/base.js文件中
# k.sig?f.set("signature",k.sig):k.s&&f.set("signature",SJ(k.s));
# SJ=function(a){a=a.split("");RJ.yF(a,48);RJ.It(a,31);RJ.yF(a,24);RJ.It(a,74);return a.join("")};
# var RJ={yF:function(a,b){var c=a[0];a[0]=a[b%a.length];a[b]=c},It:function(a){a.reverse()},yp:function(a,b){a.splice(0,b)}};
def decrypt_signature(s):
    a = list(s)
    _calc1(a, 48)
    _calc2(a, 31)
    _calc1(a, 24)
    _calc2(a, 74)
    return "".join(a)


def _calc1(a, b):
    c = a[0]
    a[0] = a[b % len(a)]
    a[b] = c


def _calc2(a, b):
    a.reverse()


def _calc3(a, b):
    a.splice(0, b)


class Youtube(robot.Robot):
    def __init__(self):
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global COOKIE_INFO

        sys_config = {
            robot.SYS_DOWNLOAD_VIDEO: True,
            robot.SYS_SET_PROXY: True,
            robot.SYS_GET_COOKIE: {".youtube.com": ()}
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        VIDEO_DOWNLOAD_PATH = self.video_download_path
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)
        COOKIE_INFO = self.cookie_value

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
    is_find = False

    def __init__(self, account_info, main_thread):
        robot.DownloadThread.__init__(self, account_info, main_thread)
        self.account_id = self.account_info[0]
        if len(self.account_info) >= 5 and self.account_info[4]:
            self.account_name = self.account_info[4]
        else:
            self.account_name = self.account_info[0]
        log.step(self.account_name + " 开始")

    # 获取所有可下载视频
    def get_crawl_list(self):
        token = ""
        video_id_list = []
        # 是否有根据视频id找到上一次的记录
        if self.account_info[2] == "":
            self.is_find = True
        is_over = False
        # 获取全部还未下载过需要解析的相册
        while not is_over:
            self.main_thread_check()  # 检测主线程运行状态
            log.step(self.account_name + " 开始解析 %s 视频页" % token)

            # 获取一页视频
            try:
                blog_pagination_response = get_one_page_video(self.account_id, token)
            except robot.RobotException, e:
                log.error(self.account_name + " 视频页（token：%s）解析失败，原因：%s" % (token, e.message))
                raise

            log.trace(self.account_name + " 视频页（token：%s）解析的全部日志：%s" % (token, blog_pagination_response["video_id_list"]))

            # 寻找这一页符合条件的日志
            for video_id in blog_pagination_response["video_id_list"]:
                # 检查是否达到存档记录
                if video_id != self.account_info[2]:
                    video_id_list.append(video_id)
                else:
                    is_over = True
                    self.is_find = True
                    break

            if not is_over:
                if blog_pagination_response["next_page_token"]:
                    # 设置下一页token
                    token = blog_pagination_response["next_page_token"]
                else:
                    is_over = True

        return video_id_list

    # 解析单个视频
    def crawl_video(self, video_id):
        video_index = int(self.account_info[1]) + 1
        # 获取指定视频信息
        try:
            video_response = get_video_page(video_id)
        except robot.RobotException, e:
            log.error(self.account_name + " 第%s个视频%s解析失败，原因：%s" % (video_index, video_id, e.message))
            raise

        # 如果解析需要下载的视频时没有找到上次的记录，表示存档所在的视频已被删除，则判断数字id
        if not self.is_find:
            if video_response["video_time"] < int(self.account_info[3]):
                log.step(self.account_name + " 视频%s跳过" % video_id)
                return
            elif video_response["video_time"] == int(self.account_info[3]):
                log.error(self.account_name + " 第%s个视频%s与存档视频发布日期一致，无法过滤，再次下载" % (video_index, video_id))
            else:
                self.is_find = True

        self.main_thread_check()  # 检测主线程运行状态
        log.step(self.account_name + " 开始下载第%s个视频 %s" % (video_index, video_response["video_url"]))

        video_file_path = os.path.join(VIDEO_DOWNLOAD_PATH, self.account_name, "%04d.mp4" % video_index)
        save_file_return = net.save_net_file(video_response["video_url"], video_file_path)
        if save_file_return["status"] == 1:
            # 设置临时目录
            log.step(self.account_name + " 第%s个视频下载成功" % video_index)
        else:
            if save_file_return["code"] == net.HTTP_RETURN_CODE_RESPONSE_TO_LARGE:
                log.error(self.account_name + " 第%s个视频（%s） %s 文件太大，跳过" % (video_index, video_id, video_response["video_url"]))
            else:
                log.error(self.account_name + " 第%s个视频（%s） %s 下载失败，原因：%s" % (video_index, video_id, video_response["video_url"], robot.get_save_net_file_failed_reason(save_file_return["code"])))
                return

        # 媒体内图片和视频全部下载完毕
        self.total_video_count += 1  # 计数累加
        self.account_info[1] = str(video_index)  # 设置存档记录
        self.account_info[2] = video_id  # 设置存档记录
        self.account_info[3] = str(video_response["video_time"])  # 设置存档记录

    def run(self):
        try:
            # 获取所有可下载视频
            video_id_list = self.get_crawl_list()
            log.step(self.account_name + " 需要下载的全部视频解析完毕，共%s个" % len(video_id_list))
            if not self.is_find:
                log.step(self.account_name + " 存档所在视频已删除，需要在下载时进行过滤")

            # 从最早的视频开始下载
            while len(video_id_list) > 0:
                video_id = video_id_list.pop()
                log.step(self.account_name + " 开始解析第%s个视频%s" % (int(self.account_info[1]) + 1, video_id))
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
    Youtube().main()
