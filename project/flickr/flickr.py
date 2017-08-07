# -*- coding:UTF-8  -*-
"""
Flickr图片爬虫
https://www.flickr.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import os
import threading
import time
import traceback

ACCOUNTS = []
IMAGE_COUNT_PER_PAGE = 2
TOTAL_IMAGE_COUNT = 0
IMAGE_TEMP_PATH = ""
IMAGE_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""


# 获取账号相册首页
def get_account_index_page(account_name):
    account_index_url = "https://www.flickr.com/photos/%s" % account_name
    account_index_response = net.http_request(account_index_url)
    result = {
        "user_id": None,  # user id
        "site_key": None,  # site key
    }
    if account_index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 获取user id
        user_id = tool.find_sub_string(account_index_response.data, '"nsid":"', '"')
        if not robot.is_integer(user_id):
            raise robot.RobotException("页面截取nsid失败\n%s" % account_index_response.data)
        result["user_id"] = user_id

        # 获取site key
        site_key = tool.find_sub_string(account_index_response.data, '"site_key":"', '"')
        if not site_key:
            raise robot.RobotException("页面截取site key失败\n%s" % account_index_response.data)
        result["site_key"] = site_key
    else:
        raise robot.RobotException(robot.get_http_request_failed_reason(account_index_response.status))
    return result


# 获取指定页数的所有图片
# user_id -> 36587311@N08
def get_one_page_photo(user_id, page_count, api_key, request_id):
    api_url = "https://api.flickr.com/services/rest"
    # API文档：https://www.flickr.com/services/api/flickr.people.getPhotos.html
    # 所有可支持的参数
    # extras = [
    #     "can_addmeta", "can_comment", "can_download", "can_share", "contact", "count_comments", "count_faves",
    #     "count_views", "date_taken", "date_upload", "description", "icon_urls_deep", "isfavorite", "ispro", "license",
    #     "media", "needs_interstitial", "owner_name", "owner_datecreate", "path_alias", "realname", "rotation",
    #     "safety_level", "secret_k", "secret_h", "url_c", "url_f", "url_h", "url_k", "url_l", "url_m", "url_n",
    #     "url_o", "url_q", "url_s", "url_sq", "url_t", "url_z", "visibility", "visibility_source", "o_dims",
    #     "is_marketplace_printable", "is_marketplace_licensable", "publiceditability"
    # ]
    post_data = {
        "per_page": IMAGE_COUNT_PER_PAGE, "page": page_count, "extras": "date_upload,url_o", "get_user_info": 0, "user_id": user_id, "view_as": "use_pref",
        "sort": "use_pref", "method": "flickr.people.getPhotos", "api_key": api_key, "format": "json", "hermes": 1, "reqId": request_id, "nojsoncallback": 1,
    }
    photo_pagination_response = net.http_request(api_url, post_data, json_decode=True)
    result = {
        "image_info_list": [],  # 所有图片信息
        "is_over": False,  # 是不是最后一页图片
    }
    if photo_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if not robot.check_sub_key(("photos",), photo_pagination_response.json_data):
            raise robot.RobotException("返回数据'photos'字段不存在\n%s" % photo_pagination_response.json_data)
        if not robot.check_sub_key(("photo", "pages"), photo_pagination_response.json_data["photos"]):
            raise robot.RobotException("返回数据'photo'或者'pages'字段不存在\n%s" % photo_pagination_response.json_data)
        if not isinstance(photo_pagination_response.json_data["photos"]["photo"], list) or len(photo_pagination_response.json_data["photos"]["photo"]) == 0:
            raise robot.RobotException("返回数据'photo'字段类型不正确\n%s" % photo_pagination_response.json_data)
        if not robot.is_integer(photo_pagination_response.json_data["photos"]["pages"]):
            raise robot.RobotException("返回数据'pages'字段类型不正确\n%s" % photo_pagination_response.json_data)
        # 获取图片信息
        for photo_info in photo_pagination_response.json_data["photos"]["photo"]:
            extra_image_info = {
                "image_url": None,  # 图片地址
                "image_time": None,  # 图片上传时间
            }
            # 获取图片上传时间
            if not robot.check_sub_key(("dateupload",), photo_info):
                raise robot.RobotException("图片信息'dateupload'字段不存在\n%s" % photo_info)
            if not robot.is_integer(photo_info["dateupload"]):
                raise robot.RobotException("图片信息'dateupload'字段类型不正确\n%s" % photo_info)
            extra_image_info["image_time"] = str(photo_info["dateupload"])

            # 获取图片地址
            if robot.check_sub_key(("url_o_cdn",), photo_info):
                extra_image_info["image_url"] = str(photo_info["url_o_cdn"])
            elif robot.check_sub_key(("url_o",), photo_info):
                extra_image_info["image_url"] = str(photo_info["url_o"])
            else:
                raise robot.RobotException("图片信息'url_o_cdn'或者'url_o'字段不存在\n%s" % photo_info)

            result["image_info_list"].append(extra_image_info)

        # 判断是不是最后一页
        if page_count >= int(photo_pagination_response.json_data["photos"]["pages"]):
            result["is_over"] = True
    else:
        raise robot.RobotException(robot.get_http_request_failed_reason(photo_pagination_response.status))
    return result


class Flickr(robot.Robot):
    def __init__(self):
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_SET_PROXY: True,
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        IMAGE_TEMP_PATH = self.image_temp_path
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

    def main(self):
        global ACCOUNTS

        # 解析存档文件
        # account_id  image_count  last_image_time
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

        account_name = self.account_info[0]

        try:
            log.step(account_name + " 开始")

            # 获取相册首页页面
            try:
                account_index_response = get_account_index_page(account_name)
            except robot.RobotException, e:
                log.error(account_name + " 相册首页访问失败，原因：%s" % e.message)
                raise

            # 生成一个随机的request id用作访问（模拟页面传入）
            request_id = tool.generate_random_string(8)

            image_count = 1
            page_count = 1
            is_over = False
            first_image_time = None
            image_path = os.path.join(IMAGE_TEMP_PATH, account_name)
            while not is_over:
                log.step(account_name + " 开始解析第%s页图片" % page_count)

                # 获取一页图片
                try:
                    photo_pagination_response = get_one_page_photo(account_index_response["user_id"], page_count, account_index_response["site_key"], request_id)
                except robot.RobotException, e:
                    log.error(account_name + " 第%s页图片信息访问失败，原因：%s" % (page_count, e.message))
                    raise

                log.trace(account_name + " 第%s页解析的所有图片：%s" % (page_count, photo_pagination_response["image_info_list"]))

                for image_info in photo_pagination_response["image_info_list"]:
                    # 检查是否达到存档记录
                    if int(self.account_info[2]) >= int(image_info["image_time"]):
                        is_over = True
                        break

                    # 新的存档记录
                    if first_image_time is None:
                        first_image_time = image_info["image_time"]

                    log.step(account_name + " 开始下载第%s张图片 %s" % (image_count, image_info["image_url"]))

                    file_type = image_info["image_url"].split(".")[-1]
                    file_path = os.path.join(image_path, "%04d.%s" % (image_count, file_type))
                    save_file_return = net.save_net_file(image_info["image_url"], file_path)
                    if save_file_return["status"] == 1:
                        log.step(account_name + " 第%s张图片下载成功" % image_count)
                        image_count += 1
                    else:
                        log.error(account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_count, image_info["image_url"], robot.get_save_net_file_failed_reason(save_file_return["code"])))

                if not is_over:
                    if photo_pagination_response["is_over"]:
                        is_over = True
                    else:
                        page_count += 1

            log.step(account_name + " 下载完毕，总共获得%s张图片" % (image_count - 1))

            # 排序
            if image_count > 1:
                destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
                if robot.sort_file(image_path, destination_path, int(self.account_info[1]), 4):
                    log.step(account_name + " 图片从下载目录移动到保存目录成功")
                else:
                    log.error(account_name + " 创建图片保存目录 %s 失败" % destination_path)
                    tool.process_exit()

            # 新的存档记录
            if first_image_time is not None:
                self.account_info[1] = str(int(self.account_info[1]) + image_count - 1)
                self.account_info[2] = first_image_time

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
    Flickr().main()
