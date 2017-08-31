# -*- coding:UTF-8  -*-
"""
网易摄影图片爬虫
http://pp.163.com/square/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, net, robot, tool
from pyquery import PyQuery as pq
import os
import re
import threading
import time
import traceback

ACCOUNTS = []
TOTAL_IMAGE_COUNT = 0
IMAGE_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""


# 获取账号主页
def get_account_index_page(account_name):
    account_index_url = "http://%s.pp.163.com/" % account_name
    account_index_response = net.http_request(account_index_url)
    result = {
        "album_url_list": [],  # 全部相册地址
    }
    if account_index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(account_index_response.status))
    # 页面编码
    account_index_html = account_index_response.data.decode("GBK").encode("UTF-8")
    if account_index_html.find("<title>该页面不存在</title>") >= 0:
        raise robot.RobotException("账号不存在")
    # 获取全部相册地址
    album_result_selector = pq(account_index_html).find("#p_contents li")
    if album_result_selector.size() == 0:
        raise robot.RobotException("页面匹配相册列表失败\n%s" % account_index_html)
    for album_index in range(0, album_result_selector.size()):
        result["album_url_list"].append(str(album_result_selector.eq(album_index).find("a.detail").attr("href")))
    return result


# 解析相册id
def get_album_id(album_url):
    album_id = tool.find_sub_string(album_url, "pp/", ".html")
    if robot.is_integer(album_id):
        return str(album_id)
    return None


# 获取相册页
def get_album_page(album_url):
    album_response = net.http_request(album_url)
    result = {
        "album_title": "",  # 相册标题
        "image_url_list": [],  # 全部图片地址
    }
    if album_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(album_response.status))
    # 获取相册标题
    album_title = tool.find_sub_string(album_response.data, '<h2 class="picset-title" id="p_username_copy">', "</h2>").strip()
    if album_title:
        result["album_title"] = album_title.decode("GBK").encode("UTF-8")
    # 获取图片地址
    image_url_list = re.findall('data-lazyload-src="([^"]*)"', album_response.data)
    if len(image_url_list) == 0:
        raise robot.RobotException("页面匹配图片地址失败\n%s" % album_response.data)
    result["image_url_list"] = map(str, image_url_list)
    return result


class Photographer(robot.Robot):
    def __init__(self):
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

    def main(self):
        global ACCOUNTS

        # 解析存档文件
        # account_id last_album_id
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

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), TOTAL_IMAGE_COUNT))


class Download(threading.Thread):
    def __init__(self, account_info, thread_lock):
        threading.Thread.__init__(self)
        self.account_info = account_info
        self.thread_lock = thread_lock

    def run(self):
        global TOTAL_IMAGE_COUNT

        account_name = self.account_info[0]
        total_image_count = 0
        temp_path = ""

        try:
            log.step(account_name + " 开始")

            # 获取主页
            try:
                account_index_response = get_account_index_page(account_name)
            except robot.RobotException, e:
                log.error(account_name + " 主页解析失败，原因：%s" % e.message)
                raise

            log.trace(account_name + " 解析的全部相册：%s" % account_index_response["album_url_list"])

            album_url_list = []
            # 获取全部还未下载过需要解析的相册
            for album_url in account_index_response["album_url_list"]:
                # 获取相册id
                album_id = get_album_id(album_url)
                if album_id is None:
                    log.error(account_name + " 相册地址%s解析相册id失败" % album_url)
                    tool.process_exit()

                # 检查是否达到存档记录
                if int(album_id) > int(self.account_info[1]):
                    album_url_list.append(album_url)
                else:
                    break

            log.step(account_name + " 需要下载的全部相册解析完毕，共%s个" % len(album_url_list))

            # 从最早的相册开始下载
            while len(album_url_list) > 0:
                album_url = album_url_list.pop()
                album_id = get_album_id(album_url)
                log.step(account_name + " 开始解析第相册%s" % album_url)

                try:
                    album_response = get_album_page(album_url)
                except robot.RobotException, e:
                    log.error(account_name + " 相册%s解析失败，原因：%s" % (album_url, e.message))
                    raise

                log.trace(account_name + " 相册%s解析的全部图片：%s" % (album_url, album_response["image_url_list"]))

                image_index = 1
                # 过滤标题中不支持的字符
                album_title = robot.filter_text(album_response["album_title"])
                if album_title:
                    album_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name, "%s %s" % (album_id, album_title))
                else:
                    album_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name, str(album_id))
                temp_path = album_path
                for image_url in album_response["image_url_list"]:
                    log.step(account_name + " 相册%s《%s》 开始下载第%s张图片 %s" % (album_id, album_title, image_index, image_url))

                    file_type = image_url.split(".")[-1]
                    file_path = os.path.join(album_path, "%03d.%s" % (image_index, file_type))
                    save_file_return = net.save_net_file(image_url, file_path)
                    if save_file_return["status"] == 1:
                        log.step(account_name + " 相册%s《%s》 第%s张图片下载成功" % (album_id, album_title, image_index))
                        image_index += 1
                    else:
                        log.error(account_name + " 相册%s《%s》 第%s张图片 %s 下载失败，原因：%s" % (album_id, album_title, image_index, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
                # 相册内图片全部下载完毕
                temp_path = ""  # 临时目录设置清除
                total_image_count += image_index - 1  # 计数累加
                self.account_info[1] = album_id  # 设置存档记录
        except SystemExit, se:
            if se.code == 0:
                log.step(account_name + " 提前退出")
            else:
                log.error(account_name + " 异常退出")
            # 如果临时目录变量不为空，表示某个相册正在下载中，需要把下载了部分的内容给清理掉
            if temp_path:
                tool.remove_dir_or_file(temp_path)
        except Exception, e:
            log.error(account_name + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 保存最后的信息
        self.thread_lock.acquire()
        tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
        TOTAL_IMAGE_COUNT += total_image_count
        ACCOUNTS.remove(account_name)
        self.thread_lock.release()
        log.step(account_name + " 下载完毕，总共获得%s张图片" % total_image_count)


if __name__ == "__main__":
    Photographer().main()
