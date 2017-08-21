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
IMAGE_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""


# 获取指定token后的一页相册
def get_one_page_blog(account_id, token):
    result = {
        "blog_info_list": [],  # 所有日志信息
        "next_page_key": None,  # 下一页token
    }
    # 截取页面中的JS数据
    if token:
        api_url = "https://get.google.com/_/AlbumArchiveUi/data"
        post_data = {"f.req": '[[[113305009,[{"113305009":["%s",null,2,16,"%s"]}],null,null,0]]]' % (account_id, token)}
        blog_pagination_response = net.http_request(api_url, method="POST", post_data=post_data)
        if blog_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
            raise robot.RobotException(robot.get_http_request_failed_reason(blog_pagination_response.status))
        script_data_html = tool.find_sub_string(blog_pagination_response.data, ")]}'", None).strip()
        if not script_data_html:
            raise robot.RobotException("页面截取日志信息失败\n%s" % blog_pagination_response.data)
        try:
            script_data = json.loads(script_data_html)
        except ValueError:
            raise robot.RobotException("日志信息加载失败\n%s" % script_data_html)
        if not (len(script_data) == 3 and len(script_data[0]) == 3 and robot.check_sub_key(("113305009",), script_data[0][2])):
            raise robot.RobotException("日志信息格式不正确\n%s" % script_data)
        script_data = script_data[0][2]["113305009"]
    else:
        blog_pagination_url = "https://get.google.com/albumarchive/%s/albums/photos-from-posts" % account_id
        blog_pagination_response = net.http_request(blog_pagination_url)
        if blog_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
            script_data_html = tool.find_sub_string(blog_pagination_response.data, "AF_initDataCallback({key: 'ds:0'", "</script>")
            script_data_html = tool.find_sub_string(script_data_html, "return ", "}});")
            if not script_data_html:
                raise robot.RobotException("页面截取日志信息失败\n%s" % blog_pagination_response.data)
            try:
                script_data = json.loads(script_data_html)
            except ValueError:
                raise robot.RobotException("日志信息加载失败\n%s" % script_data_html)
        elif blog_pagination_response.status == 400:
            raise robot.RobotException("账号不存在")
        else:
            raise robot.RobotException(robot.get_http_request_failed_reason(blog_pagination_response.status))
    if len(script_data) != 3:
        raise robot.RobotException("日志信息格式不正确\n%s" % script_data)
    # 获取下一页token
    result["next_page_key"] = str(script_data[2])
    # 获取日志信息
    if script_data[1] is not None:
        for data in script_data[1]:
            extra_blog_info = {
                "blog_id": None,  # 日志id
                "blog_time": None,  # 日志发布时间
            }
            blog_data = []
            for temp_data in data:
                if robot.check_sub_key(("113305016",), temp_data):
                    blog_data = temp_data["113305016"][0]
                    break
            if len(blog_data) >= 5:
                # 获取日志id
                extra_blog_info["blog_id"] = str(blog_data[0])
                # 获取日志发布时间
                if not robot.is_integer(blog_data[4]):
                    raise robot.RobotException("日志时间类型不正确\n%s" % blog_data)
                extra_blog_info["blog_time"] = int(int(blog_data[4]) / 1000)
            else:
                raise robot.RobotException("日志信息格式不正确\n%s" % script_data)
            result["blog_info_list"].append(extra_blog_info)
    else:
        result["is_error"] = False
    return result


# 获取指定id的相册页
def get_album_page(account_id, album_id):
    # 图片只有一页：https://get.google.com/albumarchive/102249965218267255722/album/AF1QipPLt_v4vK2Jkqcm5DOtFl6aHWZMTdu0A4mOpOFN?source=pwa
    # 图片不止一页：https://get.google.com/albumarchive/109057690948151627836/album/AF1QipMg1hsC4teQFP5xaBioWo-1SCr4Hphh4mfc0ZZX?source=pwa
    album_url = "https://get.google.com/albumarchive/%s/album/%s" % (account_id, album_id)
    result = {
        "image_url_list": [],  # 所有图片地址
    }
    album_response = net.http_request(album_url)
    if album_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(album_response.status))
    script_data_html = tool.find_sub_string(album_response.data, "AF_initDataCallback({key: 'ds:0'", "</script>")
    script_data_html = tool.find_sub_string(script_data_html, "return ", "}});")
    if not script_data_html:
        raise robot.RobotException("页面截取相册信息失败\n%s" % album_response.data)
    try:
        script_data = json.loads(script_data_html)
    except ValueError:
        raise robot.RobotException("相册信息加载失败\n%s" % script_data_html)
    try:
        user_key = script_data[4][0]
        continue_token = script_data[3]
        for data in script_data[4][1]:
            result["image_url_list"].append(str(data[1]))
    except ValueError:
        raise robot.RobotException("相册信息格式不正确\n%s" % script_data_html)
    # 判断是不是还有下一页
    while continue_token:
        api_url = "https://get.google.com/_/AlbumArchiveUi/data"
        post_data = {"f.req": '[[[113305010,[{"113305010":["%s",null,24,"%s"]}],null,null,0]]]' % (user_key, continue_token)}
        image_pagination_response = net.http_request(api_url, method="POST", post_data=post_data, encode_multipart=False)
        if image_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
            raise robot.RobotException(robot.get_http_request_failed_reason(album_response.status))
        continue_data = tool.find_sub_string(image_pagination_response.data, ")]}'", None).strip()
        try:
            continue_data = json.loads(continue_data)
        except ValueError:
            raise robot.RobotException("相册信息加载失败\n%s" % script_data_html)
        try:
            continue_token = continue_data[0][2]["113305010"][3]
            for data in continue_data[0][2]["113305010"][4][1]:
                result["image_url_list"].append(str(data[1]))
        except ValueError:
            raise robot.RobotException("相册信息格式不正确\n%s" % script_data_html)
    return result


class GooglePlus(robot.Robot):
    def __init__(self):
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_SET_PROXY: True,
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        IMAGE_DOWNLOAD_PATH = self.image_download_path
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
        self.temp_path_list = []

    def run(self):
        global TOTAL_IMAGE_COUNT

        account_id = self.account_info[0]
        if len(self.account_info) >= 4 and self.account_info[3]:
            account_name = self.account_info[3]
        else:
            account_name = self.account_info[0]
        if len(self.account_info) >= 5 and self.account_info[4]:
            account_team = self.account_info[4]
        else:
            account_team = ""
        total_image_count = 0

        try:
            log.step(account_name + " 开始")

            key = ""
            blog_info_list = []
            is_over = False
            # 获取全部还未下载过需要解析的相册
            while not is_over:
                log.step(account_name + " 开始解析 %s 相册页" % key)

                # 获取一页相册
                try:
                    blog_pagination_response = get_one_page_blog(account_id, key)
                except robot.RobotException, e:
                    log.error(account_name + " 相册页（token：%s）解析失败，原因：%s" % (key, e.message))
                    raise

                log.trace(account_name + " 相册页（token：%s）解析的所有日志信息：%s" % (key, blog_pagination_response["blog_info_list"]))

                for blog_info in blog_pagination_response["blog_info_list"]:
                    # 检查是否达到存档记录
                    if blog_info["blog_time"] > int(self.account_info[2]):
                        blog_info_list.append(blog_info)
                    else:
                        is_over = True
                        break

                if not is_over:
                    if blog_pagination_response["next_page_key"]:
                        key = blog_pagination_response["next_page_key"]
                    else:
                        # 不是第一次下载
                        if self.account_info[2] != "0":
                            log.error(account_name + " 没有找到下一页的token")
                        is_over = True

            log.step(account_name + " 需要下载的全部相册解析完毕，共%s个" % len(blog_info_list))

            # 从最早的相册开始下载
            while len(blog_info_list) > 0:
                blog_info = blog_info_list.pop()

                log.step(account_name + " 开始解析日志 %s" % blog_info["blog_id"])
                    
                # 获取相册页
                try:
                    album_response = get_album_page(account_id, blog_info["blog_id"])
                except robot.RobotException, e:
                    log.error(account_name + " 相册%s解析失败，原因：%s" % (blog_info["blog_id"], e.message))
                    raise

                if len(album_response["image_url_list"]) == 0:
                    log.error(account_name + " 相册%s没有解析到图片" % blog_info["blog_id"])
                    continue

                log.trace(account_name + " 相册存档页%s解析的所有图片：%s" % (blog_info["blog_id"], album_response["image_url_list"]))

                image_index = int(self.account_info[1]) + 1
                for image_url in album_response["image_url_list"]:
                    # 视频跳过
                    if image_url.find("video.googleusercontent.com") != -1 or image_url.find("video-downloads.googleusercontent.com") != -1:
                        continue

                    log.step(account_name + " 开始下载第%s张图片 %s" % (image_index, image_url))

                    file_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_team, account_name, "%04d.jpg" % image_index)
                    retry_count = 0
                    while True:
                        save_file_return = net.save_net_file(image_url, file_path, need_content_type=True)
                        if save_file_return["status"] == 1:
                            self.temp_path_list.append(save_file_return["file_path"])
                            log.step(account_name + " 第%s张图片下载成功" % image_index)
                            image_index += 1
                        elif save_file_return["status"] == 0 and save_file_return["code"] == 500 and retry_count <= 5:
                            retry_count += 1
                            continue
                        else:
                            log.error(account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_index, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
                        break
                # 相册图片全部下载完毕
                self.temp_path_list = []  # 临时目录设置清除
                total_image_count += (image_index - 1) - int(self.account_info[1])  # 计数累加
                self.account_info[1] = str(image_index - 1) # 设置存档记录
                self.account_info[2] = str(blog_info["blog_time"])
        except SystemExit, se:
            if se.code == 0:
                log.step(account_name + " 提前退出")
            else:
                log.error(account_name + " 异常退出")
            # 如果临时目录变量不为空，表示某个日志正在下载中，需要把下载了部分的内容给清理掉
            if len(self.temp_path_list) > 0:
                for temp_path in self.temp_path_list:
                    tool.remove_dir_or_file(temp_path)
        except Exception, e:
            log.error(account_name + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 保存最后的信息
        self.thread_lock.acquire()
        tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
        TOTAL_IMAGE_COUNT += total_image_count
        ACCOUNTS.remove(account_id)
        self.thread_lock.release()
        log.step(account_name + " 下载完毕，总共获得%s张图片" % total_image_count)


if __name__ == "__main__":
    GooglePlus().main()
