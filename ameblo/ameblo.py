# -*- coding:UTF-8  -*-
"""
ameblo图片爬虫
http://ameblo.jp/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, robot, tool
import os
import re
import threading
import time
import traceback

ACCOUNTS = []
IMAGE_COUNT_PER_PAGE = 20
TOTAL_IMAGE_COUNT = 0
GET_IMAGE_COUNT = 0
IMAGE_TEMP_PATH = ""
IMAGE_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_SORT = True
IS_DOWNLOAD_IMAGE = True
IS_DOWNLOAD_VIDEO = True

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


# 获取指定页数的日志信息
def get_blog_page_data(account_name, page_count):
    blog_url = "http://ameblo.jp/%s/page-%s.html" % (account_name, page_count)
    blog_return_code, blog_page, info = tool.http_request(blog_url)
    if blog_return_code == 1:
        return blog_page
    return None


# 解析日志发布时间
def get_blog_time(blog_page):
    blog_time_info = tool.find_sub_string(blog_page, '<span class="articleTime">', "</span>")
    if blog_time_info:
        blog_time_string = tool.find_sub_string(blog_page, 'pubdate="pubdate">', "</time>").strip()
        blog_timestamp = time.strptime(blog_time_string, "%Y-%m-%d %H:%M:%S")
        # 显示时间对应的时间戳，服务器的时区（日本），不对本地时间做转换
        return int(time.mktime(blog_timestamp))
    return None


# 从日志列表中获取全部的图片，并过滤掉表情
def get_image_url_list(blog_page):
    blog_page = tool.find_sub_string(blog_page, '<div class="articleText">', "<!--entryBottom-->", 1)
    image_url_list_find = re.findall('<img [\S|\s]*?src="([^"]*)" [\S|\s]*?>', blog_page)
    image_url_list = []
    for image_url in image_url_list_find:
        # 过滤表情
        if image_url.find(".ameba.jp/blog/ucs/") == -1:
            image_url_list.append(image_url)
    return image_url_list


class Ameblo(robot.Robot):
    def __init__(self):
        global GET_IMAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT
        global IS_DOWNLOAD_IMAGE
        global IS_DOWNLOAD_VIDEO

        robot.Robot.__init__(self)

        # 设置全局变量，供子线程调用
        GET_IMAGE_COUNT = self.get_image_count
        IMAGE_TEMP_PATH = self.image_temp_path
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        IS_SORT = self.is_sort
        IS_DOWNLOAD_IMAGE = self.is_download_image
        IS_DOWNLOAD_VIDEO = self.is_download_video
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

        tool.print_msg("配置文件读取完成")

    def main(self):
        global ACCOUNTS

        if not IS_DOWNLOAD_IMAGE and not IS_DOWNLOAD_VIDEO:
            print_error_msg("下载图片和视频都没有开启，请检查配置！")
            tool.process_exit()

        start_time = time.time()

        # 创建图片保存目录
        if IS_DOWNLOAD_IMAGE:
            print_step_msg("创建图片根目录 %s" % IMAGE_DOWNLOAD_PATH)
            if not tool.make_dir(IMAGE_DOWNLOAD_PATH, 0):
                print_error_msg("创建图片根目录 %s 失败" % IMAGE_DOWNLOAD_PATH)
                tool.process_exit()

        # 寻找idlist，如果没有结束进程
        account_list = {}
        if os.path.exists(self.save_data_path):
            # account_name  image_count  last_diary_time
            account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0"])
            ACCOUNTS = account_list.keys()
        else:
            print_error_msg("用户ID存档文件 %s 不存在" % self.save_data_path)
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
        for account_name in sorted(account_list.keys()):
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
            thread = Download(account_list[account_name])
            thread.start()

            time.sleep(1)

        # 检查除主线程外的其他所有线程是不是全部结束了
        while threading.activeCount() > main_thread_count:
            time.sleep(10)

        # 未完成的数据保存
        if len(ACCOUNTS) > 0:
            new_save_data_file = open(NEW_SAVE_DATA_PATH, "a")
            for account_name in ACCOUNTS:
                # account_name  image_count  last_blog_time
                new_save_data_file.write("\t".join(account_list[account_name]) + "\n")
            new_save_data_file.close()

        # 删除临时文件夹
        tool.remove_dir(IMAGE_TEMP_PATH)

        # 重新排序保存存档文件
        account_list = robot.read_save_data(NEW_SAVE_DATA_PATH, 0, [])
        temp_list = [account_list[key] for key in sorted(account_list.keys())]
        tool.write_file(tool.list_to_string(temp_list), self.save_data_path, 2)
        os.remove(NEW_SAVE_DATA_PATH)

        duration_time = int(time.time() - start_time)
        print_step_msg("全部下载完毕，耗时%s秒，共计图片%s张" % (duration_time, TOTAL_IMAGE_COUNT))


class Download(threading.Thread):
    def __init__(self, account_info):
        threading.Thread.__init__(self)
        self.account_info = account_info

    def run(self):
        global TOTAL_IMAGE_COUNT

        account_name = self.account_info[0]

        try:
            print_step_msg(account_name + " 开始")

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if IS_SORT:
                image_path = os.path.join(IMAGE_TEMP_PATH, account_name)
            else:
                image_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)

            image_count = 1
            page_count = 1
            first_blog_time = "0"
            is_over = False
            need_make_image_dir = True
            while not is_over:
                # 获取一页日志
                blog_data = get_blog_page_data(account_name, page_count)
                if blog_data is None:
                    print_error_msg(account_name + " 第%s页日志无法获取" % page_count)
                    tool.process_exit()

                # 解析日志发布时间
                blog_time = get_blog_time(blog_data)
                if blog_time is None:
                    print_error_msg(account_name + " 第%s页日志无法解析日志时间" % page_count)
                    tool.process_exit()

                # 检查是否是上一次的最后blog
                if blog_time <= int(self.account_info[2]):
                    break

                # 将第一个日志的时间做为新的存档记录
                if first_blog_time == "0":
                    first_blog_time = str(blog_time)

                # 从日志列表中获取全部的图片
                image_url_list = get_image_url_list(blog_data)
                for image_url in image_url_list:
                    # 使用默认图片的分辨率
                    image_url = image_url.split("?")[0]
                    print_step_msg(account_name + " 开始下载第%s张图片 %s" % (image_count, image_url))

                    # 第一张图片，创建目录
                    if need_make_image_dir:
                        if not tool.make_dir(image_path, 0):
                            print_error_msg(account_name + " 创建图片下载目录 %s 失败" % image_path)
                            tool.process_exit()
                        need_make_image_dir = False
                    file_type = image_url.split(".")[-1]
                    file_path = os.path.join(image_path, "%04d.%s" % (image_count, file_type))
                    if tool.save_net_file(image_url, file_path):
                        print_step_msg(account_name + " 第%s张图片下载成功" % image_count)
                        image_count += 1
                    else:
                        print_error_msg(account_name + " 第%s张图片 %s 获取失败" % (image_count, image_url))

                # 达到配置文件中的下载数量，结束
                if 0 < GET_IMAGE_COUNT < image_count:
                    is_over = True

                if not is_over:
                    page_count += 1

            print_step_msg(account_name + " 下载完毕，总共获得%s张图片" % (image_count - 1))

            # 排序
            if IS_SORT and image_count > 1:
                destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
                if robot.sort_file(image_path, destination_path, int(self.account_info[1]), 4):
                    print_step_msg(account_name + " 图片从下载目录移动到保存目录成功")
                else:
                    print_error_msg(account_name + " 创建图片子目录 %s 失败" % destination_path)
                    tool.process_exit()

            # 新的存档记录
            if first_blog_time != "0":
                self.account_info[1] = str(int(self.account_info[1]) + image_count - 1)
                self.account_info[2] = first_blog_time

            # 保存最后的信息
            threadLock.acquire()
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            TOTAL_IMAGE_COUNT += image_count - 1
            ACCOUNTS.remove(account_name)
            threadLock.release()

            print_step_msg(account_name + " 完成")
        except SystemExit, se:
            if se.code == 0:
                print_step_msg(account_name + " 提前退出")
            else:
                print_error_msg(account_name + " 异常退出")
        except Exception, e:
            print_error_msg(account_name + " 未知异常")
            print_error_msg(str(e) + "\n" + str(traceback.format_exc()))


if __name__ == "__main__":
    Ameblo().main()
