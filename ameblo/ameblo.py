# -*- coding:UTF-8  -*-
"""
ameblo图片爬虫
http://ameblo.jp/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, robot, tool
from PIL import Image
import os
import re
import threading
import time
import traceback

ACCOUNTS = []
TOTAL_IMAGE_COUNT = 0
GET_IMAGE_COUNT = 0
GET_PAGE_COUNT = 0
IMAGE_TEMP_PATH = ""
IMAGE_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_SORT = True


# 获取指定页数的日志页面
def get_blog_page(account_name, page_count):
    index_page_url = "http://ameblo.jp/%s/page-%s.html" % (account_name, page_count)
    index_page_response = tool.http_request2(index_page_url)
    if index_page_response.status == 200:
        return index_page_response.data
    return None


# 根绝日志页面，获取日志总页数
def is_max_page_count(page_data, page_count):
    # 有页数选择的页面样式
    if page_data.find('<div class="page topPaging">') >= 0:
        paging_data = tool.find_sub_string(page_data, '<div class="page topPaging">', "</div>")
        last_page = re.findall('/page-(\d*).html#main" class="lastPage"', paging_data)
        if len(last_page) == 1:
            return page_count >= int(last_page[0])
        page_count_find = re.findall('<a [^>]*?>(\d*)</a>', paging_data)
        if len(page_count_find) > 0:
            page_count_find = map(int, page_count_find)
            return page_count >= max(page_count_find)
        return False
    # 只有下一页和上一页按钮的样式
    elif page_data.find('<a class="skinSimpleBtn pagingPrev"') >= 0:  # 有上一页按钮
        if page_data.find('<a class="skinSimpleBtn pagingNext"') == -1:  # 但没有下一页按钮
            return True
        else:
            return False
    # 只有下一页和上一页按钮的样式
    elif page_data.find('class="skin-pagingPrev skin-btnPaging ga-pagingTopPrevTop') >= 0:  # 有上一页按钮
        if page_data.find('class="skin-pagingNext skin-btnPaging ga-pagingTopNextTop') == -1:  # 但没有下一页按钮
            return True
        else:
            return False
    return False


# 获取页面内容获取全部的日志id列表
def get_blog_id_list(page_data):
    return re.findall('data-unique-entry-id="([\d]*)"', page_data)


# 从日志列表中获取全部的图片，并过滤掉表情
def get_image_url_list(account_name, blog_id):
    blog_url = "http://ameblo.jp/%s/entry-%s.html" % (account_name, blog_id)
    blog_page_response = tool.http_request2(blog_url)
    if blog_page_response.status == 200:
        blog_page = blog_page_response.data
        article_data = tool.find_sub_string(blog_page, '<div class="subContentsInner">', "<!--entryBottom-->", 1)
        if not article_data:
            article_data = tool.find_sub_string(blog_page, '<div class="articleText">', "<!--entryBottom-->", 1)
        if not article_data:
            article_data = tool.find_sub_string(blog_page, '<div class="skin-entryInner">', "<!-- /skin-entry -->", 1)
        image_url_list_find = re.findall('<img [\S|\s]*?src="(http[^"]*)" [\S|\s]*?>', article_data)
        image_url_list = []
        for image_url in image_url_list_find:
            # 过滤表情
            if image_url.find(".ameba.jp/blog/ucs/") == -1:
                image_url_list.append(image_url)
        return image_url_list
    return None


# 过滤一些无效的地址
def filter_image_url(image_url):
    # 过滤表情
    if image_url.find("http://emoji.ameba.jp/") == 0 or image_url.find("http://blog.ameba.jp/ucs/img/char/") == 0 \
            or image_url.find("http://i.yimg.jp/images/mail/emoji/") == 0 or image_url.find("http://stat100.ameba.jp//blog/ucs/img/char/") == 0 \
            or image_url.find("https://b.st-hatena.com/images/entry-button/") == 0 or image_url.find("http://vc.ameba.jp/view?") == 0 \
            or image_url.find("https://mail.google.com/mail/") == 0 or image_url.find("http://jp.mg2.mail.yahoo.co.jp/ya/download/") == 0 \
            or image_url.find("http://blog.watanabepro.co.jp/") >= 0 or image_url[-9:] == "clear.gif":
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
                log.step("无法解析的图片地址 %s" % image_url)
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
        global GET_IMAGE_COUNT
        global GET_PAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
        }
        extra_config = {
            'save_data_path': os.path.join("info\\save2.data")
        }
        robot.Robot.__init__(self, sys_config, extra_config=extra_config, use_urllib3=True)

        # 设置全局变量，供子线程调用
        GET_IMAGE_COUNT = self.get_image_count
        GET_PAGE_COUNT = self.get_page_count
        IMAGE_TEMP_PATH = self.image_temp_path
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        IS_SORT = self.is_sort
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
            new_save_data_file = open(NEW_SAVE_DATA_PATH, "a")
            for account_name in ACCOUNTS:
                # account_name  image_count  last_blog_time
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

            image_count = 1
            page_count = 1
            first_blog_id = "0"
            unique_list = []
            is_over = False
            need_make_image_dir = True
            while not is_over:
                log.step(account_name + " 开始解析第%s页日志" % page_count)

                # 获取一页日志页面
                page_data = get_blog_page(account_name, page_count)
                if page_data is None:
                    log.error(account_name + " 第%s页日志无法获取" % page_count)
                    tool.process_exit()

                # 获取一页所有日志id列表
                blog_id_list = get_blog_id_list(page_data)
                log.trace(account_name + " 第%s页获取的所有日志：%s" % (page_count, blog_id_list))

                for blog_id in list(blog_id_list):
                    # 检查是否是上一次的最后blog
                    if int(blog_id) <= int(self.account_info[2]):
                        break

                    # 将第一个日志的时间做为新的存档记录
                    if first_blog_id == "0":
                        first_blog_id = str(blog_id)

                    # 新增日志导致的重复判断
                    if blog_id in unique_list:
                        continue
                    else:
                        unique_list.append(blog_id)

                    log.step(account_name + " 开始解析日志%s" % blog_id)

                    # 从日志页面中获取全部的图片地址列表
                    image_url_list = get_image_url_list(account_name, blog_id)
                    if image_url_list is None:
                        log.error(account_name + " 日志%s无法获取" % blog_id)
                        tool.process_exit()

                    for image_url in list(image_url_list):
                        if filter_image_url(image_url):
                            continue
                        # 获取原始图片下载地址
                        image_url = get_origin_image_url(image_url)
                        log.step(account_name + " 开始下载第%s张图片 %s" % (image_count, image_url))

                        # 第一张图片，创建目录
                        if need_make_image_dir:
                            if not tool.make_dir(image_path, 0):
                                log.error(account_name + " 创建图片下载目录 %s 失败" % image_path)
                                tool.process_exit()
                            need_make_image_dir = False

                        if image_url.rfind("/") > image_url.rfind("."):
                            file_type = "jpg"
                        else:
                            file_type = image_url.split(".")[-1].split("?")[0]
                        file_path = os.path.join(image_path, "%04d.%s" % (image_count, file_type))
                        save_file_return = tool.save_net_file2(image_url, file_path)
                        if save_file_return["status"] == 1:
                            if check_image_invalid(file_path):
                                os.remove(file_path)
                                log.step(account_name + " 第%s张图片 %s 不符合规则，删除" % (image_count, image_url))
                            else:
                                log.step(account_name + " 第%s张图片下载成功" % image_count)
                                image_count += 1
                        else:
                            log.error(account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_count, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

                    # 达到配置文件中的下载数量，结束
                    if 0 < GET_IMAGE_COUNT < image_count:
                        is_over = True
                        break

                if not is_over:
                    if 0 < GET_PAGE_COUNT < page_count:
                        is_over = True
                    else:
                        # 获取总页数
                        if is_max_page_count(page_data, page_count):
                            is_over = True
                        else:
                            page_count += 1

            log.step(account_name + " 下载完毕，总共获得%s张图片" % (image_count - 1))

            # 排序
            if IS_SORT and image_count > 1:
                destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
                log.step(account_name + " 图片开始从下载目录移动到保存目录")
                if robot.sort_file(image_path, destination_path, int(self.account_info[1]), 4):
                    log.step(account_name + " 图片从下载目录移动到保存目录成功")
                else:
                    log.error(account_name + " 创建图片子目录 %s 失败" % destination_path)
                    tool.process_exit()

            # 新的存档记录
            if first_blog_id != "0":
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
    Ameblo().main()
