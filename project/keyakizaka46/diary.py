# -*- coding:UTF-8  -*-
"""
欅坂46公式Blog图片爬虫
http://www.keyakizaka46.com/mob/news/diarShw.php?cd=member
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
IMAGE_COUNT_PER_PAGE = 20
TOTAL_IMAGE_COUNT = 0
IMAGE_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""


# 获取指定页数的全部日志
def get_one_page_blog(account_id, page_count):
    # http://www.keyakizaka46.com/mob/news/diarKiji.php?cd=member&ct=01&page=0&rw=20
    blog_pagination_url = "http://www.keyakizaka46.com/mob/news/diarKiji.php?cd=member&ct=%02d&page=%s&rw=%s" % (int(account_id), page_count - 1, IMAGE_COUNT_PER_PAGE)
    blog_pagination_response = net.http_request(blog_pagination_url)
    result = {
        "blog_info_list": [],  # 全部日志信息
    }
    if blog_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(blog_pagination_response.status))
    if len(tool.find_sub_string(blog_pagination_response.data, '<div class="box-profile">', "</div>").strip()) < 10:
        raise robot.RobotException("账号不存在")
    # 日志正文部分
    blog_article_html = tool.find_sub_string(blog_pagination_response.data, '<div class="box-main">', '<div class="box-sideMember">')
    if not blog_article_html:
        raise robot.RobotException("页面正文截取失败\n%s" % blog_pagination_response.data)
    blog_list = re.findall("<article>([\s|\S]*?)</article>", blog_article_html)
    for blog_info in blog_list:
        extra_blog_info = {
            "blog_id" : None,  # 日志id
            "image_url_list": [],  # 全部图片地址
        }
        # 获取日志id
        blog_id = tool.find_sub_string(blog_info, "/diary/detail/", "?")
        if not robot.is_integer(blog_id):
            raise robot.RobotException("日志页面截取日志id失败\n%s" % blog_info)
        extra_blog_info["blog_id"] = str(blog_id)
        # 获取全部图片地址
        image_url_list = re.findall('<img[\S|\s]*?src="([^"]+)"', blog_info)
        extra_blog_info["image_url_list"] = map(str, image_url_list)
        result["blog_info_list"].append(extra_blog_info)
    return result


# 检测图片地址是否包含域名，如果没有则补上
def get_image_url(image_url):
    # 如果图片地址没有域名，表示直接使用当前域名下的资源，需要拼接成完整的地址
    if image_url[:7] != "http://" and image_url[:8] != "https://":
        if image_url[0] == "/":
            image_url = "http://www.keyakizaka46.com%s" % image_url
        else:
            image_url = "http://www.keyakizaka46.com/%s" % image_url
    return image_url


class Diary(robot.Robot):
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
        # account_id  image_count  last_diary_time
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
                # account_id  image_count  last_blog_id
                new_save_data_file.write("\t".join(account_list[account_id]) + "\n")
            new_save_data_file.close()

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

                # 获取一页博客信息
                try:
                    blog_pagination_response = get_one_page_blog(account_id, page_count)
                except robot.RobotException, e:
                    log.error(account_name + " 第%s页日志解析失败，原因：%s" % (page_count, e.message))
                    raise

                # 没有获取到任何日志，全部日志已经全部获取完毕了
                if len(blog_pagination_response["blog_info_list"]) == 0:
                    break

                log.trace(account_name + " 第%s页解析的全部日志：%s" % (page_count, blog_pagination_response["blog_info_list"]))

                # 寻找这一页符合条件的日志
                for blog_info in blog_pagination_response["blog_info_list"]:
                    # 检查是否达到存档记录
                    if int(blog_info["blog_id"]) > int(self.account_info[2]):
                        blog_info_list.append(blog_info)
                    else:
                        is_over = True
                        break

                if not is_over:
                    page_count += 1

            log.step("需要下载的全部日志解析完毕，共%s个" % len(blog_info_list))

            # 从最早的日志开始下载
            while len(blog_info_list) > 0:
                blog_info =  blog_info_list.pop()
                log.step(account_name + " 开始解析日志%s" % blog_info["blog_id"])
                log.trace(account_name + " 日志%s解析的全部图片：%s" % (blog_info["blog_id"], blog_info["image_url_list"]))

                image_index = int(self.account_info[1]) + 1
                for image_url in blog_info["image_url_list"]:
                    # 检测图片地址是否包含域名
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
    Diary().main()
