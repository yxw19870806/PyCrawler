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
    extra_info = {
        "album_url_list": [],  # 页面解析出的所有相册地址列表
    }
    if account_index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        album_result_selector = pq(account_index_response.data).find("#p_contents li")
        for album_index in range(0, album_result_selector.size()):
            extra_info["album_url_list"].append(str(album_result_selector.eq(album_index).find("a.detail").attr("href")))
    account_index_response.extra_info = extra_info
    return account_index_response


# 解析相册id
def get_album_id(album_url):
    album_id = tool.find_sub_string(album_url, "pp/", ".html")
    if album_id and robot.is_integer(album_id):
        return str(album_id)
    return None


# 获取相册页
def get_album_page(album_url):
    album_response = net.http_request(album_url)
    extra_info = {
        "album_title": "",  # 页面解析出的相册标题
        "image_url_list": [],  # 页面解析出的所有相册地址列表
    }
    if album_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        album_title = tool.find_sub_string(album_response.data, '<h2 class="picset-title" id="p_username_copy">', "</h2>").strip()
        if album_title:
            extra_info["album_title"] = album_title.decode("GBK").encode("UTF-8")
        image_url_list = re.findall('data-lazyload-src="([^"]*)"', album_response.data)
        if len(image_url_list) > 0:
            extra_info["image_url_list"] = map(str, image_url_list)
        album_response.extra_info = extra_info
    return album_response


class Photographer(robot.Robot):
    def __init__(self):
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        IS_SORT = self.is_sort
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

        try:
            log.step(account_name + " 开始")

            # 获取主页
            account_index_response = get_account_index_page(account_name)
            if account_index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                log.error(account_name + " 账号主页访问失败，原因：%s" % account_index_response.status)
                tool.process_exit()

            if len(account_index_response.extra_info["album_url_list"]) == 0:
                log.error(account_name + " 没有获得相册信息")
                tool.process_exit()

            log.step(account_name + " 解析的所有相册地址：%s" % account_index_response.extra_info["album_url_list"])

            # 下载
            total_image_count = 0
            album_count = 0
            first_album_id = "0"
            need_make_download_dir = True
            image_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
            for album_url in account_index_response.extra_info["album_url_list"]:
                album_id = get_album_id(album_url)
                if album_id is None:
                    log.error(account_name + " 相册地址 %s 解析相册id失败" % album_url)
                    tool.process_exit()

                # 检查是否相册id小于上次的记录
                if int(album_id) <= int(self.account_info[1]):
                    break

                # 将第一个相册的id做为新的存档记录
                if first_album_id == "0":
                    first_album_id = album_id

                log.step(account_name + " 开始解析第相册%s" % album_id)

                album_response = get_album_page(album_url)
                if album_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                    log.error(account_name + " 相册 %s 访问失败，原因：%s" % (album_url, account_index_response.status))
                    tool.process_exit()

                if len(album_response.extra_info["image_url_list"]) == 0:
                    log.error(account_name + " 相册 %s 解析图片地址失败" % album_url)
                    tool.process_exit()

                log.step(account_name + " 相册%s解析的所有图片地址：%s" % (album_id, album_response.extra_info["image_url_list"]))

                if need_make_download_dir:
                    if not tool.make_dir(image_path, 0):
                        log.error(account_name + " 创建下载目录 %s 失败" % image_path)
                        tool.process_exit()
                    need_make_download_dir = False

                # 过滤标题中不支持的字符
                album_title = robot.filter_text(album_response.extra_info["album_title"])
                if album_title:
                    album_path = os.path.join(image_path, "%s %s" % (album_id, album_title))
                else:
                    album_path = os.path.join(image_path, str(album_id))
                if not tool.make_dir(album_path, 0):
                    # 目录出错，把title去掉后再试一次，如果还不行退出
                    log.error(account_name + " 创建相册目录 %s 失败，尝试不使用title" % album_path)
                    album_path = os.path.join(image_path, album_id)
                    if not tool.make_dir(album_path, 0):
                        log.error(account_name + " 创建相册目录 %s 失败" % album_path)
                        tool.process_exit()

                image_count = 1
                for image_url in album_response.extra_info["image_url_list"]:
                    log.step(account_name + " 相册%s 《%s》 开始下载第%s张图片 %s" % (album_id, album_title, image_count, image_url))

                    file_type = image_url.split(".")[-1]
                    file_path = os.path.join(album_path, "%03d.%s" % (image_count, file_type))
                    save_file_return = net.save_net_file(image_url, file_path)
                    if save_file_return["status"] == 1:
                        log.step(account_name + " 相册%s 《%s》 第%s张图片下载成功" % (album_id, album_title, image_count))
                        image_count += 1
                    else:
                        log.error(account_name + " 相册%s 《%s》 第%s张图片 %s 下载失败，原因：%s" % (album_id, album_title, image_count, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
                total_image_count += image_count - 1
                album_count += 1

            log.step(account_name + " 下载完毕，总共获得%s张图片" % total_image_count)

            # 新的存档记录
            if first_album_id != "0":
                self.account_info[1] = first_album_id

            # 保存最后的信息
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            self.thread_lock.acquire()
            TOTAL_IMAGE_COUNT += total_image_count - 1
            ACCOUNTS.remove(account_name)
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
    Photographer().main()
