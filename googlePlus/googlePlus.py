# -*- coding:UTF-8  -*-
"""
Google Plus图片爬虫
https://plus.google.com/
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

ACCOUNTS = []
GET_IMAGE_URL_COUNT = 100  # 单次获取最新的N张照片,G+ 限制最多1000张
TOTAL_IMAGE_COUNT = 0
GET_IMAGE_COUNT = 0
IMAGE_TEMP_PATH = ""
IMAGE_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_SORT = True


# 获取指定token后的一页相册
def get_one_page_blog(account_id, token):
    extra_info = {
        "is_error": True,  # 是不是格式不符合
        "blog_info_list": [],  # 页面解析出的日志信息列表
        "next_page_key": None,  # 页面解析出的下一页token
        "json_data": None,  # 原始数据
    }
    script_data = []
    if token:
        index_page_url = "https://get.google.com/_/AlbumArchiveUi/data"
        post_data = {"f.req": '[[[113305009,[{"113305009":["%s",null,2,16,"%s"]}],null,null,0]]]' % (account_id, token)}
        index_page_response = net.http_request(index_page_url, method="POST", post_data=post_data)
        if index_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
            script_data_string = tool.find_sub_string(index_page_response.data, ")]}'", None).strip()
            try:
                script_data = json.loads(script_data_string)
            except ValueError:
                script_data = []
            else:
                extra_info["json_data"] = script_data_string
            if len(script_data) == 3 and len(script_data[0]) == 3 and robot.check_sub_key(("113305009",), script_data[0][2]):
                script_data = script_data[0][2]["113305009"]
            else:
                script_data = []
    else:
        index_page_url = "https://get.google.com/albumarchive/%s/albums/photos-from-posts" % account_id
        index_page_response = net.http_request(index_page_url)
        if index_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
            script_data = tool.find_sub_string(index_page_response.data, "AF_initDataCallback({key: 'ds:0'", "</script>")
            script_data_string = tool.find_sub_string(script_data, "return ", "}});")
            try:
                script_data = json.loads(script_data_string)
            except ValueError:
                script_data = []
            else:
                extra_info["json_data"] = script_data_string
    if len(script_data) == 3:
        if script_data[1] is not None:
            extra_info["is_error"] = False
            for data in script_data[1]:
                extra_blog_info = {
                    "blog_id": None,  # 页面解析出的日志id
                    "blog_time": None,  # 页面解析出的日志上传时间
                    "json_data": data,  # 原始数据
                }
                blog_data = []
                for temp_data in data:
                    if robot.check_sub_key(("113305016",), temp_data):
                        blog_data = temp_data["113305016"][0]
                        break
                if len(blog_data) >= 5:
                    # 获取日志id
                    extra_blog_info["blog_id"] = str(blog_data[0])
                    # 获取日志创建时间
                    if robot.is_integer(blog_data[4]):
                        extra_blog_info["blog_time"] = int(int(blog_data[4]) / 1000)
                extra_info["blog_info_list"].append(extra_blog_info)
        else:
            extra_info["is_error"] = False
        extra_info["next_page_key"] = str(script_data[2])
    index_page_response.extra_info = extra_info
    return index_page_response


# 获取日志页面
def get_blog_page(account_id, picasaweb_url):
    retry_count = 0
    while True:
        blog_page_response = net.http_request(picasaweb_url)
        extra_info = {
            "album_id": None,  # 页面解析出的相册id
        }
        if blog_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
            album_id = tool.find_sub_string(blog_page_response.data, 'href="https://get.google.com/albumarchive/pwa/%s/album/' % account_id, '"')
            if album_id and robot.is_integer(album_id):
                extra_info["album_id"] = str(album_id)
        # 如果status==500，重试最多5次
        elif blog_page_response.status == 500 and retry_count < 5:
            retry_count += 1
            continue
        blog_page_response.extra_info = extra_info
        return blog_page_response


# 获取指定id的相册页
def get_album_page(account_id, album_id):
    # 图片只有一页：https://get.google.com/albumarchive/102249965218267255722/album/AF1QipPLt_v4vK2Jkqcm5DOtFl6aHWZMTdu0A4mOpOFN?source=pwa
    # 图片不止一页：https://get.google.com/albumarchive/109057690948151627836/album/AF1QipMg1hsC4teQFP5xaBioWo-1SCr4Hphh4mfc0ZZX?source=pwa
    album_page_url = "https://get.google.com/albumarchive/%s/album/%s" % (account_id, album_id)
    extra_info = {
        "image_url_list": [],  # 页面解析出的图片地址列表
    }
    # retry_count = 0
    image_url_list = []
    while True:
        album_page_response = net.http_request(album_page_url)
        if album_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
            script_data = tool.find_sub_string(album_page_response.data, "AF_initDataCallback({key: 'ds:0'", "</script>")
            script_data = tool.find_sub_string(script_data, "return ", "}});")
            try:
                script_data = json.loads(script_data)
                user_key = script_data[4][0]
                continue_token = script_data[3]
                if len(script_data[4]) >= 2:
                    for data in script_data[4][1]:
                        image_url_list.append(str(data[1]))
            except ValueError:
                pass
            else:
                # 如果不为空，说明还有下一页
                while continue_token:
                    continue_image_page_url = "https://get.google.com/_/AlbumArchiveUi/data"
                    post_data = {"f.req": '[[[113305010,[{"113305010":["%s",null,24,"%s"]}],null,null,0]]]' % (user_key, continue_token)}
                    continue_image_page_response = net.http_request(continue_image_page_url, method="POST", post_data=post_data, encode_multipart=False)
                    if continue_image_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
                        continue_data = tool.find_sub_string(continue_image_page_response.data, ")]}'", None).strip()
                        try:
                            continue_data = json.loads(continue_data)
                            continue_token = continue_data[0][2]["113305010"][3]
                            for data in continue_data[0][2]["113305010"][4][1]:
                                image_url_list.append(str(data[1]))
                        except ValueError:
                            image_url_list = []
                            continue_token = ""
            if len(image_url_list) > 0:
                extra_info["image_url_list"] = image_url_list
        album_page_response.extra_info = extra_info
        return album_page_response


class GooglePlus(robot.Robot):
    def __init__(self):
        global GET_IMAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_SET_PROXY: True,
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        GET_IMAGE_COUNT = self.get_image_count
        IMAGE_TEMP_PATH = self.image_temp_path
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        IS_SORT = self.is_sort
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

    def main(self):
        global ACCOUNTS

        # 解析存档文件
        # account_id  image_count  album_id  (account_name)  (file_path)
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

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), TOTAL_IMAGE_COUNT))


class Download(threading.Thread):
    def __init__(self, account_info, thread_lock):
        threading.Thread.__init__(self)
        self.account_info = account_info
        self.thread_lock = thread_lock

    def run(self):
        global TOTAL_IMAGE_COUNT

        account_id = self.account_info[0]
        if len(self.account_info) >= 4 and self.account_info[3]:
            account_name = self.account_info[3]
        else:
            account_name = self.account_info[0]
        if len(self.account_info) >= 5 and self.account_info[4]:
            account_file_path = self.account_info[4]
        else:
            account_file_path = ""

        try:
            log.step(account_name + " 开始")

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if IS_SORT:
                image_path = os.path.join(IMAGE_TEMP_PATH, account_name)
            else:
                image_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_file_path, account_name)

            # 图片下载
            image_count = 1
            key = ""
            first_album_id = "0"
            is_over = False
            need_make_download_dir = True
            while not is_over:
                log.step(account_name + " 开始解析 %s 相册页" % key)

                # 获取一页相册
                index_page_response = get_one_page_blog(account_id, key)
                if index_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                    log.error(account_name + " 相册页（token：%s）访问失败，原因：%s" % (key, robot.get_http_request_failed_reason(index_page_response.status)))
                    tool.process_exit()

                if index_page_response.extra_info["is_error"]:
                    if index_page_response.extra_info["json_data"] is None:
                        log.error(account_name + " 相册页（token：%s）JSON数据解析失败" % key)
                    else:
                        log.error(account_name + " 相册页（token：%s）%s解析失败" % (key, index_page_response.extra_info["json_data"]))
                    tool.process_exit()

                log.trace(account_name + " 相册页（token：%s）解析的所有日志信息：%s" % (key, index_page_response.extra_info["blog_info_list"]))

                for blog_info in index_page_response.extra_info["blog_info_list"]:
                    if blog_info["blog_id"] is None:
                        log.error(account_name + " 日志信息%s的日志id解析失败" % blog_info["json_data"])
                        tool.process_exit()

                    if blog_info["blog_time"] is None:
                        log.error(account_name + " 日志信息%s的日志时间解析失败" % blog_info["json_data"])
                        tool.process_exit()

                    # 检查是否已下载到前一次的日志
                    if blog_info["blog_time"] <= int(self.account_info[2]):
                        is_over = True
                        break

                    # 将第一个日志的id做为新的存档记录
                    if first_album_id == "0":
                        first_album_id = str(blog_info["blog_time"])

                    log.step(account_name + " 开始解析日志 %s" % blog_info["blog_id"])
                    
                    # 获取相册页
                    album_page_response = get_album_page(account_id, blog_info["blog_id"])
                    if album_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                        log.error(account_name + " 相册%s访问失败，原因：%s" % (blog_info["blog_id"], robot.get_http_request_failed_reason(album_page_response.status)))
                        tool.process_exit()

                    if len(album_page_response.extra_info["image_url_list"]) == 0:
                        log.error(account_name + " 相册%s没有解析到图片" % blog_info["blog_id"])
                        # tool.process_exit()
                        continue

                    log.trace(account_name + " 相册存档页%s解析的所有图片：%s" % (blog_info["blog_id"], album_page_response.extra_info["image_url_list"]))

                    for image_url in album_page_response.extra_info["image_url_list"]:
                        # 视频跳过
                        if image_url.find("video.googleusercontent.com") != -1:
                            continue

                        log.step(account_name + " 开始下载第%s张图片 %s" % (image_count, image_url))

                        # 第一张图片，创建目录
                        if need_make_download_dir:
                            if not tool.make_dir(image_path, 0):
                                log.error(account_name + " 创建图片下载目录 %s 失败" % image_path)
                                tool.process_exit()
                            need_make_download_dir = False

                        file_path = os.path.join(image_path, "%04d.jpg" % image_count)
                        retry_count = 0
                        while True:
                            save_file_return = net.save_net_file(image_url, file_path, need_content_type=True)
                            if save_file_return["status"] == 1:
                                log.step(account_name + " 第%s张图片下载成功" % image_count)
                                image_count += 1
                            elif save_file_return["status"] == 0 and save_file_return["code"] == 500 and retry_count <= 5:
                                retry_count += 1
                                continue
                            else:
                                log.error(account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_count, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
                            break

                        # 达到配置文件中的下载数量，结束
                        if 0 < GET_IMAGE_COUNT < image_count:
                            is_over = True
                            break
                    if is_over:
                        break

                if not is_over:
                    if index_page_response.extra_info["next_page_key"]:
                        key = index_page_response.extra_info["next_page_key"]
                    else:
                        # 不是第一次下载
                        if self.account_info[2] != "0":
                            log.error(account_name + " 没有找到下一页的token，将该页保存：")
                            log.error(index_page_response.data)
                        is_over = True

            log.step(account_name + " 下载完毕，总共获得%s张图片" % (image_count - 1))

            # 排序
            if IS_SORT and image_count > 1:
                log.step(account_name + " 图片开始从下载目录移动到保存目录")
                destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_file_path, account_name)
                if robot.sort_file(image_path, destination_path, int(self.account_info[1]), 4):
                    log.step(account_name + " 图片从下载目录移动到保存目录成功")
                else:
                    log.error(account_name + " 创建图片子目录 %s 失败" % destination_path)
                    tool.process_exit()

            # 新的存档记录
            if first_album_id != "0":
                self.account_info[1] = str(int(self.account_info[1]) + image_count - 1)
                self.account_info[2] = first_album_id

            # 保存最后的信息
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            self.thread_lock.acquire()
            TOTAL_IMAGE_COUNT += image_count - 1
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
    GooglePlus().main()
