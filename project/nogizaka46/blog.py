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


# 获取成员指定页数的一页日志信息
# account_id -> asuka.saito
def get_one_page_blog(account_id, page_count):
    # http://blog.nogizaka46.com/asuka.saito
    blog_pagination_url = "http://blog.nogizaka46.com/%s/" % account_id
    query_data = {"p": page_count}
    blog_pagination_response = net.http_request(blog_pagination_url, method="GET", fields=query_data)
    result = {
        "blog_info_list": [],  # 全部图片信息
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
            result_image_info = {
                "big_2_small_image_lust": {},  # 全部含有大图的图片
                "blog_id": None,  # 日志id
                "image_url_list": [],  # 全部图片地址
            }
            # 获取日志id
            blog_id_html = tool.find_sub_string(blog_data, '<a href="http://blog.nogizaka46.com/%s/' % account_id, '.php"')
            if not blog_id_html:
                raise robot.RobotException("日志内容截取日志id失败\n%s" % blog_data)
            blog_id = blog_id_html.split("/")[-1]
            if not robot.is_integer(blog_id):
                raise robot.RobotException("日志内容截取日志id失败\n%s" % blog_data)
            result_image_info["blog_id"] = str(int(blog_id))
            # 获取图片地址列表
            image_url_list = re.findall('src="(http[^"]*)"', blog_data)
            result_image_info["image_url_list"] = map(str, image_url_list)
            # 获取全部大图对应的小图
            big_image_list_find = re.findall('<a href="([^"]*)"><img[\S|\s]*? src="([^"]*)"', blog_data)
            big_2_small_image_lust = {}
            for big_image_url, small_image_url in big_image_list_find:
                big_2_small_image_lust[str(small_image_url)] = str(big_image_url)
            result_image_info["big_2_small_image_lust"] = big_2_small_image_lust
            result["blog_info_list"].append(result_image_info)
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
        "cookies": None,  # 页面返回的cookies
        "image_url": None,  # 大图地址
        "is_over": False,  # 是不是已经没有还生效的大图了
    }
    if image_url in big_2_small_list:
        if big_2_small_list[image_url].find("http://dcimg.awalker.jp") == 0:
            big_image_response = net.http_request(big_2_small_list[image_url], method="GET")
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
    file_path = path.change_path_encoding(file_path)
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
        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
        }
        robot.Robot.__init__(self, sys_config)

    def main(self):
        # 解析存档文件
        # account_id  image_count  last_blog_time
        self.account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0"])

        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for account_id in sorted(self.account_list.keys()):
            # 检查正在运行的线程数
            if threading.activeCount() >= self.thread_count + main_thread_count:
                self.wait_sub_thread()

            # 提前结束
            if not self.is_running():
                break

            # 开始下载
            thread = Download(self.account_list[account_id], self)
            thread.start()

            time.sleep(1)

        # 检查除主线程外的其他所有线程是不是全部结束了
        while threading.activeCount() > main_thread_count:
            self.wait_sub_thread()

        # 未完成的数据保存
        if len(self.account_list) > 0:
            tool.write_file(tool.list_to_string(self.account_list.values()), self.temp_save_data_path)

        # 重新排序保存存档文件
        robot.rewrite_save_file(self.temp_save_data_path, self.save_data_path)

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), self.total_image_count))


class Download(robot.DownloadThread):
    def __init__(self, account_info, main_thread):
        robot.DownloadThread.__init__(self, account_info, main_thread)
        self.account_id = self.account_info[0]
        if len(self.account_info) >= 4 and self.account_info[3]:
            self.account_name = self.account_info[3]
        else:
            self.account_name = self.account_info[0]
        log.step(self.account_name + " 开始")
        
    # 获取所有可下载日志
    def get_crawl_list(self):
        page_count = 1
        blog_info_list = []
        is_over = False
        # 获取全部还未下载过需要解析的日志
        while not is_over:
            self.main_thread_check()  # 检测主线程运行状态
            log.step(self.account_name + " 开始解析第%s页日志" % page_count)

            # 获取一页图片
            try:
                blog_pagination_response = get_one_page_blog(self.account_id, page_count)
            except robot.RobotException, e:
                log.error(self.account_name + " 第%s页日志解析失败，原因：%s" % (page_count, e.message))
                raise

            log.trace(self.account_name + " 第%s页解析的全部日志：%s" % (page_count, blog_pagination_response["blog_info_list"]))

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

        return blog_info_list

    # 解析单个日志
    def crawl_blog(self, blog_info):
        image_index = int(self.account_info[1]) + 1
        for image_url in blog_info["image_url_list"]:
            self.main_thread_check()  # 检测主线程运行状态
            # 检查是否存在大图可以下载
            big_image_response = check_big_image(image_url, blog_info["big_2_small_image_lust"])
            if big_image_response["image_url"] is not None:
                image_url = big_image_response["image_url"]
            log.step(self.account_name + " 开始下载第%s张图片 %s" % (image_index, image_url))

            file_type = image_url.split(".")[-1]
            if file_type.find("?") != -1:
                file_type = "jpeg"
            file_path = os.path.join(self.main_thread.image_download_path, self.account_name, "%04d.%s" % (image_index, file_type))
            save_file_return = net.save_net_file(image_url, file_path, cookies_list=big_image_response["cookies"])
            if save_file_return["status"] == 1:
                if check_image_invalid(file_path):
                    path.delete_dir_or_file(file_path)
                    log.step(self.account_name + " 第%s张图片 %s 不符合规则，删除" % (image_index, image_url))
                else:
                    self.temp_path_list.append(file_path)
                    log.step(self.account_name + " 第%s张图片下载成功" % image_index)
                    image_index += 1
            else:
                log.error(self.account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_index, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

        # 日志内图片全部下载完毕
        self.temp_path_list = []  # 临时目录设置清除
        self.total_image_count += (image_index - 1) - int(self.account_info[1])  # 计数累加
        self.account_info[1] = str(image_index - 1)  # 设置存档记录
        self.account_info[2] = blog_info["blog_id"]  # 设置存档记录

    def run(self):
        try:
            # 获取所有可下载日志
            blog_info_list = self.get_crawl_list()
            log.step("需要下载的全部日志解析完毕，共%s个" % len(blog_info_list))

            # 从最早的日志开始下载
            while len(blog_info_list) > 0:
                blog_info = blog_info_list.pop()
                log.step(self.account_name + " 开始解析日志%s" % blog_info["blog_id"])
                self.crawl_blog(blog_info)
                self.main_thread_check()  # 检测主线程运行状态
        except SystemExit, se:
            if se.code == 0:
                log.step(self.account_name + " 提前退出")
            else:
                log.error(self.account_name + " 异常退出")
            # 如果临时目录变量不为空，表示某个日志正在下载中，需要把下载了部分的内容给清理掉
            self.clean_temp_path()
        except Exception, e:
            log.error(self.account_name + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 保存最后的信息
        with self.thread_lock:
            tool.write_file("\t".join(self.account_info), self.main_thread.temp_save_data_path)
            self.main_thread.total_image_count += self.total_image_count
            self.main_thread.account_list.pop(self.account_id)
        log.step(self.account_name + " 下载完毕，总共获得%s张图片" % self.total_image_count)
        self.notify_main_thread()


if __name__ == "__main__":
    Blog().main()
