# -*- coding:UTF-8  -*-
"""
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import os
import re
import time
import threading

TOTAL_IMAGE_COUNT = 0


# 获取指定页数的所有图片
def get_one_page_photo(page_count):
    photo_pagination_url = "http://www.abase.me/movies.php?page=%s" % page_count
    photo_pagination_response = net.http_request(photo_pagination_url)
    result = {
        "page_video_count": 0,  # 页面解析出的影片数量
        "image_info_list": [],  # 页面解析出的图片信息列表
    }
    if photo_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(photo_pagination_response.status))
    # 获取页面中的影片数量
    result["page_video_count"] = photo_pagination_response.data.count('<div class="item pull-left">')
    # 获取页面中的所有图片信息列表
    # 单张图片信息的格式：[image_url, title]
    image_info_list = re.findall('<img src="" data-original="([^"]*)" class="lazy [^"]*" title="([^"]*)">', photo_pagination_response.data)
    result["image_info_list"] = [map(str, key) for key in image_info_list]
    return result


# 获取图片原图的下载地址
# 1.http://pics.dmm.co.jp//digital/video/daqu00001/daqu00001ps.jpg
# ->
# http://pics.dmm.co.jp//digital/video/daqu00001/daqu00001pl.jpg
# 2.http://images.abase.me/00/86/MK/MKBD-S86_1.jpg
# ->
# http://images.abase.me/00/86/MK/MKBD-S86_2.jpg
def get_large_image_url(image_url):
    if image_url.find("http://images.abase.me") >= 0:
        if image_url.find("_1.") >= 0:
            return image_url.replace("_1.", "_2.")
    elif image_url.find("http://pics.dmm.co.jp") >= 0:
        if image_url.find("ps.") >= 0 and image_url.count("ps.") == 1:
            return image_url.replace("ps.", "pl.")
    return None


# 检测图片是否是无效的（已被删除的无效图片）
def check_invalid_image(file_path):
    if os.path.getsize(file_path) == 2732:
        if tool.get_file_md5(file_path) in ["f591f3826a1085af5cdeeca250b2c97a", "ec9c76280bf2d31aa39c203808446f06"]:
            return True
    return False


class ABase(robot.Robot):
    def __init__(self):
        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_NOT_CHECK_SAVE_DATA: True,
        }
        robot.Robot.__init__(self, sys_config)

        self.thread_count = 50

    def main(self):
        page_count = 1
        main_thread_count = threading.activeCount()
        # 多线程下载类型
        # 1 同时开始N个下载线程
        # 2 对一页中的所有图片开启多线程下载，下完一页中的所有图片后开始下一页
        thread_type = 2
        while True:
            log.step("开始解析第%s页图片" % page_count)

            # 获取一页图片
            try:
                photo_pagination_response = get_one_page_photo(page_count)
            except robot.RobotException, e:
                log.error("第%s页解析失败，原因：%s" % (page_count, e.message))
                raise 

            # 已经下载完毕了
            if photo_pagination_response["page_video_count"] == 0:
                break

            log.trace("第%s页解析到影片%s个，封面图片%s张" % (page_count, len(photo_pagination_response["image_info_list"]), photo_pagination_response["page_video_count"]))

            for small_image_url, title in photo_pagination_response["image_info_list"]:
                # 达到线程上限，等待
                while thread_type == 1 and threading.activeCount() >= self.thread_count + main_thread_count:
                    time.sleep(5)

                title = robot.filter_text(title).upper()
                image_url = get_large_image_url(small_image_url)
                if image_url is None:
                    log.error("%s的封面图片 %s 大图地址解析失败" % (small_image_url, title))
                    continue

                log.step("开始下载%s的封面图片 %s" % (title, image_url))

                file_type = image_url.split(".")[-1]
                file_path = os.path.join(self.image_download_path, "%s.%s" % (title, file_type))
                file_temp_path = os.path.join(self.image_download_path, "%s_temp.%s" % (title, file_type))

                # 开始下载
                thread = Download(self.thread_lock, title, file_path, file_temp_path, image_url)
                thread.start()
                time.sleep(0.1)

            # 还有未完成线程
            while thread_type == 2 and threading.activeCount() > main_thread_count:
                time.sleep(5)

            page_count += 1

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), TOTAL_IMAGE_COUNT))


class Download(threading.Thread):
    def __init__(self, thread_lock, title, file_path, file_temp_path, file_url):
        threading.Thread.__init__(self)
        self.thread_lock = thread_lock
        self.title = title
        self.file_path = file_path
        self.file_temp_path = file_temp_path
        self.file_url = file_url

    def run(self):
        global TOTAL_IMAGE_COUNT

        # 如果文件已经存在，则使用临时文件名保存
        if os.path.exists(self.file_path):
            is_exist = True
            file_path = self.file_temp_path
        else:
            is_exist = False
            file_path = self.file_path

        save_file_return = net.save_net_file(self.file_url, file_path)
        if save_file_return["status"] == 1:
            if check_invalid_image(file_path):
                os.remove(file_path)
                log.step("%s的封面图片无效，自动删除" % self.title)
            else:
                log.step("%s的封面图片下载成功" % self.title)
                if is_exist:
                    # 如果新下载图片比原来大，则替换原本的；否则删除新下载的图片
                    if os.path.getsize(self.file_temp_path) > os.path.getsize(self.file_path):
                        os.remove(self.file_path)
                        os.rename(self.file_temp_path, self.file_path)
                    else:
                        os.remove(self.file_temp_path)

                self.thread_lock.acquire()
                TOTAL_IMAGE_COUNT += 1
                self.thread_lock.release()
        else:
            log.error("%s的封面图片 %s 下载失败，原因：%s" % (self.title, self.file_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))


if __name__ == "__main__":
    ABase().main()
