# -*- coding:UTF-8  -*-
"""
乃木坂46 OFFICIAL BLOG图片爬虫
http://blog.nogizaka46.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, net, robot, tool
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


# 获取成员指定页数的一页日志信息
# account_id -> asuka.saito
def get_one_page_blog(account_id, page_count):
    # http://blog.nogizaka46.com/asuka.saito
    index_page_url = "http://blog.nogizaka46.com/%s/?p=%s" % (account_id, page_count)
    index_page_response = net.http_request(index_page_url)
    extra_info = {
        "blog_info_list": [],  # 页面解析出的所有图片信息列表
        "is_over": False,  # 是不是最后一页日志
    }
    if index_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 获取日志中文，并分组
        page_html = tool.find_sub_string(index_page_response.data, '<div class="paginate">', '<div class="paginate">', 1)
        blog_data_list = page_html.split('<h1 class="clearfix">')
        if len(blog_data_list) > 0:
            # 第一位不是日志内容，没有用
            blog_data_list.pop(0)
        for blog_data in blog_data_list:
            extra_image_info = {
                "blog_id": None,  # 页面解析出的日志id
                "image_url_list": [],  # 页面解析出的所有图片地址列表
                "big_2_small_image_lust": {},  # 页面解析出的所有含有大图的图片列表
            }
            # 获取日志id
            blog_id = tool.find_sub_string(blog_data, '<a href="http://blog.nogizaka46.com/%s/' % account_id, '.php"')
            blog_id = blog_id.split("/")[-1]
            if blog_id and robot.is_integer(blog_id):
                # 获取日志id
                extra_image_info["blog_id"] = int(blog_id)
            # 获取图片地址列表
            image_url_list = re.findall('src="([^"]*)"', blog_data)
            extra_image_info["image_url_list"] = map(str, image_url_list)
            # 获取所有的大图对应的小图
            big_image_list_find = re.findall('<a href="([^"]*)"><img[\S|\s]*? src="([^"]*)"', blog_data)
            big_2_small_image_lust = {}
            for big_image_url, small_image_url in big_image_list_find:
                big_2_small_image_lust[str(small_image_url)] = str(big_image_url)
            extra_image_info["big_2_small_image_lust"] = big_2_small_image_lust

            extra_info["blog_info_list"].append(extra_image_info)
        # 检测是否还有下一页
        paginate_data = tool.find_sub_string(index_page_response.data, '<div class="paginate">', "</div>")
        page_count_find = re.findall('"\?p=(\d+)"', paginate_data)
        extra_info["is_over"] = page_count >= max(map(int, page_count_find))
    index_page_response.extra_info = extra_info
    return index_page_response


# 检查图片是否存在对应的大图，以及判断大图是否仍然有效，如果存在可下载的大图则返回大图地址，否则返回原图片地址
def check_big_image(image_url, big_2_small_list):
    big_image_response = net.ErrorResponse(net.HTTP_RETURN_CODE_EXCEPTION_CATCH)
    extra_info = {
        "image_url": None,  # 页面解析出的大图地址
        "is_over": False,  # 是不是已经没有还生效的大图了
    }
    if image_url in big_2_small_list:
        if big_2_small_list[image_url].find("http://dcimg.awalker.jp") == 0:
            big_image_response = net.http_request(big_2_small_list[image_url])
            if big_image_response.status == net.HTTP_RETURN_CODE_SUCCEED:
                # 检测是不是已经过期删除
                temp_image_url = tool.find_sub_string(big_image_response.data, '<img src="', '"')
                if temp_image_url != "/img/expired.gif":
                    extra_info["image_url"] = temp_image_url
                else:
                    extra_info["is_over"] = True
        else:
            extra_info["image_url"] = big_2_small_list[image_url]
    big_image_response.extra_info = extra_info
    return big_image_response


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
        global GET_IMAGE_COUNT
        global GET_PAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
        }
        robot.Robot.__init__(self, sys_config)

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
            is_big_image_over = False
            while not is_over:
                log.step(account_name + " 开始解析第%s页日志" % page_count)

                # 获取一页图片
                index_page_response = get_one_page_blog(account_id, page_count)
                if index_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                    log.error(account_name + " 第%s页日志访问失败，原因：%s" % (page_count, robot.get_http_request_failed_reason(index_page_response.status)))
                    tool.process_exit()

                if len(index_page_response.extra_info["blog_info_list"]) == 0:
                    log.error(account_name + " 第%s页日志%s分组失败" % (page_count, index_page_response.data))
                    tool.process_exit()

                for blog_info in index_page_response.extra_info["blog_info_list"]:
                    # 获取日志id
                    if blog_info["blog_id"] is None:
                        log.error(account_name + " 日志id解析失败")
                        tool.process_exit()

                    # 检查是否已下载到前一次的日志
                    if blog_info["blog_id"] <= int(self.account_info[2]):
                        is_over = True
                        break

                    # 将第一个日志的ID做为新的存档记录
                    if first_blog_id == "0":
                        first_blog_id = str(blog_info["blog_id"])

                    log.step(account_name + " 开始解析日志%s" % blog_info["blog_id"])

                    if len(blog_info["image_url_list"]) == 0:
                        continue

                    # 下载图片
                    for image_url in blog_info["image_url_list"]:
                        header_list = None
                        # 检查是否存在大图可以下载
                        if not is_big_image_over:
                            big_image_response = check_big_image(image_url, blog_info["big_2_small_image_lust"])
                            if big_image_response.extra_info["image_url"] is not None:
                                image_url = big_image_response.extra_info["image_url"]
                                if "Set-Cookie" in big_image_response.headers:
                                    header_list = {"Cookie": big_image_response.headers["Set-Cookie"]}
                            is_big_image_over = big_image_response.extra_info["is_over"]
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
                        save_file_return = net.save_net_file(image_url, file_path, header_list=header_list)
                        if save_file_return["status"] == 1:
                            if check_image_invalid(file_path):
                                os.remove(tool.change_path_encoding(file_path))
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
                    # 达到配置文件中的下载页数，结束
                    if 0 < GET_PAGE_COUNT <= page_count:
                        is_over = True
                    elif index_page_response.extra_info["is_over"]:
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
    Blog().main()
