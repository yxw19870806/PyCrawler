# -*- coding:UTF-8  -*-
"""
乃木坂46 OFFICIAL BLOG图片爬虫
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
TOTAL_IMAGE_COUNT = 0
GET_IMAGE_COUNT = 0
IMAGE_TEMP_PATH = ""
IMAGE_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_SORT = True
IS_DOWNLOAD_IMAGE = True


# 获取成员指定页数的一页日志信息
# account_id -> asuka.saito
def get_one_page_blog(account_id, page_count):
    # http://blog.nogizaka46.com/asuka.saito
    blog_url = "http://blog.nogizaka46.com/%s/?p=%s" % (account_id, page_count)
    blog_return_code, blog_page = tool.http_request(blog_url)[:2]
    if blog_return_code == 1:
        return tool.find_sub_string(blog_page, '<div class="paginate">', '<div class="paginate">', 1)
    return None


# 获取页面中的所有日志内容列表
def get_blog_data_list(blog_page):
    blog_data_list = blog_page.split('<h1 class="clearfix">')
    if len(blog_data_list) > 0:
        # 第一位不是日志内容，没有用
        blog_data_list.pop(0)
    return blog_data_list


# 解析日志页面，获取日志最大页数
def get_max_page_count(blog_page):
    paginate_data = tool.find_sub_string(blog_page, '<div class="paginate">', '</div>')
    page_count_find = re.findall('"\?p=(\d+)"', paginate_data)
    return max(map(int, page_count_find))


# 解析日志页面，获取日志id
def get_blog_id(account_id, blog_data):
    # <a href="http://blog.nogizaka46.com/asuka.saito/2016/10/035004.php"
    blog_id_info = tool.find_sub_string(blog_data, '<a href="http://blog.nogizaka46.com/%s/' % account_id, '.php"')
    if blog_id_info:
        return int(blog_id_info.split("/")[-1])
    return None


# 获取日志中的全部图片地址列表
def get_image_url_list(blog_data):
    return re.findall('src="([^"]*)"', blog_data)


# 获取日志中存在的所有大图显示地址，以及对应的小图地址
def get_big_image_url_list(blog_data):
    big_image_list_find = re.findall('<a href="([^"]*)"><img src="([^"]*)"', blog_data)
    big_2_small_list = {}
    for big_image_url, small_image_url in big_image_list_find:
        big_2_small_list[small_image_url] = big_image_url
    return big_2_small_list


# 检查图片是否存在对应的大图，以及判断大图是否仍然有效，如果存在可下载的大图则返回大图地址，否则返回原图片地址
def check_big_image(image_url, big_2_small_list):
    if image_url in big_2_small_list:
        big_image_display_page_return_code, big_image_display_page = tool.http_request(big_2_small_list[image_url])[:2]
        if big_image_display_page_return_code == 1:
            temp_image_url = tool.find_sub_string(big_image_display_page, '<img src="', '"')
            if temp_image_url != "/img/expired.gif":
                return temp_image_url
    return image_url


class Template(robot.Robot):
    def __init__(self):
        global GET_IMAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT
        global IS_DOWNLOAD_IMAGE

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_SET_COOKIE: (),
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        GET_IMAGE_COUNT = self.get_image_count
        IMAGE_TEMP_PATH = self.image_temp_path
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        IS_SORT = self.is_sort
        IS_DOWNLOAD_IMAGE = self.is_download_image
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

        tool.print_msg("配置文件读取完成")

    def main(self):
        global ACCOUNTS

        # 解析存档文件
        # account_id  image_count  last_blog_time
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
        tool.remove_dir(IMAGE_TEMP_PATH)

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

        try:
            log.step(account_name + " 开始")

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if IS_SORT:
                image_path = os.path.join(IMAGE_TEMP_PATH, account_name)
            else:
                image_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)

            # 图片
            image_count = 1
            page_count = 1
            first_blog_id = "0"
            need_make_image_dir = True
            is_over = False
            while not is_over:
                # 获取一页日志信息
                blog_page = get_one_page_blog(account_id, page_count)
                if blog_page is None:
                    log.error(account_name + " 第%s页日志获取失败" % page_count)
                    tool.process_exit()
                if not blog_page:
                    log.error(account_name + " 第%s页日志解析失败" % page_count)
                    tool.process_exit()

                blog_data_list = get_blog_data_list(blog_page)
                if len(blog_data_list) == 0:
                    log.error(account_name + " 第%s页日志分组失败" % page_count)
                    tool.process_exit()

                for blog_data in blog_data_list:
                    # 获取日志id
                    blog_id = get_blog_id(account_id, blog_data)
                    if blog_id is None:
                        log.error(account_name + " 日志解析日志id失败，日志内容：%s" % blog_data)
                        tool.process_exit()

                    # 检查是否已下载到前一次的日志
                    if blog_id <= int(self.account_info[2]):
                        is_over = True
                        break

                    # 将第一个日志的ID做为新的存档记录
                    if first_blog_id == "0":
                        first_blog_id = str(blog_id)

                    # 获取该页日志的全部图片地址列表
                    image_url_list = get_image_url_list(blog_data)
                    if len(image_url_list) == 0:
                        log.error(account_name + " 第%s页日志获取失败" % page_count)
                        tool.process_exit()

                    # 获取日志页面中存在的所有大图显示地址，以及对应的小图地址
                    big_2_small_list = get_big_image_url_list(blog_data)

                    # 下载图片
                    for image_url in image_url_list:
                        # 检查是否存在大图可以下载
                        image_url = check_big_image(image_url, big_2_small_list)
                        log.step(account_name + " 开始下载第%s张图片 %s" % (image_count, image_url))

                        # 第一张图片，创建目录
                        if need_make_image_dir:
                            if not tool.make_dir(image_path, 0):
                                log.error(account_name + " 创建图片下载目录 %s 失败" % image_path)
                                tool.process_exit()
                            need_make_image_dir = False

                        file_type = image_url.split(".")[-1]
                        if file_type.find("?") != -1:
                            file_type = "jpeg"
                        file_path = os.path.join(image_path, "%04d.%s" % (image_count, file_type))
                        if tool.save_net_file(image_url, file_path):
                            log.step(account_name + " 第%s张图片下载成功" % image_count)
                            image_count += 1
                        else:
                            log.error(account_name + " 第%s张图片 %s 下载失败" % (image_count, image_url))

                # 判断当前页数是否大等于总页数
                if not is_over and page_count >= get_max_page_count(blog_page):
                    is_over = True
                else:
                    page_count += 1

            log.step(account_name + " 下载完毕，总共获得%s张图片" % (image_count - 1))

            # 排序
            if IS_SORT:
                if first_blog_id != "0":
                    destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
                    if robot.sort_file(image_path, destination_path, int(self.account_info[1]), 4):
                        log.step(account_name + " 图片从下载目录移动到保存目录成功")
                    else:
                        log.error(account_name + " 创建图片保存目录 %s 失败" % destination_path)
                        tool.process_exit()

            # 新的存档记录
            if first_blog_id != "0":
                self.account_info[1] = str(int(self.account_info[1]) + image_count - 1)
                self.account_info[2] = first_blog_id

            # 保存最后的信息
            self.thread_lock.acquire()
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
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
    Template().main()
