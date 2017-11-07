# -*- coding:UTF-8  -*-
"""
一直播图片&视频爬虫
http://www.yizhibo.com/
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

ACCOUNTS = []
TOTAL_IMAGE_COUNT = 0
TOTAL_VIDEO_COUNT = 0
IMAGE_DOWNLOAD_PATH = ""
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_DOWNLOAD_IMAGE = True
IS_DOWNLOAD_VIDEO = True


# 获取全部图片地址列表
def get_image_index_page(account_id):
    # http://www.yizhibo.com/member/personel/user_photos?memberid=6066534
    image_index_url = "http://www.yizhibo.com/member/personel/user_photos"
    query_data = {"memberid": account_id}
    image_index_response = net.http_request(image_index_url, method="GET", fields=query_data)
    result = {
        "image_url_list": [],  # 全部图片地址
    }
    if image_index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(image_index_response.status))
    if image_index_response.data == '<script>window.location.href="/404.html";</script>':
        raise robot.RobotException("账号不存在")
    # 获取全部图片地址
    if image_index_response.data.find("还没有照片哦") == -1:
        image_url_list = re.findall('<img src="([^"]*)@[^"]*" alt="" class="index_img_main">', image_index_response.data)
        if len(image_url_list) == 0:
            raise robot.RobotException("页面匹配图片地址失败\n%s" % image_index_response.data)
        result["image_url_list"] = map(str, image_url_list)
    return result


#  获取图片的header
def get_image_header(image_url):
    image_head_response = net.http_request(image_url, method="HEAD")
    result = {
        "image_time": None, # 图片上传时间
    }
    if image_head_response.status == 404:
        return result
    elif image_head_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(image_head_response.status))
    last_modified = image_head_response.headers.get("Last-Modified")
    if last_modified is None:
        raise robot.RobotException("图片header'Last-Modified'字段不存在\n%s" % image_head_response.headers)
    try:
        last_modified_time = time.strptime(last_modified, "%a, %d %b %Y %H:%M:%S %Z")
    except ValueError:
        raise robot.RobotException("图片上传时间文本格式不正确\n%s" % last_modified)
    result["image_time"] = int(time.mktime(last_modified_time)) - time.timezone
    return result


# 获取全部视频ID列表
def get_video_index_page(account_id):
    # http://www.yizhibo.com/member/personel/user_videos?memberid=6066534
    video_pagination_url = "http://www.yizhibo.com/member/personel/user_videos" % account_id
    query_data = {"memberid": account_id}
    video_pagination_response = net.http_request(video_pagination_url, method="GET", fields=query_data)
    result = {
        "is_exist": True,  # 是不是存在视频
        "video_id_list": [],  # 全部视频id
    }
    if video_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(video_pagination_response.status))
    if video_pagination_response.data == '<script>window.location.href="/404.html";</script>':
        raise robot.RobotException("账号不存在")
    if video_pagination_response.data.find("还没有直播哦") == -1:
        video_id_list = re.findall('<div class="scid" style="display:none;">([^<]*?)</div>', video_pagination_response.data)
        if len(video_id_list) == 0:
            raise robot.RobotException("页面匹配视频id失败\n%s" % video_pagination_response.data)
        result["video_id_list"] = map(str, video_id_list)
    return result


# 根据video id获取指定视频的详细信息（上传时间、视频列表的下载地址等）
# video_id -> qxonW5XeZru03nUB
def get_video_info_page(video_id):
    # http://api.xiaoka.tv/live/web/get_play_live?scid=xX9-TLVx0xTiSZ69
    video_info_url = "http://api.xiaoka.tv/live/web/get_play_live"
    query_data = {"scid": video_id}
    video_info_response = net.http_request(video_info_url, method="GET", fields=query_data, json_decode=True)
    result = {
        "video_time": False,  # 视频上传时间
        "video_url_list": [],  # 全部视频分集地址
    }
    if video_info_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(video_info_response.status))
    if not robot.check_sub_key(("result", "data"), video_info_response.json_data):
        raise robot.RobotException("返回信息'result'或'data'字段不存在\n%s" % video_info_response.json_data)
    if not robot.is_integer(video_info_response.json_data["result"]):
        raise robot.RobotException("返回信息'result'字段类型不正确\n%s" % video_info_response.json_data)
    if int(video_info_response.json_data["result"]) != 1:
        raise robot.RobotException("返回信息'result'字段取值不正确\n%s" % video_info_response.json_data)
    # 获取视频上传时间
    if not robot.check_sub_key(("createtime",), video_info_response.json_data["data"]):
        raise robot.RobotException("返回信息'createtime'字段不存在\n%s" % video_info_response.json_data)
    if not robot.is_integer(video_info_response.json_data["data"]["createtime"]):
        raise robot.RobotException("返回信息'createtime'字段类型不正确\n%s" % video_info_response.json_data)
    result["video_time"] = int(video_info_response.json_data["data"]["createtime"])
    # 获取视频地址所在文件地址
    if not robot.check_sub_key(("linkurl",), video_info_response.json_data["data"]):
        raise robot.RobotException("返回信息'linkurl'字段不存在\n%s" % video_info_response.json_data)
    video_file_url = str(video_info_response.json_data["data"]["linkurl"])
    video_file_response = net.http_request(video_file_url, method="GET")
    if video_file_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        ts_id_list = re.findall("([\S]*.ts)", video_file_response.data)
        if len(ts_id_list) == 0:
            raise robot.RobotException("分集文件匹配视频地址失败\n%s" % video_info_response.json_data)
        # http://alcdn.hls.xiaoka.tv/20161122/6b6/c5f/xX9-TLVx0xTiSZ69/
        prefix_url = video_file_url[:video_file_url.rfind("/") + 1]
        for ts_id in ts_id_list:
            result["video_url_list"].append(prefix_url + str(ts_id))
    else:
        raise robot.RobotException(robot.get_http_request_failed_reason(video_info_response.status))
    return result


class YiZhiBo(robot.Robot):
    def __init__(self):
        global IMAGE_DOWNLOAD_PATH
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_DOWNLOAD_IMAGE
        global IS_DOWNLOAD_VIDEO

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_DOWNLOAD_VIDEO: True,
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        VIDEO_DOWNLOAD_PATH = self.video_download_path
        IS_DOWNLOAD_IMAGE = self.is_download_image
        IS_DOWNLOAD_VIDEO = self.is_download_video
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

    def main(self):
        global ACCOUNTS

        # 解析存档文件
        # account_id  video_count  last_video_time  image_count  last_image_time(account_name)
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0", "0", "0"])
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

        log.step("全部下载完毕，耗时%s秒，共计图片%s张，视频%s个" % (self.get_run_time(), TOTAL_IMAGE_COUNT, TOTAL_VIDEO_COUNT))


class Download(robot.DownloadThread):
    def __init__(self, account_info, thread_lock):
        robot.DownloadThread.__init__(self, account_info, thread_lock)

    def run(self):
        global TOTAL_IMAGE_COUNT
        global TOTAL_VIDEO_COUNT

        account_id = self.account_info[0]
        if len(self.account_info) >= 6 and self.account_info[5]:
            account_name = self.account_info[5]
        else:
            account_name = self.account_info[0]
        total_image_count = 0
        total_video_count = 0

        try:
            log.step(account_name + " 开始")

            # 图片下载
            while IS_DOWNLOAD_IMAGE:
                image_info_list = []
                is_error = False
                # 获取全部图片地址列表
                try:
                    image_index_response = get_image_index_page(account_id)
                except robot.RobotException, e:
                    log.error(account_name + " 图片首页解析失败，原因：%s" %  e.message)
                    break

                # 寻找这一页符合条件的图片
                for image_url in image_index_response["image_url_list"]:
                    log.step(account_name + " 开始解析图片%s" % image_url)
                    try:
                        image_head_response = get_image_header(image_url)
                    except robot.RobotException, e:
                        log.error(account_name + " 图片%s解析失败，原因：%s" % (image_url, e.message))
                        is_error = True
                        break

                    if image_head_response["image_time"] is None:
                        continue

                    # 检查是否达到存档记录
                    if image_head_response["image_time"] > int(self.account_info[4]):
                        image_info_list.append({"image_url": image_url, "image_time": image_head_response["image_time"],})
                    else:
                        break

                if is_error:
                    break

                log.step("需要下载的全部图片解析完毕，共%s张" % len(image_info_list))

                # 从最早的图片开始下载
                while len(image_info_list) > 0:
                    image_info = image_info_list.pop()
                    image_index = int(self.account_info[3]) + 1
                    log.step(account_name + " 开始下载第%s张图片 %s" % (image_index, image_info["image_url"]))

                    file_type = image_info["image_url"].split(".")[-1].split(":")[0]
                    image_file_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name, "%04d.%s" % (image_index, file_type))
                    save_file_return = net.save_net_file(image_info["image_url"], image_file_path)
                    if save_file_return["status"] == 1:
                        log.step(account_name + " 第%s张图片下载成功" % image_index)
                    else:
                        log.error(account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_index, image_info["image_url"], robot.get_save_net_file_failed_reason(save_file_return["code"])))
                        continue
                    # 图片下载完毕
                    total_image_count += 1  # 计数累加
                    self.account_info[3] = str(image_index)  # 设置存档记录
                    self.account_info[4] = str(image_info["image_time"])  # 设置存档记录
                break

            # 视频下载
            while IS_DOWNLOAD_VIDEO:
                video_info_list = []
                is_error = False
                # 获取全部视频ID列表
                try:
                    video_pagination_response = get_video_index_page(account_id)
                except robot.RobotException, e:
                    log.error(account_name + " 视频首页解析失败，原因：%s" %  e.message)
                    break

                # 寻找这一页符合条件的视频
                for video_id in video_pagination_response["video_id_list"]:
                    log.step(account_name + " 开始解析视频%s" % video_id)
                    # 获取视频的时间和下载地址
                    try:
                        video_info_response = get_video_info_page(video_id)
                    except robot.RobotException, e:
                        log.error(account_name + " 视频%s解析失败，原因：%s" % (video_id, e.message))
                        is_error = True
                        break

                    # 检查是否达到存档记录
                    if video_info_response["video_time"] > int(self.account_info[2]):
                        video_info_list.append(video_info_response)
                    else:
                        break

                if is_error:
                    break

                log.step(account_name + " 需要下载的全部视频解析完毕，共%s个" % len(video_info_list))

                # 从最早的视频开始下载
                video_index = int(self.account_info[1]) + 1
                while len(video_info_list) > 0:
                    video_info = video_info_list.pop()
                    log.step(account_name + " 开始下载第%s个视频 %s" % (video_index, video_info["video_url_list"]))

                    video_file_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name, "%04d.ts" % video_index)
                    save_file_return = net.save_net_file_list(video_info["video_url_list"], video_file_path)
                    if save_file_return["status"] == 1:
                        log.step(account_name + " 第%s个视频下载成功" % video_index)
                    else:
                        log.error(account_name + " 第%s个视频 %s 下载失败" % (video_index, video_info["video_url_list"]))
                        continue
                    # 视频下载完毕
                    total_video_count += 1  # 计数累加
                    self.account_info[1] = str(video_index)  # 设置存档记录
                    self.account_info[2] = str(video_info["video_time"])  # 设置存档记录
                break
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
        TOTAL_IMAGE_COUNT += total_image_count
        TOTAL_VIDEO_COUNT += total_video_count
        ACCOUNTS.remove(account_id)
        self.thread_lock.release()
        log.step(account_name + " 下载完毕，总共获得%s张图片和%s个视频" % (total_image_count, total_video_count))


if __name__ == "__main__":
    YiZhiBo().main()
