# -*- coding:UTF-8  -*-
"""
篠田麻里子博客图片爬虫
http://blog.mariko-shinoda.net/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import os
import re


# 获取指定页数的所有日志
def get_one_page_blog(page_count):
    blog_pagination_url = "http://blog.mariko-shinoda.net/page%s.html" % (page_count - 1)
    result = {
        "is_over": False,  # 是不是最后一页日志
        "image_name_list": [],  # 所有图片名字
    }
    blog_pagination_response = net.http_request(blog_pagination_url)
    if blog_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 检测是否是最后一页
        result["is_over"] = blog_pagination_response.data == "記事が存在しません。"

        # 获取图片名字
        image_name_list = re.findall('data-original="./([^"]*)"', blog_pagination_response.data)
        result["image_name_list"] = map(str, image_name_list)
    else:
        raise robot.RobotException(robot.get_http_request_failed_reason(blog_pagination_response.status))
    return result


class Blog(robot.Robot):
    def __init__(self):
        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_NOT_CHECK_SAVE_DATA: True,
        }
        robot.Robot.__init__(self, sys_config)

    def main(self):
        # 解析存档文件
        last_blog_time = 0
        image_start_index = 0
        if os.path.exists(self.save_data_path):
            save_info = tool.read_file(self.save_data_path).split("\t")
            if len(save_info) >= 2:
                image_start_index = int(save_info[0])
                last_blog_time = int(save_info[1])

        # 下载
        page_count = 1
        image_count = 1
        is_over = False
        first_blog_time = None
        while not is_over:
            log.step("开始解析第%s页日志" % page_count)

            # 获取一页日志
            try:
                blog_pagination_response = get_one_page_blog(page_count)
            except robot.RobotException, e:
                log.error("第%s页日志访问失败，原因：%s" % (page_count, e.message))
                raise

            # 是否已经获取完毕
            if blog_pagination_response["is_over"]:
                break

            # 获取页面内的所有图片
            log.trace("第%s页解析的全部图片：%s" % (page_count, blog_pagination_response["image_name_list"]))

            if len(blog_pagination_response["image_name_list"]) > 0:
                # 获取日志时间
                blog_time = int(blog_pagination_response["image_name_list"][0].split("-")[0])

                # 检查是否达到存档记录
                if blog_time <= last_blog_time:
                    break

                # 新的存档记录
                if first_blog_time is None:
                    first_blog_time = str(blog_time)

            for image_name in blog_pagination_response["image_name_list"]:
                image_url = "http://blog.mariko-shinoda.net/%s" % image_name
                log.step("开始下载第%s张图片 %s" % (image_count, image_url))

                file_type = image_url.split(".")[-1].split(":")[0]
                file_path = os.path.join(self.image_temp_path, "%05d.%s" % (image_count, file_type))
                save_file_return = net.save_net_file(image_url, file_path)
                if save_file_return["status"] == 1:
                    log.step("第%s张图片下载成功" % image_count)
                    image_count += 1
                else:
                    log.step("第%s张图片 %s 下载失败，原因：%s" % (image_count, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
            page_count += 1

        log.step("下载完毕，总共获得%s张图片" % (image_count - 1))

        # 排序复制到保存目录
        if image_count > 1:
            log.step("图片开始从下载目录移动到保存目录")
            if robot.sort_file(self.image_temp_path, self.image_download_path, image_start_index, 5):
                log.step("图片从下载目录移动到保存目录成功")
            else:
                log.error("创建图片保存目录 %s 失败" % self.image_download_path)
                tool.process_exit()

        # 保存新的存档文件
        if first_blog_time is not None:
            tool.write_file(str(image_start_index) + "\t" + first_blog_time, self.save_data_path, 2)

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), image_count - 1))


if __name__ == "__main__":
    Blog().main()
