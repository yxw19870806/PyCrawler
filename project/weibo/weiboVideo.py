# -*- coding:UTF-8  -*-
"""
微博视频爬虫
http://www.weibo.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import weiboCommon
import base64
import os
import random
import re
import threading
import time
import traceback
import urllib2

ACCOUNTS = []
INIT_SINCE_ID = "9999999999999999"
TOTAL_VIDEO_COUNT = 0
VIDEO_TEMP_PATH = ""
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
COOKIE_INFO = {"SUB": ""}


# 获取一页的视频信息
# page_id -> 1005052535836307
def get_one_page_video(account_page_id, since_id):
    # http://weibo.com/p/aj/album/loading?type=video&since_id=9999999999999999&page_id=1005052535836307&page=1&ajax_call=1
    video_pagination_url = "http://weibo.com/p/aj/album/loading"
    video_pagination_url += "?type=video&since_id=%s&page_id=%s&page=1&ajax_call=1&__rnd=%s" % (since_id, account_page_id, int(time.time() * 1000))
    cookies_list = {"SUB": COOKIE_INFO["SUB"]}
    result = {
        "is_error": False,  # 是不是格式不符合
        "video_play_url_list": [],  # 所有视频地址
        "next_page_since_id": None,  # 下一页视频指针
    }
    video_pagination_response = net.http_request(video_pagination_url, cookies_list=cookies_list, json_decode=True)
    if video_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(video_pagination_response.status))
    if not robot.check_sub_key(("code", "data"), video_pagination_response.json_data):
        raise robot.RobotException("返回信息'code'或'data'字段不存在\n%s" % video_pagination_response.json_data)
    if not robot.is_integer(video_pagination_response.json_data["code"]):
        raise robot.RobotException("返回信息'code'字段类型不正确\n%s" % video_pagination_response.json_data)
    if int(video_pagination_response.json_data["code"]) != 100000:
        raise robot.RobotException("返回信息'code'字段取值不正确\n%s" % video_pagination_response.json_data)
    page_html = video_pagination_response.json_data["data"].encode("UTF-8")
    # 获取视频播放地址
    video_play_url_list = re.findall('<a target="_blank" href="([^"]*)"><div ', page_html)
    if len(video_play_url_list) == 0:
        if since_id != INIT_SINCE_ID or page_html.find("还没有发布过视频") == -1:
            raise robot.RobotException("返回信息匹配视频地址失败\n%s" % video_pagination_response.json_data)
    else:
        result["video_play_url_list"] = map(str, video_play_url_list)
    # 获取下一页视频的指针
    next_page_since_id = tool.find_sub_string(page_html, "type=video&owner_uid=&viewer_uid=&since_id=", '">')
    if not robot.is_integer(next_page_since_id):
        raise robot.RobotException("返回信息截取下一页指针失败\n%s" % video_pagination_response.json_data)
    result["next_page_since_id"] = next_page_since_id
    return result


# 从视频播放页面中提取下载地址
def get_video_url(video_play_url):
    video_url = None
    # http://miaopai.com/show/Gmd7rwiNrc84z5h6S9DhjQ__.htm
    if video_play_url.find("miaopai.com/show/") >= 0:  # 秒拍
        video_id = tool.find_sub_string(video_play_url, "miaopai.com/show/", ".")
        video_info_url = "http://gslb.miaopai.com/stream/%s.json?token=" % video_id
        video_info_response = net.http_request(video_info_url, json_decode=True)
        if video_info_response.status != net.HTTP_RETURN_CODE_SUCCEED:
            raise robot.RobotException(robot.get_http_request_failed_reason(video_info_response.status))
        if not robot.check_sub_key(("status", "result"), video_info_response.json_data):
            raise robot.RobotException("返回信息'status'或'result'字段不存在\n%s" % video_info_response.json_data)
        if not robot.is_integer(video_info_response.json_data["status"]):
            raise robot.RobotException("返回信息'status'字段类型不正确\n%s" % video_info_response.json_data)
        if int(video_info_response.json_data["status"]) != 200:
            raise robot.RobotException("返回信息'status'字段取值不正确\n%s" % video_info_response.json_data)
        if len(video_info_response.json_data["result"]) == 0:
            raise robot.RobotException("返回信息'result'字段长度不正确\n%s" % video_info_response.json_data)
        for video_info in video_info_response.json_data["result"]:
            if robot.check_sub_key(("path", "host", "scheme"), video_info):
                video_url = str(video_info["scheme"] + video_info["host"] + video_info["path"])
                break
        if video_url is None:
            raise robot.RobotException("返回信息匹配视频地址失败\n%s" % video_info_response.json_data)
    # http://video.weibo.com/show?fid=1034:e608e50d5fa95410748da61a7dfa2bff
    elif video_play_url.find("video.weibo.com/show?fid=") >= 0:  # 微博视频
        cookies_list = {"SUB": COOKIE_INFO["SUB"]}
        video_play_response = net.http_request(video_play_url, cookies_list=cookies_list)
        if video_play_response.status == net.HTTP_RETURN_CODE_SUCCEED:
            video_url = tool.find_sub_string(video_play_response.data, "video_src=", "&")
            if not video_url:
                video_url = tool.find_sub_string(video_play_response.data, 'flashvars="list=', '"')
            if not video_url:
                raise robot.RobotException("页面截取视频地址失败\n%s" % video_play_response.data)
            video_url = str(urllib2.unquote(video_url))
        elif video_play_response.status == 404:
            video_url = ""
        else:
            raise robot.RobotException(robot.get_http_request_failed_reason(video_play_response.status))
    # http://www.meipai.com/media/98089758
    elif video_play_url.find("www.meipai.com/media") >= 0:  # 美拍
        video_play_response = net.http_request(video_play_url)
        if video_play_response.status != net.HTTP_RETURN_CODE_SUCCEED:
            raise robot.RobotException(robot.get_http_request_failed_reason(video_play_response.status))
        video_url_find = re.findall('<meta content="([^"]*)" property="og:video:url">', video_play_response.data)
        if len(video_url_find) != 1:
            raise robot.RobotException("页面匹配加密视频信息失败\n%s" % video_play_response.data)
        loc1 = meipai_get_hex(video_url_find[0])
        loc2 = meipai_get_dec(loc1["hex"])
        loc3 = meipai_sub_str(loc1["str"], loc2["pre"])
        video_url_string = meipai_sub_str(loc3, meipai_get_pos(loc3, loc2["tail"]))
        try:
            video_url = base64.b64decode(video_url_string)
        except TypeError:
            raise robot.RobotException("加密视频地址解密失败\n%s\n%s" % (str(video_url_find[0]), video_url_string))
        if video_url.find("http") != 0:
            raise robot.RobotException("加密视频地址解密失败\n%s\n%s" % (str(video_url_find[0]), video_url_string))
    # http://v.xiaokaxiu.com/v/0YyG7I4092d~GayCAhwdJQ__.html
    elif video_play_url.find("v.xiaokaxiu.com/v/") >= 0:  # 小咖秀
        video_id = video_play_url.split("/")[-1].split(".")[0]
        video_url = "http://gslb.miaopai.com/stream/%s.mp4" % video_id
    # http://www.weishi.com/t/2000546051794045
    elif video_play_url.find("www.weishi.com/t/") >= 0:  # 微视
        video_play_response = net.http_request(video_play_url)
        if video_play_response != net.HTTP_RETURN_CODE_SUCCEED:
            raise robot.RobotException(robot.get_http_request_failed_reason(video_play_response.status))
        video_id_find = re.findall('<div class="vBox js_player"[\s]*id="([^"]*)"', video_play_response.data)
        if len(video_id_find) != 1:
            raise robot.RobotException("页面匹配视频id失败\n%s" % video_play_response.data)
        video_id = video_play_url.split("/")[-1]
        video_info_url = "http://wsi.weishi.com/weishi/video/downloadVideo.php?vid=%s&device=1&id=%s" % (video_id_find[0], video_id)
        video_info_response = net.http_request(video_info_url, json_decode=True)
        if video_info_response.status != net.HTTP_RETURN_CODE_SUCCEED:
            raise robot.RobotException("API " + robot.get_http_request_failed_reason(video_info_response.status))
        if not robot.check_sub_key(("data",), video_info_response.json_data):
            raise robot.RobotException("返回信息'data'字段不存在\n%s" % video_info_response.json_data)
        if not robot.check_sub_key(("url",), video_play_response.json_data["data"]):
            raise robot.RobotException("返回信息'url'字段不存在\n%s" % video_info_response.json_data)
        video_url = str(random.choice(video_info_response.json_data["data"]["url"]))
    else:  # 其他视频，暂时不支持，收集看看有没有
        raise robot.RobotException("未知的第三方视频\n%s" % video_play_url)
    return video_url


def meipai_get_hex(arg1):
    return {"str": arg1[4:], "hex": reduce(lambda x, y: y + x, arg1[0:4])}


def meipai_get_dec(arg1):
    loc1 = str(int(arg1, 16))
    return {"pre": [int(loc1[0]), int(loc1[1])], "tail": [int(loc1[2]), int(loc1[3])]}


def meipai_sub_str(arg1, arg2):
    loc1 = arg1[:arg2[0]]
    loc2 = arg1[arg2[0]: arg2[0] + arg2[1]]
    return loc1 + arg1[arg2[0]:].replace(loc2, "", 1)


def meipai_get_pos(arg1, arg2):
    arg2[0] = len(arg1) - arg2[0] - arg2[1]
    return arg2


class Weibo(robot.Robot):
    def __init__(self, extra_config=None):
        global VIDEO_TEMP_PATH
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global COOKIE_INFO

        sys_config = {
            robot.SYS_DOWNLOAD_VIDEO: True,
            robot.SYS_GET_COOKIE: {
                ".sina.com.cn": (),
                ".login.sina.com.cn": (),
            },
        }
        robot.Robot.__init__(self, sys_config, extra_config)

        # 设置全局变量，供子线程调用
        VIDEO_TEMP_PATH = self.video_temp_path
        VIDEO_DOWNLOAD_PATH = self.video_download_path
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)
        COOKIE_INFO.update(self.cookie_value)

    def main(self):
        global ACCOUNTS
        global COOKIE_INFO

        # 检测登录状态
        if not weiboCommon.check_login(COOKIE_INFO):
            # 如果没有获得登录相关的cookie，则模拟登录并更新cookie
            new_cookies_list = weiboCommon.generate_login_cookie(COOKIE_INFO)
            if new_cookies_list:
                COOKIE_INFO.update(new_cookies_list)
            # 再次检测登录状态
            if not weiboCommon.check_login(COOKIE_INFO):
                log.error("没有检测到登录信息")
                tool.process_exit()

        # 解析存档文件
        # account_id  image_count  last_image_time  video_count  last_video_url  (account_name)
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0", "0", ""])
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
        if len(self.account_info) >= 6 and self.account_info[5]:
            account_name = self.account_info[5]
        else:
            account_name = self.account_info[0]

        try:
            log.step(account_name + " 开始")

            # 视频
            video_count = 1
            first_video_url = None
            video_path = os.path.join(VIDEO_TEMP_PATH, account_name)
            # 获取账号首页
            try:
                account_index_response = weiboCommon.get_account_index_page(account_id)
            except robot.RobotException, e:
                log.error(account_name + " 首页解析失败，原因：%s" % e.message)
                raise

            is_over = False
            since_id = INIT_SINCE_ID
            while not is_over:
                log.step(account_name + " 开始解析%s后一页视频" % since_id)

                # 获取指定时间点后的一页视频信息
                try:
                    video_pagination_response = get_one_page_video(account_index_response["account_page_id"], since_id)
                except robot.RobotException, e:
                    log.error(account_name + " %s后的一页视频解析失败，原因：%s" % (since_id, e.message))
                    raise

                # 匹配获取全部的视频页面
                log.trace(account_name + "since_id：%s中的全部视频：%s" % (since_id, video_pagination_response["video_play_url_list"]))

                for video_play_url in video_pagination_response["video_play_url_list"]:
                    # 检查是否达到存档记录
                    if self.account_info[4] == video_play_url:
                        is_over = True
                        break

                    # 新的存档记录
                    if first_video_url is None:
                        first_video_url = video_play_url

                    log.step(account_name + " 开始解析第%s个视频 %s" % (video_count, video_play_url))

                    # 获取这个视频的下载地址
                    try:
                        video_url = get_video_url(video_play_url)
                    except robot.RobotException, e:
                        log.error(account_name + " 视频 %s 解析失败，原因：%s" % (video_play_url, e.message))
                        raise

                    if video_url is "":
                        continue

                    log.step(account_name + " 开始下载第%s个视频 %s" % (video_count, video_url))

                    video_file_path = os.path.join(video_path, "%04d.mp4" % video_count)
                    save_file_return = net.save_net_file(video_url, video_file_path)
                    if save_file_return["status"] == 1:
                        log.step(account_name + " 第%s个视频下载成功" % video_count)
                        video_count += 1
                    else:
                        log.error(account_name + " 第%s个视频 %s（%s) 下载失败，原因：%s" % (video_count, video_play_url, video_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

                if not is_over:
                    # 获取下一页的since_id
                    since_id = video_pagination_response["next_page_since_id"]
                    if not since_id:
                        break

            # 有历史记录，并且此次没有获得正常结束的标记，说明历史最后的视频已经被删除了
            if self.account_info[4] != "" and first_video_url is not None and not is_over:
                log.error(account_name + " 没有找到上次下载的最后一个视频地址")

            log.step(account_name + " 下载完毕，总共获得%s个视频" % (video_count - 1))

            # 排序
            if first_video_url is not None:
                log.step(account_name + " 视频开始从下载目录移动到保存目录")
                destination_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)
                if robot.sort_file(video_path, destination_path, int(self.account_info[3]), 4):
                    log.step(account_name + " 视频从下载目录移动到保存目录成功")
                else:
                    log.error(account_name + " 创建视频保存目录 %s 失败" % destination_path)
                    tool.process_exit()

            # 新的存档记录
            if first_video_url is not None:
                self.account_info[3] = str(int(self.account_info[3]) + video_count - 1)
                self.account_info[4] = first_video_url

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
    Weibo().main()
