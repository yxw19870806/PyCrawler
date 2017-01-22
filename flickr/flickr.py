# -*- coding:UTF-8  -*-
"""
Flickr图片爬虫
https://www.flickr.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, net, robot, tool
import json
import os
import threading
import time
import traceback

ACCOUNTS = []
IMAGE_COUNT_PER_PAGE = 2
TOTAL_IMAGE_COUNT = 0
GET_IMAGE_COUNT = 0
GET_PAGE_COUNT = 0
IMAGE_TEMP_PATH = ""
IMAGE_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_SORT = True


# 获取账号的user id和此次的token
def get_api_info(account_name):
    photo_index_url = "https://www.flickr.com/photos/%s" % account_name
    photo_index_response = net.http_request(photo_index_url)
    if photo_index_response.status == 200:
        user_id = tool.find_sub_string(photo_index_response.data, '"nsid":"', '"')
        site_key = tool.find_sub_string(photo_index_response.data, '"site_key":"', '"')
        return {"user_id": user_id, "site_key": site_key}
    return None


# 获取指定页数的图片信息列表
# user_id -> 36587311@N08
def get_one_page_image(user_id, page_count, api_key, request_id):
    image_data_page_url = "https://api.flickr.com/services/rest"
    # API文档：https://www.flickr.com/services/api/flickr.people.getPhotos.html
    # 所有可支持的参数
    # extra_data = [
    #     "can_addmeta", "can_comment", "can_download", "can_share", "contact", "count_comments", "count_faves",
    #     "count_views", "date_taken", "date_upload", "description", "icon_urls_deep", "isfavorite", "ispro", "license",
    #     "media", "needs_interstitial", "owner_name", "owner_datecreate", "path_alias", "realname", "rotation",
    #     "safety_level", "secret_k", "secret_h", "url_c", "url_f", "url_h", "url_k", "url_l", "url_m", "url_n",
    #     "url_o", "url_q", "url_s", "url_sq", "url_t", "url_z", "visibility", "visibility_source", "o_dims",
    #     "is_marketplace_printable", "is_marketplace_licensable", "publiceditability"
    # ]
    extra_data = ["date_upload", "url_o"]
    post_data = {
        "per_page": IMAGE_COUNT_PER_PAGE,
        "page": page_count,
        "extras": ",".join(extra_data),
        "get_user_info": 0,
        # "jump_to": "",
        "user_id": user_id,
        "view_as": "use_pref",
        "sort": "use_pref",
        # "viewerNSID": "",
        "method": "flickr.people.getPhotos",
        # "csrf": "",
        "api_key": api_key,
        "format": "json",
        "hermes": 1,
        "reqId": request_id,
        "nojsoncallback": 1,
    }
    return net.http_request(image_data_page_url, post_data, json_decode=True)


class Flickr(robot.Robot):
    def __init__(self):
        global GET_IMAGE_COUNT
        global GET_PAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_SET_PROXY: True,
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
        tool.remove_dir(IMAGE_TEMP_PATH)

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

            # 获取user id
            api_info = get_api_info(account_name)
            if api_info is None:
                log.error(account_name + " API信息查找失败")
                tool.process_exit()
            if not api_info["user_id"]:
                log.error(account_name + " user_id解析失败")
                tool.process_exit()
            if not api_info["site_key"]:
                log.error(account_name + " site_key解析失败")
                tool.process_exit()
            # 生成一个随机的request id用作访问（使用原理暂时不明，只管模拟页面传入）
            request_id = tool.generate_random_string(8)

            # 图片
            image_count = 1
            page_count = 1
            first_image_time = "0"
            is_over = False
            need_make_image_dir = True
            while not is_over:
                log.step(account_name + " 开始解析第%s页图片" % page_count)

                # 获取一页图片信息
                index_page_response = get_one_page_image(api_info["user_id"], page_count, api_info["site_key"], request_id)
                if index_page_response.status != 200:
                    log.error(account_name + " 第%s页图片信息访问失败，原因：%s" % (page_count, robot.get_http_request_failed_reason(index_page_response.status)))
                    tool.process_exit()

                # json格式验证
                if not robot.check_sub_key(("stat", "photos"), index_page_response.json_data) or index_page_response.json_data["stat"] != "ok" or \
                        not robot.check_sub_key(("photo", "total"), index_page_response.json_data["photos"]):
                    log.error(account_name + " 第%s页图片信息解析失败" % page_count)
                    tool.process_exit()

                log.trace(account_name + " 第%s页获取的所有图片：%s" % (page_count, index_page_response.json_data["photos"]["photo"]))

                for photo_info in index_page_response.json_data["photos"]["photo"]:
                    if "dateupload" not in photo_info:
                        log.error(account_name + " 第%s张图片上传时间获取失败，图片信息：%s" % (image_count, photo_info))
                        continue

                    # 检查是否是上一次的最后视频
                    if int(self.account_info[2]) >= int(photo_info["dateupload"]):
                        is_over = True
                        break

                    # 将第一张图片的上传时间做为新的存档记录
                    if first_image_time == "0":
                        first_image_time = str(photo_info["dateupload"])

                    if "url_o_cdn" in photo_info:
                        image_url = str(photo_info["url_o_cdn"])
                    elif "url_o" in photo_info:
                        image_url = str(photo_info["url_o"])
                    else:
                        log.error(account_name + " 第%s张图片下载地址获取失败，图片信息：%s" % (image_count, photo_info))
                        continue
                    log.step(account_name + " 开始下载第%s张图片 %s" % (image_count, image_url))

                    if need_make_image_dir:
                        if not tool.make_dir(image_path, 0):
                            log.error(account_name + " 创建图片下载目录 %s 失败" % image_path)
                            tool.process_exit()
                        need_make_image_dir = False

                    file_type = image_url.split(".")[-1]
                    file_path = os.path.join(image_path, "%04d.%s" % (image_count, file_type))
                    save_file_return = net.save_net_file(image_url, file_path)
                    if save_file_return["status"] == 1:
                        log.step(account_name + " 第%s张图片下载成功" % image_count)
                        image_count += 1
                    else:
                        log.error(account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_count, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

                    # 达到配置文件中的下载数量，结束
                    if 0 < GET_IMAGE_COUNT < image_count:
                        is_over = True
                        break

                if not is_over:
                    # 达到配置文件中的下载数量，结束
                    if 0 < GET_PAGE_COUNT <= page_count:
                        is_over = True
                    elif page_count >= int(index_page_response.json_data["photos"]["pages"]):
                        is_over = True
                    else:
                        page_count += 1

            log.step(account_name + " 下载完毕，总共获得%s张图片" % (image_count - 1))

            # 排序
            if IS_SORT and image_count > 1:
                destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
                if robot.sort_file(image_path, destination_path, int(self.account_info[1]), 4):
                    log.step(account_name + " 图片从下载目录移动到保存目录成功")
                else:
                    log.error(account_name + " 创建图片保存目录 %s 失败" % destination_path)
                    tool.process_exit()

            # 新的存档记录
            if first_image_time != "0":
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
