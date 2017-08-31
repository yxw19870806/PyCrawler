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
IMAGE_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""


# 获取指定页数的全部日志
def get_one_page_blog(account_name, page_count):
    # http://moexia.lofter.com/?page=1
    blog_pagination_url = "http://%s.lofter.com/?page=%s" % (account_name, page_count)
    blog_pagination_response = net.http_request(blog_pagination_url)
    result = {
        "blog_url_list": [],  # 全部日志地址
    }
    if blog_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 获取全部日志地址
        blog_url_list = re.findall('"(http://' + account_name + '.lofter.com/post/[^"]*)"', blog_pagination_response.data)
        # 去重排序
        result["blog_url_list"] = sorted(list(set(blog_url_list)), reverse=True)
    elif page_count == 1 and blog_pagination_response.status == 404:
        raise robot.RobotException("账号不存在")
    else:
        raise robot.RobotException(robot.get_http_request_failed_reason(blog_pagination_response.status))
    return result


# 获取日志
def get_blog_page(blog_url):
    blog_response = net.http_request(blog_url)
    result = {
        "image_url_list": [],  # 全部图片地址
    }
    if blog_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(blog_response.status))
    # 获取全部图片地址
    image_url_list = re.findall('bigimgsrc="([^"]*)"', blog_response.data)
    result["image_url_list"] = map(str, image_url_list)
    return result


# 从日志地址中解析出日志id
def get_blog_id(blog_url):
    return blog_url.split("/")[-1].split("_")[-1]


# 去除图片的参数
def get_image_url(image_url):
     if image_url.rfind("?") > image_url.rfind("."):
        return image_url.split("?")[0]
     return image_url


class Lofter(robot.Robot):
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
        total_image_count = 0
        temp_path_list = []

        try:
            log.step(account_name + " 开始")

            page_count = 1
            unique_list = []
            blog_url_list = []
            is_over = False
            # 获取全部还未下载过需要解析的日志
            while not is_over:
                log.step(account_name + " 开始解析第%s页日志" % page_count)

                try:
                    blog_pagination_response = get_one_page_blog(account_name, page_count)
                except robot.RobotException, e:
                    log.error(account_name + " 第%s页日志解析失败，原因：%s" % (page_count, e.message))
                    raise

                # 下载完毕了
                if len(blog_pagination_response["blog_url_list"]) == 0:
                    break

                log.trace(account_name + " 第%s页解析的全部日志：%s" % (page_count, blog_pagination_response["blog_url_list"]))

                # 寻找这一页符合条件的日志
                for blog_url in blog_pagination_response["blog_url_list"]:
                    blog_id = get_blog_id(blog_url)

                    # 新增日志导致的重复判断
                    if blog_id in unique_list:
                        continue
                    else:
                        unique_list.append(blog_id)

                    # 检查是否达到存档记录
                    if blog_id > self.account_info[2]:
                        blog_url_list.append(blog_url)
                    else:
                        is_over = True
                        break

                if not is_over:
                    page_count += 1

            log.step("需要下载的全部日志解析完毕，共%s个" % len(blog_url_list))

            # 从最早的日志开始下载
            while len(blog_url_list) > 0:
                blog_url = blog_url_list.pop()
                log.step(account_name + " 开始解析日志 %s" % blog_url)

                # 获取日志
                try:
                    blog_response = get_blog_page(blog_url)
                except robot.RobotException, e:
                    log.error(account_name + " 日志 %s 解析失败，原因：%s" % (blog_url, e.message))
                    raise

                # 获取图片下载地址列表
                if len(blog_response["image_url_list"]) == 0:
                    log.error(account_name + " 日志 %s 中没有找到图片" % blog_url)
                    continue

                log.trace(account_name + " 日志 %s 解析的全部图片：%s" % (blog_url, blog_response["image_url_list"]))

                image_index = int(self.account_info[1]) + 1
                for image_url in blog_response["image_url_list"]:
                    # 去除图片地址的参数
                    image_url = get_image_url(image_url)
                    log.step(account_name + " 开始下载第%s张图片 %s" % (image_index, image_url))

                    file_type = image_url.split(".")[-1]
                    file_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name, "%04d.%s" % (image_index, file_type))
                    save_file_return = net.save_net_file(image_url, file_path)
                    if save_file_return["status"] == 1:
                        temp_path_list.append(file_path)
                        log.step(account_name + " 第%s张图片下载成功" % image_index)
                        image_index += 1
                    else:
                        log.error(account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_index, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
                # 日志内图片全部下载完毕
                temp_path_list = []  # 临时目录设置清除
                total_image_count += (image_index - 1) - int(self.account_info[1])  # 计数累加
                self.account_info[1] = str(image_index - 1)  # 设置存档记录
                self.account_info[2] = get_blog_id(blog_url)  # 设置存档记录
        except SystemExit, se:
            if se.code == 0:
                log.step(account_name + " 提前退出")
            else:
                log.error(account_name + " 异常退出")
            # 如果临时目录变量不为空，表示某个日志正在下载中，需要把下载了部分的内容给清理掉
            if len(temp_path_list) > 0:
                for temp_path in temp_path_list:
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
    Lofter().main()
