# -*- coding:UTF-8  -*-
"""
乃木坂46 OFFICIAL BLOG图片爬虫
http://blog.nogizaka46.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
from PIL import Image
import os
import re
import threading
import time
import traceback

ACCOUNTS = []
TOTAL_IMAGE_COUNT = 0
IMAGE_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""


# 获取成员指定页数的一页日志信息
# account_id -> asuka.saito
def get_one_page_blog(account_id, page_count):
    # http://blog.nogizaka46.com/asuka.saito
    blog_pagination_url = "http://blog.nogizaka46.com/%s/?p=%s" % (account_id, page_count)
    blog_pagination_response = net.http_request(blog_pagination_url)
    result = {
        "blog_info_list": [],  # 所有图片信息
        "is_over": False,  # 是不是最后一页日志
    }
    if blog_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 获取日志正文，并分组
        page_html = tool.find_sub_string(blog_pagination_response.data, '<div class="paginate">', '<div class="paginate">', 1)
        if not page_html:
            raise robot.RobotException("页面截取正文失败\n%s" % blog_pagination_response.data)
        blog_data_list = page_html.split('<h1 class="clearfix">')
        if len(blog_data_list) == 0:
            raise robot.RobotException("正文分割日志失败\n%s" % page_html)
        # 第一位不是日志内容，没有用
        blog_data_list.pop(0)
        for blog_data in blog_data_list:
            extra_image_info = {
                "blog_id": None,  # 日志id
                "image_url_list": [],  # 所有图片地址
                "big_2_small_image_lust": {},  # 所有含有大图的图片
            }
            # 获取日志id
            blog_id_html = tool.find_sub_string(blog_data, '<a href="http://blog.nogizaka46.com/%s/' % account_id, '.php"')
            if not blog_id_html:
                raise robot.RobotException("日志内容截取日志id失败\n%s" % blog_data)
            blog_id = blog_id_html.split("/")[-1]
            if not robot.is_integer(blog_id):
                raise robot.RobotException("日志内容截取日志id失败\n%s" % blog_data)
            extra_image_info["blog_id"] = str(int(blog_id))
            # 获取图片地址列表
            image_url_list = re.findall('src="([^"]*)"', blog_data)
            extra_image_info["image_url_list"] = map(str, image_url_list)
            # 获取所有的大图对应的小图
            big_image_list_find = re.findall('<a href="([^"]*)"><img[\S|\s]*? src="([^"]*)"', blog_data)
            big_2_small_image_lust = {}
            for big_image_url, small_image_url in big_image_list_find:
                big_2_small_image_lust[str(small_image_url)] = str(big_image_url)
            extra_image_info["big_2_small_image_lust"] = big_2_small_image_lust
            result["blog_info_list"].append(extra_image_info)
        # 判断是不是最后一页
        paginate_data = tool.find_sub_string(blog_pagination_response.data, '<div class="paginate">', "</div>")
        if not paginate_data:
            raise robot.RobotException("页面截取分页信息失败\n%s" % blog_pagination_response.data)
        page_count_find = re.findall('"\?p=(\d+)"', paginate_data)
        if len(page_count_find) == 0:
            raise robot.RobotException("分页信息匹配页码失败\n%s" % paginate_data)
        result["is_over"] = page_count >= max(map(int, page_count_find))
    elif blog_pagination_response.status == 404:
        raise robot.RobotException("账号不存在")
    else:
        raise robot.RobotException(robot.get_http_request_failed_reason(blog_pagination_response.status))
    return result


# 检查图片是否存在对应的大图，以及判断大图是否仍然有效，如果存在可下载的大图则返回大图地址，否则返回原图片地址
def check_big_image(image_url, big_2_small_list):
    result = {
        "image_url": None,  # 大图地址
        "is_over": False,  # 是不是已经没有还生效的大图了
        "cookies": None,  # 页面返回的cookies
    }
    if image_url in big_2_small_list:
        if big_2_small_list[image_url].find("http://dcimg.awalker.jp") == 0:
            big_image_response = net.http_request(big_2_small_list[image_url])
            if big_image_response.status == net.HTTP_RETURN_CODE_SUCCEED:
                # 检测是不是已经过期删除
                temp_image_url = tool.find_sub_string(big_image_response.data, '<img src="', '"')
                if temp_image_url != "/img/expired.gif":
                    result["image_url"] = temp_image_url
                else:
                    result["is_over"] = True
                # 获取cookies
                result["cookies"] = net.get_cookies_from_response_header(big_image_response.headers)
        else:
            result["image_url"] = big_2_small_list[image_url]
    return result


# 检测图片是否有效
def check_image_invalid(file_path):
    file_path = tool.change_path_encoding(file_path)
    file_size = os.path.getsize(file_path)
    # 文件小于1K
    if file_size < 1024:
        try:
            image = Image.open(file_path)
        except IOError:  # 不是图片格式
            return True
        # 长或宽任意小于20像素的
        if image.height <= 20 or image.width <= 20:
            return True
    return False


class Blog(robot.Robot):
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
        total_image_count = 0
        temp_path_list = []

        try:
            log.step(account_name + " 开始")

            page_count = 1
            blog_info_list = []
            is_over = False
            # 获取全部还未下载过需要解析的日志
            while not is_over:
                log.step(account_name + " 开始解析第%s页日志" % page_count)

                # 获取一页图片
                try:
                    blog_pagination_response = get_one_page_blog(account_id, page_count)
                except robot.RobotException, e:
                    log.error(account_name + " 第%s页日志解析失败，原因：%s" % (page_count, e.message))
                    raise

                log.trace(account_name + " 第%s页解析的所有日志信息：%s" % (page_count, blog_pagination_response["blog_info_list"]))

                # 寻找这一页符合条件的日志
                for blog_info in blog_pagination_response["blog_info_list"]:
                    # 检查是否达到存档记录
                    if int(blog_info["blog_id"]) > int(self.account_info[2]):
                        blog_info_list.append(blog_info)
                    else:
                        is_over = True
                        break

                if not is_over:
                    if blog_pagination_response["is_over"]:
                        is_over = True
                    else:
                        page_count += 1

            log.step("需要下载的全部日志解析完毕，共%s个" % len(blog_info_list))

            # 从最早的日志开始下载
            while len(blog_info_list) > 0:
                blog_info = blog_info_list.pop()
                log.step(account_name + " 开始解析日志%s" % blog_info["blog_id"])

                image_index = int(self.account_info[1]) + 1
                for image_url in blog_info["image_url_list"]:
                    # 检查是否存在大图可以下载
                    big_image_response = check_big_image(image_url, blog_info["big_2_small_image_lust"])
                    if big_image_response["image_url"] is not None:
                        image_url = big_image_response["image_url"]
                    log.step(account_name + " 开始下载第%s张图片 %s" % (image_index, image_url))

                    file_type = image_url.split(".")[-1]
                    if file_type.find("?") != -1:
                        file_type = "jpeg"
                    file_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name, "%04d.%s" % (image_index, file_type))
                    save_file_return = net.save_net_file(image_url, file_path, cookies_list=big_image_response["cookies"])
                    if save_file_return["status"] == 1:
                        if check_image_invalid(file_path):
                            tool.remove_dir_or_file(file_path)
                            log.step(account_name + " 第%s张图片 %s 不符合规则，删除" % (image_index, image_url))
                        else:
                            temp_path_list.append(file_path)
                            log.step(account_name + " 第%s张图片下载成功" % image_index)
                            image_index += 1
                    else:
                        log.error(account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_index, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
                # 日志内图片全部下载完毕
                temp_path_list = []  # 临时目录设置清除
                total_image_count += (image_index - 1) - int(self.account_info[1])  # 计数累加
                self.account_info[1] = str(image_index - 1)  # 设置存档记录
                self.account_info[2] = blog_info["blog_id"]  # 设置存档记录
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
        ACCOUNTS.remove(account_id)
        self.thread_lock.release()
        log.step(account_name + " 下载完毕，总共获得%s张图片" % total_image_count)


if __name__ == "__main__":
    Blog().main()
