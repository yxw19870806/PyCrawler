# -*- coding:UTF-8  -*-
"""
新浪博客图片爬虫
http://http://blog.sina.com.cn/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
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


# 获取指定页数的全部日志
def get_one_page_blog(account_id, page_count):
    # http://moexia.lofter.com/?page=1
    blog_pagination_url = "http://blog.sina.com.cn/s/articlelist_%s_0_%s.html" % (account_id, page_count)
    blog_pagination_response = net.http_request(blog_pagination_url)
    result = {
        "blog_info_list": [],  # 全部日志地址
        "is_over": False,  # 是不是最后一页
    }
    if blog_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if page_count == 1 and blog_pagination_response.data.find("抱歉，您要访问的页面不存在或被删除！") >= 0:
            raise robot.RobotException("账号不存在")
        article_list_selector = pq(blog_pagination_response.data.decode("UTF-8")).find(".articleList .articleCell")
        if article_list_selector.size() == 0:
            raise robot.RobotException("页面截取日志列表失败\n%s" % blog_pagination_response.data)
        for article_index in range(article_list_selector.size()):
            result_blog_info = {
                "blog_url": None,  # 日志地址
                "blog_time": None,  # 日志时间
                "blog_title": "",  # 日志标题
            }
            article_selector = article_list_selector.eq(article_index)
            # 获取日志地址
            blog_url = article_selector.find("span.atc_title a").attr("href")
            if not blog_url:
                raise robot.RobotException("日志列表解析日志地址失败\n%s" % article_selector.html().encode("UTF-8"))
            result_blog_info["blog_url"] = str(blog_url)
            # 获取日志标题
            blog_title = article_selector.find("span.atc_title a").text().encode("UTF-8")
            if not blog_title:
                raise robot.RobotException("日志列表解析日志标题失败\n%s" % article_selector.html().encode("UTF-8"))
            result_blog_info["blog_title"] = str(blog_title)
            # 获取日志时间
            blog_time = article_selector.find("span.atc_tm").text()
            if not blog_time:
                raise robot.RobotException("日志列表解析日志时间失败\n%s" % article_selector.html().encode("UTF-8"))
            try:
                result_blog_info["blog_time"] = int(time.mktime(time.strptime(blog_time, "%Y-%m-%d %H:%M")))
            except ValueError:
                raise robot.RobotException("日志时间格式不正确\n%s" % blog_time)
            result["blog_info_list"].append(result_blog_info)
        # 获取分页信息
        pagination_html = tool.find_sub_string(blog_pagination_response.data, '<div class="SG_page">', '</div>')
        if not pagination_html:
            result["is_over"] = True
        else:
            max_page_count = tool.find_sub_string(pagination_html, "共", "页")
            if not robot.is_integer(max_page_count):
                raise robot.RobotException("分页信息截取总页数失败\n%s" % pagination_html)
            result["is_over"] = page_count >= int(max_page_count)
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
    # 获取博客正文
    article_html = tool.find_sub_string(blog_response.data, "<!-- 正文开始 -->", "<!-- 正文结束 -->")
    # 获取图片地址
    image_url_list = re.findall('real_src ="([^"]*)"', article_html)
    result["image_url_list"] = map(str, image_url_list)
    # 获取全部图片地址
    return result


# 获取日志id
def get_blog_id(blog_url):
    return tool.find_sub_string(blog_url.split("/")[-1], "blog_", ".html")


# 获取图片原始地址
def get_image_url(image_url):
    if image_url.find("&amp") >= 0:
        temp_list = image_url.split("&amp")[0].split("/")
        temp_list[-2] = "orignal"
        image_url = "/".join(temp_list)
    return image_url


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
        # account_name  last_blog_id
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "0"])
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
        if len(self.account_info) > 2 and self.account_info[2]:
            account_name = self.account_info[2]
        else:
            account_name = account_id
        total_image_count = 0
        temp_path = ""

        try:
            log.step(account_name + " 开始")

            page_count = 1
            unique_list = []
            blog_info_list = []
            is_over = False
            # 获取全部还未下载过需要解析的日志
            while not is_over:
                log.step(account_name + " 开始解析第%s页日志" % page_count)

                try:
                    blog_pagination_response = get_one_page_blog(account_id, page_count)
                except robot.RobotException, e:
                    log.error(account_name + " 第%s页日志解析失败，原因：%s" % (page_count, e.message))
                    raise

                log.trace(account_name + " 第%s页解析的全部日志：%s" % (page_count, blog_pagination_response["blog_info_list"]))

                # 寻找这一页符合条件的日志
                for blog_info in blog_pagination_response["blog_info_list"]:
                    # 新增日志导致的重复判断
                    if blog_info["blog_url"] in unique_list:
                        continue
                    else:
                        unique_list.append(blog_info["blog_url"])

                    # 检查是否达到存档记录
                    if blog_info["blog_time"] > int(self.account_info[1]):
                        blog_info_list.append(blog_info)
                    else:
                        is_over = True
                        break

                if not is_over:
                    if blog_pagination_response["is_over"]:
                        is_over = blog_pagination_response["is_over"]
                    else:
                        page_count += 1

            log.step("需要下载的全部日志解析完毕，共%s个" % len(blog_info_list))

            # 从最早的日志开始下载
            while len(blog_info_list) > 0:
                blog_info = blog_info_list.pop()
                log.step(account_name + " 开始解析日志 %s" % blog_info["blog_url"])

                # 获取日志
                try:
                    blog_response = get_blog_page(blog_info["blog_url"])
                except robot.RobotException, e:
                    log.error(account_name + " 日志 %s 解析失败，原因：%s" % (blog_info["blog_url"], e.message))
                    raise

                log.trace(account_name + " 日志 %s 解析的全部图片：%s" % (blog_info["blog_url"], blog_response["image_url_list"]))

                image_index = 1
                # 过滤标题中不支持的字符
                blog_title = robot.filter_text(blog_info["blog_title"])
                blog_id = get_blog_id(blog_info["blog_url"])
                # 过滤标题中不支持的字符
                if blog_title:
                    image_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name, "%s %s" % (blog_id, blog_title))
                else:
                    image_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name, blog_id)
                temp_path = image_path
                for image_url in blog_response["image_url_list"]:
                    # 获取图片原始地址
                    image_url = get_image_url(image_url)
                    log.step(account_name + " 开始下载第%s张图片 %s" % (image_index, image_url))

                    if image_url.rfind(".") > image_url.rfind("/"):
                        file_type = image_url.split(".")[-1]
                    else:
                        file_type = "jpg"
                    file_path = os.path.join(image_path, "%04d.%s" % (image_index, file_type))
                    save_file_return = net.save_net_file(image_url, file_path)
                    if save_file_return["status"] == 1:
                        log.step(account_name + " 第%s张图片下载成功" % image_index)
                        image_index += 1
                    else:
                        log.error(account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_index, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
                # 日志内图片全部下载完毕
                temp_path = ""  # 临时目录设置清除
                total_image_count += image_index - 1  # 计数累加
                self.account_info[1] = str(blog_info["blog_time"])  # 设置存档记录
        except SystemExit, se:
            if se.code == 0:
                log.step(account_name + " 提前退出")
            else:
                log.error(account_name + " 异常退出")
            # 如果临时目录变量不为空，表示某个日志正在下载中，需要把下载了部分的内容给清理掉
            if temp_path:
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
