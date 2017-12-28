# -*- coding:UTF-8  -*-
"""
微博图片爬虫
http://www.weibo.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import weiboCommon
import os
import threading
import time
import traceback

IMAGE_COUNT_PER_PAGE = 20  # 每次请求获取的图片数量
COOKIE_INFO = {"SUB": ""}


# 获取一页的图片信息
def get_one_page_photo(account_id, page_count):
    photo_pagination_url = "http://photo.weibo.com/photos/get_all"
    query_data = {
        "uid": account_id,
        "count": IMAGE_COUNT_PER_PAGE,
        "page": page_count,
        "type": "3",
    }
    cookies_list = {"SUB": COOKIE_INFO["SUB"]}
    result = {
        "image_info_list": [],  # 全部图片信息
        "is_over": False,  # 是不是最后一页图片
    }
    photo_pagination_response = net.http_request(photo_pagination_url, method="GET", fields=query_data, cookies_list=cookies_list, json_decode=True)
    if photo_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if not robot.check_sub_key(("data",), photo_pagination_response.json_data):
            raise robot.RobotException("返回数据'data'字段不存在\n%s" % photo_pagination_response.json_data)
        if not robot.check_sub_key(("total", "photo_list"), photo_pagination_response.json_data["data"]):
            raise robot.RobotException("返回数据'data'字段格式不正确\n%s" % photo_pagination_response.json_data)
        if not robot.is_integer(photo_pagination_response.json_data["data"]["total"]):
            raise robot.RobotException("返回数据'total'字段类型不正确\n%s" % photo_pagination_response.json_data)
        if not isinstance(photo_pagination_response.json_data["data"]["photo_list"], list):
            raise robot.RobotException("返回数据'photo_list'字段类型不正确\n%s" % photo_pagination_response.json_data)
        for image_info in photo_pagination_response.json_data["data"]["photo_list"]:
            result_image_info = {
                "image_time": None,  # 图片上传时间
                "image_url": None,  # 图片地址
            }
            # 获取图片上传时间
            if not robot.check_sub_key(("timestamp",), image_info):
                raise robot.RobotException("图片信息'timestamp'字段不存在\n%s" % image_info)
            if not robot.check_sub_key(("timestamp",), image_info):
                raise robot.RobotException("图片信息'timestamp'字段类型不正确\n%s" % image_info)
            result_image_info["image_time"] = int(image_info["timestamp"])
            # 获取图片地址
            if not robot.check_sub_key(("pic_host", "pic_name"), image_info):
                raise robot.RobotException("图片信息'pic_host'或者'pic_name'字段不存在\n%s" % image_info)
            result_image_info["image_url"] = str(image_info["pic_host"]) + "/large/" + str(image_info["pic_name"])
            result["image_info_list"].append(result_image_info)
        # 检测是不是还有下一页 总的图片数量 / 每页显示的图片数量 = 总的页数
        result["is_over"] = page_count >= (photo_pagination_response.json_data["data"]["total"] * 1.0 / IMAGE_COUNT_PER_PAGE)
    elif photo_pagination_response.status == net.HTTP_RETURN_CODE_JSON_DECODE_ERROR and photo_pagination_response.data.find('<p class="txt M_txtb">用户不存在或者获取用户信息失败</p>') >= 0:
        raise robot.RobotException("账号不存在")
    else:
        raise robot.RobotException(robot.get_http_request_failed_reason(photo_pagination_response.status))
    return result


class Weibo(robot.Robot):
    def __init__(self, extra_config=None):
        global COOKIE_INFO

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_GET_COOKIE: {
                ".sina.com.cn": (),
                ".login.sina.com.cn": (),
            },
        }
        robot.Robot.__init__(self, sys_config, extra_config)

        # 设置全局变量，供子线程调用
        COOKIE_INFO.update(self.cookie_value)

    def main(self):
        global COOKIE_INFO

        # 检测登录状态
        if not weiboCommon.check_login(COOKIE_INFO):
            # 如果没有获得登录相关的cookie，则模拟登录并更新cookie
            new_cookies_list = weiboCommon.generate_login_cookie(COOKIE_INFO)
            if new_cookies_list:
                COOKIE_INFO.update(new_cookies_list)
            # 再次检测登录状态
            if not weiboCommon.check_login(COOKIE_INFO):
                log.error("没有检测到登录信息")
                tool.process_exit()

        # 解析存档文件
        # account_id  image_count  last_image_time  (account_name)
        self.account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0"])

        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for account_id in sorted(self.account_list.keys()):
            # 检查正在运行的线程数
            if threading.activeCount() >= self.thread_count + main_thread_count:
                self.wait_sub_thread()

            # 提前结束
            if not self.is_running():
                break

            # 开始下载
            thread = Download(self.account_list[account_id], self)
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

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), self.total_image_count))


class Download(robot.DownloadThread):
    def __init__(self, account_info, main_thread):
        robot.DownloadThread.__init__(self, account_info, main_thread)
        self.account_id = self.account_info[0]
        if len(self.account_info) >= 4 and self.account_info[3]:
            self.account_name = self.account_info[3]
        else:
            self.account_name = self.account_info[0]
        log.step(self.account_name + " 开始")

    # 获取所有可下载图片
    def get_crawl_list(self):
        page_count = 1
        unique_list = []
        image_info_list = []
        is_over = False
        # 获取全部还未下载过需要解析的图片
        while not is_over:
            self.main_thread_check()  # 检测主线程运行状态
            log.step(self.account_name + " 开始解析第%s页图片" % page_count)

            # 获取指定一页图片的信息
            try:
                photo_pagination_response = get_one_page_photo(self.account_id, page_count)
            except robot.RobotException, e:
                log.error(self.account_name + " 第%s页图片解析失败，原因：%s" % (page_count, e.message))
                raise

            log.trace(self.account_name + "第%s页解析的全部图片信息：%s" % (page_count, photo_pagination_response["image_info_list"]))

            # 寻找这一页符合条件的图片
            for image_info in photo_pagination_response["image_info_list"]:
                # 新增图片导致的重复判断
                if image_info["image_url"] in unique_list:
                    continue
                else:
                    unique_list.append(image_info["image_url"])

                # 检查是否达到存档记录
                if image_info["image_time"] > int(self.account_info[2]):
                    image_info_list.append(image_info)
                else:
                    is_over = True
                    break

            if not is_over:
                if photo_pagination_response["is_over"]:
                    is_over = True
                else:
                    page_count += 1

        return image_info_list

    # 下载同一上传时间的所有图片
    def crawl_image(self, image_info_list):
        # 同一上传时间的所有图片
        image_index = int(self.account_info[1]) + 1
        for image_info in image_info_list:
            self.main_thread_check()  # 检测主线程运行状态
            log.step(self.account_name + " 开始下载第%s张图片 %s" % (image_index, image_info["image_url"]))

            file_type = image_info["image_url"].split(".")[-1]
            if file_type.find("/") != -1:
                file_type = "jpg"
            image_file_path = os.path.join(self.main_thread.image_download_path, self.account_name, "%04d.%s" % (image_index, file_type))
            save_file_return = net.save_net_file(image_info["image_url"], image_file_path)
            if save_file_return["status"] == 1:
                if weiboCommon.check_image_invalid(image_file_path):
                    path.delete_dir_or_file(image_file_path)
                    log.error(self.account_name + " 第%s张图片 %s 资源已被删除，跳过" % (image_index, image_info["image_url"]))
                    continue
                else:
                    # 设置临时目录
                    self.temp_path_list.append(image_file_path)
                    log.step(self.account_name + " 第%s张图片下载成功" % image_index)
                    image_index += 1
            else:
                log.error(self.account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_index, image_info["image_url"], robot.get_save_net_file_failed_reason(save_file_return["code"])))
                continue

        # 图片下载完毕
        self.temp_path_list = []  # 临时目录设置清除
        self.total_image_count += (image_index - 1) - int(self.account_info[1])  # 计数累加
        self.account_info[1] = str(image_index - 1)  # 设置存档记录
        self.account_info[2] = str(image_info_list[0]["image_time"])  # 设置存档记录

    def run(self):
        try:
            # 获取所有可下载图片
            image_info_list = self.get_crawl_list()
            log.step(self.account_name + " 需要下载的全部图片解析完毕，共%s张" % len(image_info_list))

            # 从最早的图片开始下载
            deal_image_info_list = []
            while len(image_info_list) > 0:
                image_info = image_info_list.pop()
                # 下一张图片的上传时间一致，合并下载
                deal_image_info_list.append(image_info)
                if len(image_info_list) > 0 and image_info_list[-1]["image_time"] == image_info["image_time"]:
                    continue

                # 下载同一上传时间的所有图片
                self.crawl_image(deal_image_info_list)
                deal_image_info_list = []  # 累加图片地址清除
                self.main_thread_check()  # 检测主线程运行状态
        except SystemExit, se:
            if se.code == 0:
                log.step(self.account_name + " 提前退出")
            else:
                log.error(self.account_name + " 异常退出")
            # 如果临时目录变量不为空，表示同一时间的图片正在下载中，需要把下载了部分的内容给清理掉
            self.clean_temp_path()
        except Exception, e:
            log.error(self.account_name + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 保存最后的信息
        with self.thread_lock:
            tool.write_file("\t".join(self.account_info), self.main_thread.temp_save_data_path)
            self.main_thread.total_image_count += self.total_image_count
            self.main_thread.account_list.pop(self.account_id)
        log.step(self.account_name + " 下载完毕，总共获得%s张图片" % self.total_image_count)
        self.notify_main_thread()


if __name__ == "__main__":
    Weibo().main()
