# -*- coding:UTF-8  -*-
"""
7gogo图片&视频爬虫
https://7gogo.jp/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import os
import threading
import time
import traceback

INIT_TARGET_ID = "99999"
MESSAGE_COUNT_PER_PAGE = 30


# 获取指定页数的全部日志信息
def get_one_page_blog(account_name, target_id):
    blog_pagination_url = "https://api.7gogo.jp/web/v2/talks/%s/images" % account_name
    query_data = {
        "targetId": target_id,
        "limit": MESSAGE_COUNT_PER_PAGE,
        "direction": "PREV",
    }
    blog_pagination_response = net.http_request(blog_pagination_url, method="GET", fields=query_data, json_decode=True)
    result = {
        "blog_info_list": [],  # 全部日志信息
    }
    if blog_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if not robot.check_sub_key(("data",), blog_pagination_response.json_data):
            raise robot.RobotException("返回信息'data'字段不存在\n%s" % blog_pagination_response.json_data)
        if not isinstance(blog_pagination_response.json_data["data"], list):
            raise robot.RobotException("返回信息'data'字段类型不正确\n%s" % blog_pagination_response.json_data)
        for blog_info in blog_pagination_response.json_data["data"]:
            result_blog_info = {
                "blog_id": None,  # 日志id
                "image_url_list": [],  # 全部图片地址
                "video_url_list": [],  # 全部视频地址
            }
            if not robot.check_sub_key(("post",), blog_info):
                raise robot.RobotException("日志信息'post'字段不存在\n%s" % blog_info)
            # 获取日志id
            if not robot.check_sub_key(("postId",), blog_info["post"]):
                raise robot.RobotException("日志信息'postId'字段不存在\n%s" % blog_info)
            if not robot.is_integer(blog_info["post"]["postId"]):
                raise robot.RobotException("日志信息'postId'类型不正确n%s" % blog_info)
            result_blog_info["blog_id"] = str(blog_info["post"]["postId"])
            # 获取日志内容
            if not robot.check_sub_key(("body",), blog_info["post"]):
                raise robot.RobotException("日志信息'body'字段不存在\n%s" % blog_info)
            for blog_body in blog_info["post"]["body"]:
                if not robot.check_sub_key(("bodyType",), blog_body):
                    raise robot.RobotException("日志信息'bodyType'字段不存在\n%s" % blog_body)
                if not robot.is_integer(blog_body["bodyType"]):
                    raise robot.RobotException("日志信息'bodyType'字段类型不正确\n%s" % blog_body)
                # bodyType = 1: text, bodyType = 3: image, bodyType = 8: video
                body_type = int(blog_body["bodyType"])
                if body_type == 1:  # 文本
                    continue
                elif body_type == 2:  # 表情
                    continue
                elif body_type == 3:  # 图片
                    if not robot.check_sub_key(("image",), blog_body):
                        raise robot.RobotException("日志信息'image'字段不存在\n%s" % blog_body)
                    result_blog_info["image_url_list"].append(str(blog_body["image"]))
                elif body_type == 7:  # 转发
                    continue
                elif body_type == 8:  # video
                    if not robot.check_sub_key(("movieUrlHq",), blog_body):
                        raise robot.RobotException("日志信息'movieUrlHq'字段不存在\n%s" % blog_body)
                    result_blog_info["video_url_list"].append(str(blog_body["movieUrlHq"]))
                else:
                    raise robot.RobotException("日志信息'bodyType'字段取值不正确\n%s" % blog_body)
            result["blog_info_list"].append(result_blog_info)
    elif target_id == INIT_TARGET_ID and blog_pagination_response.status == 400:
        raise robot.RobotException("talk不存在")
    else:
        raise robot.RobotException(robot.get_http_request_failed_reason(blog_pagination_response.status))
    return result


class NanaGoGo(robot.Robot):
    def __init__(self):
        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_DOWNLOAD_VIDEO: True,
        }
        robot.Robot.__init__(self, sys_config)

        # 解析存档文件
        # account_name  image_count  video_count  last_post_id
        self.account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0", "0"])

    def main(self):
        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for account_name in sorted(self.account_list.keys()):
            # 检查正在运行的线程数
            if threading.activeCount() >= self.thread_count + main_thread_count:
                self.wait_sub_thread()

            # 提前结束
            if not self.is_running():
                break

            # 开始下载
            thread = Download(self.account_list[account_name], self)
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

        log.step("全部下载完毕，耗时%s秒，共计图片%s张，视频%s个" % (self.get_run_time(), self.total_image_count, self.total_video_count))


class Download(robot.DownloadThread):
    def __init__(self, account_info, main_thread):
        robot.DownloadThread.__init__(self, account_info, main_thread)
        self.account_name = self.account_info[0]
        log.step(self.account_name + " 开始")

    # 获取所有可下载日志
    def get_crawl_list(self):
        target_id = INIT_TARGET_ID
        blog_info_list = []
        is_over = False
        # 获取全部还未下载过需要解析的日志
        while not is_over:
            self.main_thread_check()  # 检测主线程运行状态
            log.step(self.account_name + " 开始解析target id %s后的一页日志" % target_id)

            # 获取一页日志信息
            try:
                blog_pagination_response = get_one_page_blog(self.account_name, target_id)
            except robot.RobotException, e:
                log.error(self.account_name + " target id %s的一页日志信息解析失败，原因：%s" % (target_id, e.message))
                raise

            # 如果为空，表示已经取完了
            if len(blog_pagination_response["blog_info_list"]) == 0:
              break

            log.trace(self.account_name + " target id %s解析的全部日志：%s" % (target_id, blog_pagination_response["blog_info_list"]))

            # 寻找这一页符合条件的日志
            for blog_info in blog_pagination_response["blog_info_list"]:
                # 检查是否达到存档记录
                if int(blog_info["blog_id"]) > int(self.account_info[3]):
                    blog_info_list.append(blog_info)
                    # 设置下一页指针
                    target_id = blog_info["blog_id"]
                else:
                    is_over = True
                    break

        return blog_info_list

    # 解析单个日志
    def crawl_blog(self, blog_info):
        # 图片下载
        image_index = int(self.account_info[1]) + 1
        if self.main_thread.is_download_image:
            for image_url in blog_info["image_url_list"]:
                self.main_thread_check()  # 检测主线程运行状态
                log.step(self.account_name + " 开始下载第%s张图片 %s" % (image_index, image_url))

                file_type = image_url.split(".")[-1]
                image_file_path = os.path.join(self.main_thread.image_download_path, self.account_name, "%04d.%s" % (image_index, file_type))
                save_file_return = net.save_net_file(image_url, image_file_path)
                if save_file_return["status"] == 1:
                    self.temp_path_list.append(image_file_path)
                    log.step(self.account_name + " 第%s张图片下载成功" % image_index)
                    image_index += 1
                else:
                    log.error(self.account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_index, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

        # 视频下载
        video_index = int(self.account_info[2]) + 1
        if self.main_thread.is_download_video:
            for video_url in blog_info["video_url_list"]:
                self.main_thread_check()  # 检测主线程运行状态
                log.step(self.account_name + " 开始下载第%s个视频 %s" % (video_index, video_url))

                file_type = video_url.split(".")[-1]
                video_file_path = os.path.join(self.main_thread.video_download_path, self.account_name, "%04d.%s" % (video_index, file_type))
                save_file_return = net.save_net_file(video_url, video_file_path)
                if save_file_return["status"] == 1:
                    self.temp_path_list.append(video_file_path)
                    log.step(self.account_name + " 第%s个视频下载成功" % video_index)
                    video_index += 1
                else:
                    log.error(self.account_name + " 第%s个视频 %s 下载失败，原因：%s" % (video_index, video_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

        # 日志内图片和视频全部下载完毕
        self.temp_path_list = []  # 临时目录设置清除
        self.total_image_count += (image_index - 1) - int(self.account_info[1])  # 计数累加
        self.total_video_count += (video_index - 1) - int(self.account_info[2])  # 计数累加
        self.account_info[1] = str(image_index - 1)  # 设置存档记录
        self.account_info[2] = str(video_index - 1)  # 设置存档记录
        self.account_info[3] = str(blog_info["blog_id"])

    def run(self):
        try:
            # 获取所有可下载日志
            blog_info_list = self.get_crawl_list()
            log.step(self.account_name + " 需要下载的全部日志解析完毕，共%s个" % len(blog_info_list))

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
            self.main_thread.total_video_count += self.total_video_count
            self.main_thread.account_list.pop(self.account_name)
        log.step(self.account_name + " 下载完毕，总共获得%s张图片，%s个视频" % (self.total_image_count, self.total_video_count))
        self.notify_main_thread()


if __name__ == "__main__":
    NanaGoGo().main()
