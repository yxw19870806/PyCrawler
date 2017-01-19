# -*- coding:UTF-8  -*-
"""
篠田麻里子博客图片爬虫
http://blog.mariko-shinoda.net/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, net, robot, tool
import os
import re


# 获取指定页数的所有日志
def get_one_page_blog(page_count):
    index_page_url = "http://blog.mariko-shinoda.net/page%s.html" % (page_count - 1)
    return net.http_request(index_page_url)


# 判断日志是否已经全部获取完毕
def is_blog_over(page_data):
    return page_data == "記事が存在しません。"


# 获取页面中的所有图片地址列表
def get_image_name_list(page_data):
    return re.findall('data-original="./([^"]*)"', page_data)


class Shinoda(robot.Robot):
    def __init__(self):
        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_NOT_CHECK_SAVE_DATA: True,
        }
        robot.Robot.__init__(self, sys_config, use_urllib3=True)

    def main(self):
        # 解析存档文件
        last_blog_time = 0
        image_start_index = 0
        if os.path.exists(self.save_data_path):
            save_file = open(self.save_data_path, "r")
            save_info = save_file.read()
            save_file.close()
            save_info = save_info.split("\t")
            if len(save_info) >= 2:
                image_start_index = int(save_info[0])
                last_blog_time = int(save_info[1])

        # 下载
        page_count = 1
        image_count = 1
        new_last_blog_time = ""
        is_over = False
        need_make_download_dir = True
        if self.is_sort:
            image_path = self.image_temp_path
        else:
            image_path = self.image_download_path
        while not is_over:
            log.step("开始解析第%s页日志" % page_count)

            # 获取一页日志
            index_page_response = get_one_page_blog(page_count)
            if index_page_response.status != 200:
                log.error("第%s页日志访问失败，原因：%s" % (page_count, robot.get_http_request_failed_reason(index_page_response.status)))
                tool.process_exit()

            # 是否已经获取完毕
            if is_blog_over(index_page_response.data):
                break

            # 获取页面内的全部图片
            image_name_list = get_image_name_list(index_page_response.data)
            log.trace("第%s页获取的全部图片：%s" % (page_count, image_name_list))

            if len(image_name_list) >= 1:
                # 获取blog时间
                blog_time = int(image_name_list[0].split("-")[0])

                # 检查是否已下载到前一次的图片
                if blog_time <= last_blog_time:
                    is_over = True

                # 将第一个博客的id做为新的存档记录
                if new_last_blog_time == "":
                    new_last_blog_time = str(blog_time)

            for image_name in image_name_list:
                image_url = "http://blog.mariko-shinoda.net/%s" % image_name
                log.step("开始下载第%s张图片 %s" % (image_count, image_url))

                if need_make_download_dir:
                    if not tool.make_dir(image_path, 0):
                        log.error("创建图片下载目录 %s 失败" % image_path)
                        tool.process_exit()
                    need_make_download_dir = False

                file_type = image_url.split(".")[-1].split(":")[0]
                file_path = os.path.join(image_path, "%05d.%s" % (image_count, file_type))
                save_file_return = net.save_net_file(image_url, file_path)
                if save_file_return["status"] == 1:
                    log.step("第%s张图片下载成功" % image_count)
                    image_count += 1
                else:
                    log.step("第%s张图片 %s 下载失败，原因：%s" % (image_count, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
            page_count += 1

        log.step("下载完毕，总共获得%s张图片" % (image_count - 1))

        # 排序复制到保存目录
        if self.is_sort:
            log.step("图片开始从下载目录移动到保存目录")
            if robot.sort_file(self.image_temp_path, self.image_download_path, image_start_index, 5):
                log.step(" 图片从下载目录移动到保存目录成功")
            else:
                log.error(" 创建图片保存目录 %s 失败" % self.image_download_path)
                tool.process_exit()

        # 保存新的存档文件
        new_save_file_path = robot.get_new_save_file_path(self.save_data_path)
        log.step("保存新存档文件 %s" % new_save_file_path)
        new_save_file = open(new_save_file_path, "w")
        new_save_file.write(str(image_start_index) + "\t" + new_last_blog_time)
        new_save_file.close()

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), image_count - 1))


if __name__ == "__main__":
    Shinoda().main()
