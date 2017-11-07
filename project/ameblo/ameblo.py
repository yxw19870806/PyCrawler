# -*- coding:UTF-8  -*-
"""
ameblo图片爬虫
http://ameblo.jp/
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


# 获取指定页数的全部日志
def get_one_page_blog(account_name, page_count):
    blog_pagination_url = "https://ameblo.jp/%s/page-%s.html" % (account_name, page_count)
    blog_pagination_response = net.http_request(blog_pagination_url, method="GET")
    result = {
        "blog_id_list": [],  # 全部日志id
        "is_over": False,  # 是不是最后一页日志
    }
    if blog_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 获取日志id
        blog_id_list = re.findall('data-unique-entry-id="([\d]*)"', blog_pagination_response.data)
        # 另一种页面格式
        if len(blog_id_list) == 0:
            page_data = tool.find_sub_string(blog_pagination_response.data, 'class="skin-tiles"', 'class="skin-entryAd"')
            if not page_data:
                raise robot.RobotException("页面截取正文失败\n%s" % blog_pagination_response.data)
            blog_id_list = re.findall('<a data-uranus-component="imageFrameLink" href="https://ameblo.jp/' + account_name + '/entry-(\d*).html"', page_data)
        if len(blog_id_list) == 0:
            raise robot.RobotException("页面匹配日志id失败\n%s" % blog_pagination_response.data)
        result["blog_id_list"] = map(str, blog_id_list)
        # 判断是不是最后一页
        # 有页数选择的页面样式
        if blog_pagination_response.data.find('<div class="page topPaging">') >= 0:
            paging_data = tool.find_sub_string(blog_pagination_response.data, '<div class="page topPaging">', "</div>")
            last_page = re.findall('/page-(\d*).html#main" class="lastPage"', paging_data)
            if len(last_page) == 1:
                result["is_over"] = page_count >= int(last_page[0])
            page_count_find = re.findall("<a [^>]*?>(\d*)</a>", paging_data)
            if len(page_count_find) > 0:
                result["is_over"] = page_count >= max(map(int, page_count_find))
        # 只有下一页和上一页按钮的样式
        elif blog_pagination_response.data.find('<a class="skinSimpleBtn pagingPrev"') >= 0:  # 有上一页按钮
            if blog_pagination_response.data.find('<a class="skinSimpleBtn pagingNext"') == -1:  # 但没有下一页按钮
                result["is_over"] = True
        # 另一种只有下一页和上一页按钮的样式
        elif blog_pagination_response.data.find('class="skin-pagingPrev skin-btnPaging ga-pagingTopPrevTop') >= 0:  # 有上一页按钮
            if blog_pagination_response.data.find('class="skin-pagingNext skin-btnPaging ga-pagingTopNextTop') == -1:  # 但没有下一页按钮
                result["is_over"] = True
    elif page_count == 1 and blog_pagination_response.status == 404:
        raise robot.RobotException("账号不存在")
    else:
        raise robot.RobotException(robot.get_http_request_failed_reason(blog_pagination_response.status))
    return result


# 获取指定id的日志
def get_blog_page(account_name, blog_id):
    blog_url = "https://ameblo.jp/%s/entry-%s.html" % (account_name, blog_id)
    blog_response = net.http_request(blog_url, method="GET")
    result = {
        "image_url_list": [],  # 全部图片地址
    }
    if blog_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(blog_response.status))
    # 截取日志正文部分（有多种页面模板）
    article_data = tool.find_sub_string(blog_response.data, '<div class="subContentsInner">', "<!--entryBottom-->", 1)
    if not article_data:
        article_data = tool.find_sub_string(blog_response.data, '<div class="articleText">', "<!--entryBottom-->", 1)
    if not article_data:
        article_data = tool.find_sub_string(blog_response.data, '<div class="skin-entryInner">', "<!-- /skin-entry -->", 1)
    if not article_data:
        raise robot.RobotException("页面截取正文失败\n%s" % blog_response.data)
    # 获取图片地址
    image_url_list = re.findall('<img [\S|\s]*?src="(http[^"]*)" [\S|\s]*?>', article_data)
    result["image_url_list"] = map(str, image_url_list)
    return result


# 过滤一些无效的地址
def filter_image_url(image_url):
    # 过滤表情
    if image_url.find("//emoji.ameba.jp/") >= 0 or image_url.find("//blog.ameba.jp/ucs/img/char/") >= 0 \
            or image_url.find("//stat.ameba.jp/blog/ucs/img/") >= 0 or image_url.find("//stat100.ameba.jp//blog/ucs/img/char/") >= 0 \
            or image_url.find("//stat100.ameba.jp/blog/ucs/img/char/") >= 0 or image_url.find("//i.yimg.jp/images/mail/emoji/") >= 0 \
            or image_url.find("//b.st-hatena.com/images/entry-button/") >= 0 or image_url.find("//vc.ameba.jp/view?") >= 0 \
            or image_url.find("//mail.google.com/mail/") >= 0 or image_url.find("//www.youtube.com/") >= 0 \
            or image_url.find("//jp.mg2.mail.yahoo.co.jp/ya/download/") >= 0 or image_url.find("//blog.watanabepro.co.jp/") >= 0 \
            or image_url.find("//iine.blog.ameba.jp/web/display_iine.html") >= 0 \
            or image_url[-9:] == "clear.gif":
        return True
    return False


# 获取原始图片下载地址
# http://stat.ameba.jp/user_images/20110612/15/akihabara48/af/3e/j/t02200165_0800060011286009555.jpg
# ->
# http://stat.ameba.jp/user_images/20110612/15/akihabara48/af/3e/j/o0800060011286009555.jpg
# http://stat.ameba.jp/user_images/4b/90/10112135346_s.jpg
# ->
# http://stat.ameba.jp/user_images/4b/90/10112135346.jpg
def get_origin_image_url(image_url):
    if image_url.find("http://stat.ameba.jp/user_images") == 0:
        # 最新的image_url使用?caw=指定显示分辨率，去除
        # http://stat.ameba.jp/user_images/20161220/12/akihabara48/fd/1a/j/o0768032013825427476.jpg?caw=800
        image_url = image_url.split("?")[0]
        temp_list = image_url.split("/")
        image_name = temp_list[-1]
        if image_name[0] != "o":
            # http://stat.ameba.jp/user_images/20110612/15/akihabara48/af/3e/j/t02200165_0800060011286009555.jpg
            if image_name[0] == "t" and image_name.find("_") > 0:
                temp_list[-1] = "o" + image_name.split("_", 1)[1]
                image_url = "/".join(temp_list)
            # http://stat.ameba.jp/user_images/4b/90/10112135346_s.jpg
            elif image_name.split(".")[0][-2:] == "_s":
                temp_list[-1] = image_name.replace("_s", "")
                image_url = "/".join(temp_list)
            else:
                # todo 检测包含其他格式
                log.error("无法解析的图片地址 %s" % image_url)
    elif image_url.find("http://stat100.ameba.jp/blog/img/") == 0:
        pass
    else:
        log.trace("第三方图片地址 %s" % image_url)
    return image_url


# 检测图片是否有效
def check_image_invalid(file_path):
    file_size = os.path.getsize(file_path)
    # 文件小于1K
    if file_size < 1024:
        return True
    try:
        image = Image.open(file_path)
    except IOError:  # 不是图片格式
        return True
    # 长或宽任意小于20像素的
    if image.height <= 20 or image.width <= 20:
        return True
    # 文件小于 5K 并且 长或宽任意小于50像素的
    if file_size < 5120 and (image.height <= 50 or image.width <= 50):
        return True
    return False


class Ameblo(robot.Robot):
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
        # account_name  image_count  last_diary_time
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0"])
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
            with open(NEW_SAVE_DATA_PATH, "a") as new_save_data_file:
                for account_name in ACCOUNTS:
                    # account_name  image_count  last_blog_time
                    new_save_data_file.write("\t".join(account_list[account_name]) + "\n")

        # 重新排序保存存档文件
        robot.rewrite_save_file(NEW_SAVE_DATA_PATH, self.save_data_path)

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), TOTAL_IMAGE_COUNT))


class Download(robot.DownloadThread):
    def __init__(self, account_info, thread_lock):
        robot.DownloadThread.__init__(self, account_info, thread_lock)

    def run(self):
        global TOTAL_IMAGE_COUNT

        account_name = self.account_info[0]
        total_image_count = 0
        temp_path_list = []

        try:
            log.step(account_name + " 开始")

            page_count = 1
            blog_id_list = []
            is_over = False
            # 获取全部还未下载过需要解析的日志
            while not is_over:
                log.step(account_name + " 开始解析第%s页日志" % page_count)

                # 获取一页日志
                try:
                    blog_pagination_response = get_one_page_blog(account_name, page_count)
                except robot.RobotException, e:
                    log.error(account_name + " 第%s页日志解析失败，原因：%s" % (page_count, e.message))
                    raise

                log.trace(account_name + " 第%s页解析的全部日志：%s" % (page_count, blog_pagination_response["blog_id_list"]))

                for blog_id in blog_pagination_response["blog_id_list"]:
                    # 检查是否达到存档记录
                    if int(blog_id) > int(self.account_info[2]):
                        # 新增日志导致的重复判断
                        if blog_id in blog_id_list:
                            continue
                        else:
                            blog_id_list.append(blog_id)
                    else:
                        is_over = True
                        break

                if not is_over:
                    if blog_pagination_response["is_over"]:
                        is_over = True
                    else:
                        page_count += 1

            log.step(account_name + " 需要下载的全部日志解析完毕，共%s个" % len(blog_id_list))

            # 从最早的日志开始下载
            while len(blog_id_list) > 0:
                blog_id = blog_id_list.pop()
                log.step(account_name + " 开始解析日志%s" % blog_id)

                # 获取日志
                try:
                    blog_response = get_blog_page(account_name, blog_id)
                except robot.RobotException, e:
                    log.error(account_name + " 日志%s解析失败，原因：%s" % (blog_id, e.message))
                    raise

                log.trace(account_name + " 日志%s解析的全部图片：%s" % (blog_id, blog_response["image_url_list"]))

                image_index = int(self.account_info[1]) + 1
                for image_url in blog_response["image_url_list"]:
                    # 过滤一些无效的地址
                    if filter_image_url(image_url):
                        continue
                    # 获取原始图片下载地址
                    image_url = get_origin_image_url(image_url)
                    log.step(account_name + " 开始下载第%s张图片 %s" % (image_index, image_url))

                    if image_url.rfind("/") > image_url.rfind("."):
                        file_type = "jpg"
                    else:
                        file_type = image_url.split(".")[-1].split("?")[0]
                    file_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name, "%04d.%s" % (image_index, file_type))
                    save_file_return = net.save_net_file(image_url, file_path)
                    if save_file_return["status"] == 1:
                        if check_image_invalid(file_path):
                            path.delete_dir_or_file(file_path)
                            log.step(account_name + " 第%s张图片 %s 不符合规则，删除" % (image_index, image_url))
                        else:
                            # 设置临时目录
                            temp_path_list.append(file_path)
                            log.step(account_name + " 第%s张图片下载成功" % image_index)
                            image_index += 1
                    else:
                        log.error(account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_index, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
                # 日志内图片全部下载完毕
                temp_path_list = []  # 临时目录设置清除
                total_image_count += (image_index - 1) - int(self.account_info[1])  # 计数累加
                self.account_info[1] = str(image_index - 1)  # 设置存档记录
                self.account_info[2] = blog_id  # 设置存档记录
        except SystemExit, se:
            if se.code == 0:
                log.step(account_name + " 提前退出")
            else:
                log.error(account_name + " 异常退出")
            # 如果临时目录变量不为空，表示某个日志正在下载中，需要把下载了部分的内容给清理掉
            if len(temp_path_list) > 0:
                for temp_path in temp_path_list:
                    path.delete_dir_or_file(temp_path)
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
    Ameblo().main()
