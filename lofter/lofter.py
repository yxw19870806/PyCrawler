# -*- coding:UTF-8  -*-
"""
lofter图片爬虫
http://www.lofter.com/
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
GET_PAGE_COUNT = 0
GET_IMAGE_COUNT = 0
IMAGE_TEMP_PATH = ""
IMAGE_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_SORT = True


# 获取指定页数的所有日志
def get_one_page_blog(account_name, page_count):
    # http://moexia.lofter.com/?page=1
    blog_pagination_url = "http://%s.lofter.com/?page=%s" % (account_name, page_count)
    blog_pagination_response = net.http_request(blog_pagination_url)
    extra_info = {
        "blog_url_list": [],  # 页面解析出的所有日志列表
    }
    if blog_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 获取页面中所有的日志地址列表
        blog_url_list = re.findall('"(http://' + account_name + '.lofter.com/post/[^"]*)"', blog_pagination_response.data)
        # 去重排序
        extra_info["blog_url_list"] = sorted(list(set(blog_url_list)), reverse=True)
    blog_pagination_response.extra_info = extra_info
    return blog_pagination_response


# 获取日志
def get_blog_page(blog_url):
    blog_response = net.http_request(blog_url)
    extra_info = {
        "image_url_list": [],  # 页面解析出的所有图片列表
    }
    if blog_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        image_url_list = re.findall('bigimgsrc="([^"]*)"', blog_response.data)
        extra_info["image_url_list"] = map(str, image_url_list)
    blog_response.extra_info = extra_info
    return blog_response


class Lofter(robot.Robot):
    def __init__(self):
        global GET_PAGE_COUNT
        global GET_IMAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        GET_PAGE_COUNT = self.get_page_count
        GET_IMAGE_COUNT = self.get_image_count
        IMAGE_TEMP_PATH = self.image_temp_path
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        IS_SORT = self.is_sort
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

    def main(self):
        global ACCOUNTS

        # 解析存档文件
        # account_name  image_count  last_blog_id
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", ""])
        ACCOUNTS = account_list.keys()

        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for account_name in sorted(account_list.keys()):
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
            thread = Download(account_list[account_name], self.thread_lock)
            thread.start()

            time.sleep(1)

        # 检查除主线程外的其他所有线程是不是全部结束了
        while threading.activeCount() > main_thread_count:
            time.sleep(10)

        # 未完成的数据保存
        if len(ACCOUNTS) > 0:
            new_save_data_file = open(NEW_SAVE_DATA_PATH, "a")
            for account_name in ACCOUNTS:
                new_save_data_file.write("\t".join(account_list[account_name]) + "\n")
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

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if IS_SORT:
                image_path = os.path.join(IMAGE_TEMP_PATH, account_name)
            else:
                image_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)

            # 图片下载
            page_count = 1
            image_count = 1
            first_blog_id = ""
            unique_list = []
            is_over = False
            need_make_download_dir = True
            while not is_over:
                log.step(account_name + " 开始解析第%s页日志" % page_count)

                blog_pagination_response = get_one_page_blog(account_name, page_count)
                if blog_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                    log.error(account_name + " 第%s页日志访问失败，原因：%s" % (page_count, robot.get_http_request_failed_reason(blog_pagination_response.status)))
                    tool.process_exit()

                if len(blog_pagination_response.extra_info["blog_url_list"]) == 0:
                    # 下载完毕了
                    break

                log.trace(account_name + " 第%s页去重排序后的日志：%s" % (page_count, blog_pagination_response.extra_info["blog_url_list"]))

                for blog_url in blog_pagination_response.extra_info["blog_url_list"]:
                    blog_id = blog_url.split("/")[-1].split("_")[-1]

                    # 检查是否已下载到前一次的日志
                    if blog_id <= self.account_info[2]:
                        is_over = True
                        break

                    # 将第一个日志的id做为新的存档记录
                    if first_blog_id == "":
                        first_blog_id = blog_id

                    # 新增日志导致的重复判断
                    if blog_id in unique_list:
                        continue
                    else:
                        unique_list.append(blog_id)

                    log.step(account_name + " 开始解析日志 %s" % blog_url)

                    # 获取日志
                    blog_response = get_blog_page(blog_url)
                    if blog_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                        log.error(account_name + " 日志 %s 访问失败，原因：%s" % (blog_url, robot.get_http_request_failed_reason(blog_response.status)))
                        continue

                    # 获取图片下载地址列表
                    if len(blog_response.extra_info["image_url_list"]) == 0:
                        log.error(account_name + " 日志 %s 中没有找到图片" % blog_url)
                        continue

                    log.trace(account_name + " 日志 %s 解析的所有图片：%s" % (blog_url, blog_response.extra_info["image_url_list"]))

                    for image_url in blog_response.extra_info["image_url_list"]:
                        if image_url.rfind("?") > image_url.rfind("."):
                            image_url = image_url.split("?")[0]
                        log.step(account_name + " 开始下载第%s张图片 %s" % (image_count, image_url))

                        # 第一张图片，创建目录
                        if need_make_download_dir:
                            if not tool.make_dir(image_path, 0):
                                log.error(account_name + " 创建图片下载目录 %s 失败" % image_path)
                                tool.process_exit()
                            need_make_download_dir = False

                        file_type = image_url.split(".")[-1]
                        file_path = os.path.join(image_path, "%04d.%s" % (image_count, file_type))
                        save_file_return = net.save_net_file(image_url, file_path)
                        if save_file_return["status"] == 1:
                            log.step(account_name + " 第%s张图片下载成功" % image_count)
                            image_count += 1
                        else:
                            log.error(account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_count, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

                        # 达到配置文件中的下载数量，结束
                        if 0 < GET_IMAGE_COUNT < image_count:
                            is_over = True
                            break

                    if is_over:
                        break

                if not is_over:
                    # 达到配置文件中的下载数量，结束
                    if 0 < GET_PAGE_COUNT <= page_count:
                        is_over = True
                    else:
                        page_count += 1

            log.step(account_name + " 下载完毕，总共获得%s张图片" % (image_count - 1))

            # 排序
            if IS_SORT and image_count > 1:
                log.step(account_name + " 图片开始从下载目录移动到保存目录")
                destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
                if robot.sort_file(image_path, destination_path, int(self.account_info[1]), 4):
                    log.step(account_name + " 图片从下载目录移动到保存目录成功")
                else:
                    log.error(account_name + " 创建图片子目录 %s 失败" % destination_path)
                    tool.process_exit()

            # 新的存档记录
            if first_blog_id != "":
                self.account_info[1] = str(int(self.account_info[1]) + image_count - 1)
                self.account_info[2] = first_blog_id

            # 保存最后的信息
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            self.thread_lock.acquire()
            TOTAL_IMAGE_COUNT += image_count - 1
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
    Lofter().main()
