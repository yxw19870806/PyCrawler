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
import traceback


# 获取指定页数的全部日志
def get_one_page_blog(page_count):
    blog_pagination_url = "http://blog.mariko-shinoda.net/page%s.html" % (page_count - 1)
    result = {
        "blog_info_list": [],  # 全部日志信息
        "is_over": False,  # 是不是最后一页日志
    }
    blog_pagination_response = net.http_request(blog_pagination_url)
    if blog_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(blog_pagination_response.status))
    # 检测是否是最后一页
    result["is_over"] = blog_pagination_response.data == "記事が存在しません。"
    if result["is_over"]:
        return result
    # 获取图片名字
    blog_html_find = re.findall("<section>([\s|\S]*?)</section>", blog_pagination_response.data)
    if len(blog_html_find) == 0:
        raise robot.RobotException("页面匹配日志信息失败\n%s" % blog_pagination_response.data)
    for blog_html in blog_html_find:
        result_blog_info = {
            "blog_id": None,  # 日志id
            "image_url_list": [],  # 图片地址列表
        }
        image_name_list = re.findall('data-original="./([^"]*)"', blog_html)
        if len(image_name_list) == 0:
            continue
        blog_id = str(image_name_list[0]).split("-")[0]
        if not robot.is_integer(blog_id):
            raise robot.RobotException("图片名字截取日志id失败\n%s" % blog_html)
        result_blog_info["blog_id"] = blog_id
        for image_name in image_name_list:
            result_blog_info["image_url_list"].append("http://blog.mariko-shinoda.net/%s" % image_name)
        result["blog_info_list"].append(result_blog_info)
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
        # image_count  last_blog_id
        save_info = ["0", "0"]
        if os.path.exists(self.save_data_path):
            file_save_info = tool.read_file(self.save_data_path).split("\t")
            if len(file_save_info) >= 2 and robot.is_integer(file_save_info[0]) and robot.is_integer(file_save_info[1]):
                save_info = file_save_info
            else:
                log.error("存档内数据格式不正确")
                tool.process_exit()
        total_image_count = 0
        temp_path_list = []

        try:
            page_count = 1
            blog_info_list = []
            is_over = False
            # 获取全部还未下载过需要解析的日志
            while not is_over:
                log.step("开始解析第%s页日志" % page_count)

                # 获取一页日志
                try:
                    blog_pagination_response = get_one_page_blog(page_count)
                except robot.RobotException, e:
                    log.error("第%s页日志解析失败，原因：%s" % (page_count, e.message))
                    raise

                # 是否已经获取完毕
                if blog_pagination_response["is_over"]:
                    break

                # 获取页面内的全部图片
                log.trace("第%s页解析的全部日志：%s" % (page_count, blog_pagination_response["blog_info_list"]))

                # 寻找这一页符合条件的日志
                for blog_info in blog_pagination_response["blog_info_list"]:
                    # 检查是否达到存档记录
                    if int(blog_info["blog_id"]) > int(save_info[1]):
                        blog_info_list.append(blog_info)
                    else:
                        is_over = True
                        break

                if not is_over:
                    page_count += 1

            log.step("需要下载的全部日志解析完毕，共%s个" % len(blog_info_list))

            # 从最早的日志开始下载
            while len(blog_info_list) > 0:
                blog_info = blog_info_list.pop()
                log.step("开始解析日志 %s" % blog_info["blog_id"])

                image_index = int(save_info[0]) + 1
                for image_url in blog_info["image_url_list"]:
                    log.step("开始下载第%s张图片 %s" % (image_index, image_url))

                    file_type = image_url.split(".")[-1].split(":")[0]
                    file_path = os.path.join(self.image_download_path, "%05d.%s" % (image_index, file_type))
                    save_file_return = net.save_net_file(image_url, file_path)
                    if save_file_return["status"] == 1:
                        temp_path_list.append(file_path)
                        log.step("第%s张图片下载成功" % image_index)
                        image_index += 1
                    else:
                        log.step("第%s张图片 %s 下载失败，原因：%s" % (image_index, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
                # 日志内图片全部下载完毕
                temp_path_list = []  # 临时目录设置清除
                total_image_count += (image_index - 1) - int(save_info[0])  # 计数累加
                save_info[0] = str(image_index - 1)  # 设置存档记录
                save_info[1] = blog_info["blog_id"]  # 设置存档记录
        except SystemExit, se:
            if se.code == 0:
                log.step("提前退出")
            else:
                log.error("异常退出")
            # 如果临时目录变量不为空，表示某个图集正在下载中，需要把下载了部分的内容给清理掉
            if len(temp_path_list) > 0:
                for temp_path in temp_path_list:
                    path.delete_dir_or_file(temp_path)
        except Exception, e:
            log.error("未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 保存新的存档文件
        tool.write_file("\t".join(save_info), self.save_data_path, 2)
        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), total_image_count))


if __name__ == "__main__":
    Blog().main()
