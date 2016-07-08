# -*- coding:UTF-8  -*-
"""
Twitter图片爬虫
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, robot, tool
import json
import os
import re
import threading
import time
import traceback
import urllib2

ACCOUNTS = []
INIT_MAX_ID = "999999999999999999"
TOTAL_IMAGE_COUNT = 0
GET_IMAGE_COUNT = 0
IMAGE_TEMP_PATH = ""
IMAGE_DOWNLOAD_PATH = ""
VIDEO_TEMP_PATH = ""
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_SORT = 1
IS_DOWNLOAD_IMAGE = 1

threadLock = threading.Lock()


def print_error_msg(msg):
    threadLock.acquire()
    log.error(msg)
    threadLock.release()


def print_step_msg(msg):
    threadLock.acquire()
    log.step(msg)
    threadLock.release()


def trace(msg):
    threadLock.acquire()
    log.trace(msg)
    threadLock.release()


# 获取一页的图片信息
def get_twitter_media_page_data(account_id, data_tweet_id):
    media_page_url = "https://twitter.com/i/profiles/show/%s/media_timeline?include_available_features=1" \
                     "&include_entities=1&max_position=%s" % (account_id, data_tweet_id)
    [media_page_return_code, media_page_response] = tool.http_request(media_page_url)[:2]
    if media_page_return_code == 1:
        try:
            media_page = json.loads(media_page_response)
        except ValueError:
            pass
        else:
            if robot.check_sub_key(("has_more_items", "items_html", "min_position"), media_page):
                return media_page
    return None


# 返回的是当前时区对应的时间
def get_image_last_modified(response):
    if isinstance(response, urllib2.addinfourl):
        info = response.info()
        last_modified_time = tool.get_response_info(info, "last-modified")
        last_modified_time = time.strptime(last_modified_time, "%a, %d %b %Y %H:%M:%S %Z")
        return int(time.mktime(last_modified_time)) - time.timezone
    return 0


# 将图片的二进制数据保存为本地文件
def save_image(image_byte, image_path):
    image_path = tool.change_path_encoding(image_path)
    image_file = open(image_path, "wb")
    image_file.write(image_byte)
    image_file.close()


class Twitter(robot.Robot):
    def __init__(self, save_data_path="", this_image_download_path="", this_image_temp_path=""):
        global GET_IMAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT
        global IS_DOWNLOAD_IMAGE

        robot.Robot.__init__(self)

        if save_data_path != "":
            self.save_data_path = save_data_path

        GET_IMAGE_COUNT = self.get_image_count
        if this_image_temp_path != "":
            IMAGE_TEMP_PATH = this_image_temp_path
        else:
            IMAGE_TEMP_PATH = self.image_temp_path
        if this_image_download_path != "":
            IMAGE_DOWNLOAD_PATH = this_image_download_path
        else:
            IMAGE_DOWNLOAD_PATH = self.image_download_path
        IS_SORT = self.is_sort
        IS_DOWNLOAD_IMAGE = self.is_download_image
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

        tool.print_msg("配置文件读取完成")

    def main(self):
        global ACCOUNTS
        
        if IS_DOWNLOAD_IMAGE == 0:
            print_error_msg("下载图片没开启，请检查配置！")
            tool.process_exit()

        start_time = time.time()

        # 图片保存目录
        print_step_msg("创建图片根目录：" + IMAGE_DOWNLOAD_PATH)
        if not tool.make_dir(IMAGE_DOWNLOAD_PATH, 0):
            print_error_msg("创建图片根目录：" + IMAGE_DOWNLOAD_PATH + " 失败")
            tool.process_exit()

        # 设置代理
        if self.is_proxy == 1 or self.is_proxy == 2:
            tool.set_proxy(self.proxy_ip, self.proxy_port, "https")

        # 寻找idlist，如果没有结束进程
        account_list = {}
        if os.path.exists(self.save_data_path):
            # account_id  image_count  last_image_time
            account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0"])
            ACCOUNTS = account_list.keys()
        else:
            print_error_msg("用户ID存档文件: " + self.save_data_path + "不存在")
            tool.process_exit()

        # 创建临时存档文件
        new_save_data_file = open(NEW_SAVE_DATA_PATH, "w")
        new_save_data_file.close()

        # 启用线程监控是否需要暂停其他下载线程
        process_control_thread = tool.ProcessControl()
        process_control_thread.setDaemon(True)
        process_control_thread.start()

        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for account_id in sorted(account_list.keys()):
            # 检查正在运行的线程数
            while threading.activeCount() >= self.thread_count + main_thread_count:
                if tool.is_process_end() == 0:
                    time.sleep(10)
                else:
                    break

            # 提前结束
            if tool.is_process_end() > 0:
                break

            # 开始下载
            thread = Download(account_list[account_id])
            thread.start()

            time.sleep(1)

        # 检查除主线程外的其他所有线程是不是全部结束了
        while threading.activeCount() > main_thread_count:
            time.sleep(10)

        # 未完成的数据保存
        if len(ACCOUNTS) > 0:
            new_save_data_file = open(NEW_SAVE_DATA_PATH, "a")
            for account_id in ACCOUNTS:
                # account_id  image_count  last_image_time
                new_save_data_file.write("\t".join(account_list[account_id]) + "\n")
            new_save_data_file.close()

        # 删除临时文件夹
        tool.remove_dir(IMAGE_TEMP_PATH)

        # 重新排序保存存档文件
        account_list = robot.read_save_data(NEW_SAVE_DATA_PATH, 0, [])
        temp_list = [account_list[key] for key in sorted(account_list.keys())]
        tool.write_file(tool.list_to_string(temp_list), self.save_data_path, 2)
        os.remove(NEW_SAVE_DATA_PATH)

        duration_time = int(time.time() - start_time)
        print_step_msg("全部下载完毕，耗时" + str(duration_time) + "秒，共计图片" + str(TOTAL_IMAGE_COUNT) + "张")


class Download(threading.Thread):
    def __init__(self, account_info):
        threading.Thread.__init__(self)
        self.account_info = account_info

    def run(self):
        global TOTAL_IMAGE_COUNT

        account_id = self.account_info[0]

        try:
            print_step_msg(account_id + " 开始")

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if IS_SORT == 1:
                image_path = os.path.join(IMAGE_TEMP_PATH, account_id)
            else:
                image_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_id)

            # 图片下载
            image_count = 1
            data_tweet_id = INIT_MAX_ID
            first_image_time = "0"
            is_over = False
            need_make_download_dir = True
            while not is_over:
                # 获取指定时间点后的一页图片信息
                media_page = get_twitter_media_page_data(account_id, data_tweet_id)
                if media_page is None:
                    print_error_msg(account_id + " 图片列表解析错误")
                    break

                # 匹配获取全部的图片地址
                this_page_image_url_list = re.findall('data-image-url="([^"]*)"', media_page["items_html"])
                trace(account_id + " data_tweet_id：" + data_tweet_id + " 的全部图片列表" + str(this_page_image_url_list))
                for image_url in this_page_image_url_list:
                    image_url = str(image_url)
                    print_step_msg(account_id + " 开始下载第 " + str(image_count) + "张图片：" + image_url)

                    # todo 是否可以优化到一个方法中
                    [image_return_code, image_response_data, image_response] = tool.http_request(image_url)
                    # 404，不算做错误，图片已经被删掉了
                    if image_return_code == -404:
                        print_error_msg(account_id + " 第" + str(image_count) + "张图片 " + image_url + "已被删除，跳过")
                    elif image_return_code == 1:
                        image_time = get_image_last_modified(image_response)
                        # 将第一张图片的上传时间做为新的存档记录
                        if first_image_time == "0":
                            first_image_time = str(image_time)
                        # 检查是否图片时间小于上次的记录
                        if image_time <= int(self.account_info[2]):
                            is_over = True
                            break

                        file_type = image_url.split(".")[-1].split(":")[0]
                        file_path = os.path.join(image_path, str("%04d" % image_count) + "." + file_type)
                        # 第一张图片，创建目录
                        if need_make_download_dir:
                            if not tool.make_dir(image_path, 0):
                                print_error_msg(account_id + " 创建图片下载目录： " + image_path + " 失败")
                                tool.process_exit()
                            need_make_download_dir = False
                        save_image(image_response_data, file_path)
                        print_step_msg(account_id + " 第" + str(image_count) + "张图片下载成功")
                        image_count += 1
                    else:
                        print_error_msg(account_id + " 第" + str(image_count) + "张图片 " + image_url + " 获取失败")

                    # 达到配置文件中的下载数量，结束
                    if 0 < GET_IMAGE_COUNT < image_count:
                        is_over = True
                        break

                if not is_over:
                    # 查找下一页的data_tweet_id
                    if media_page["has_more_items"]:
                        data_tweet_id = str(media_page["min_position"])
                    else:
                        is_over = True

            print_step_msg(account_id + " 下载完毕，总共获得" + str(image_count - 1) + "张图片")

            # 排序
            if IS_SORT == 1 and image_count > 1:
                destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_id)
                if robot.sort_file(image_path, destination_path, int(self.account_info[1]), 4):
                    print_step_msg(account_id + " 图片从下载目录移动到保存目录成功")
                else:
                    print_error_msg(account_id + " 创建图片子目录： " + destination_path + " 失败")
                    tool.process_exit()

            # 新的存档记录
            if first_image_time != "0":
                self.account_info[1] = str(int(self.account_info[1]) + image_count - 1)
                self.account_info[2] = first_image_time

            # 保存最后的信息
            threadLock.acquire()
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            TOTAL_IMAGE_COUNT += image_count - 1
            ACCOUNTS.remove(account_id)
            threadLock.release()

            print_step_msg(account_id + " 完成")
        except SystemExit:
            print_error_msg(account_id + " 异常退出")
        except Exception, e:
            print_step_msg(account_id + " 未知异常")
            print_error_msg(str(e) + "\n" + str(traceback.print_exc()))


if __name__ == "__main__":
    tool.restore_process_status()
    Twitter().main()
