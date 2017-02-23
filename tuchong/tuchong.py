# -*- coding:UTF-8  -*-
"""
图虫图片爬虫
https://tuchong.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, net, robot, tool
import os
import threading
import time
import traceback

ACCOUNTS = []
IMAGE_COUNT_PER_PAGE = 20  # 每次请求获取的图片数量
TOTAL_IMAGE_COUNT = 0
GET_PAGE_COUNT = 0
IMAGE_TEMP_PATH = ""
IMAGE_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_SORT = True
IS_DOWNLOAD_IMAGE = True


# 获取账号首页
def get_home_page(account_name):
    home_page_url = "https://%s.tuchong.com" % account_name
    home_page_url_response = net.http_request(home_page_url)
    extra_info = {
        "account_id": None,  # account id（字母账号->数字账号)
    }
    if home_page_url_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        extra_info["account_id"] = tool.find_sub_string(home_page_url_response.data, '<div class="time-line" data-site-id="', '">')
    home_page_url_response.extra_info = extra_info
    return home_page_url_response


# 获取指定时间点起的一页相册信息列表
# account_name -> deer-vision
# account_id -> 1186455
# post_time -> 2016-11-11 11:11:11
def get_one_page_album(account_id, post_time):
    # https://deer-vision.tuchong.com/rest/sites/1186455/posts/2016-11-11%2011:11:11?limit=20
    index_page_url = "https://www.tuchong.com/rest/sites/%s/posts/%s?limit=%s" % (account_id, post_time, IMAGE_COUNT_PER_PAGE)
    return net.http_request(index_page_url, json_decode=True)


# 生成图片大图下载地址
def generate_large_image_url(account_id, image_id):
    return "https://photo.tuchong.com/%s/f/%s.jpg" % (account_id, image_id)


class TuChong(robot.Robot):
    def __init__(self):
        global GET_PAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT
        global IS_DOWNLOAD_IMAGE

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
        }
        robot.Robot.__init__(self, sys_config, use_urllib3=True)

        # 设置全局变量，供子线程调用
        GET_PAGE_COUNT = self.get_page_count
        IMAGE_TEMP_PATH = self.image_temp_path
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        IS_SORT = self.is_sort
        IS_DOWNLOAD_IMAGE = self.is_download_image
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

    def main(self):
        global ACCOUNTS

        # 解析存档文件
        # account_id  last_post_id
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "0"])
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

            if account_name.isdigit():
                account_id = account_name
            else:
                home_page_response = get_home_page(account_name)
                if home_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                    log.error(account_name + " 主页无法访问，原因：%s" % robot.get_http_request_failed_reason(home_page_response.status))
                    tool.process_exit()
                if not home_page_response.extra_info["account_id"]:
                    log.error(account_name + " account id解析失败")
                    tool.process_exit()
                account_id = home_page_response.extra_info["account_id"]

            image_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)

            this_account_total_image_count = 0
            post_count = 0
            first_post_id = "0"
            post_time = "2016-11-16 14:12:00"
            is_over = False
            while not is_over:
                log.step(account_name + " 开始解析%s后的一页相册" % post_time)

                # 获取一页相册
                index_page_response = get_one_page_album(account_id, post_time)
                if index_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                    log.error(account_name + " %s后的一页相册访问失败，原因：%s" % (post_time, robot.get_http_request_failed_reason(index_page_response.status)))
                    tool.process_exit()

                if not (robot.check_sub_key(("posts", "result"), index_page_response.json_data) and index_page_response.json_data["result"] == "SUCCESS"):
                    log.error(account_name + " %s后的一页相册 %s 解析失败" % (post_time, index_page_response.json_data))
                    continue

                # 如果为空，表示已经取完了
                if len(index_page_response.json_data["posts"]) == 0:
                    break

                log.trace(account_name + " %s后的一页相册：%s" % (post_time, index_page_response.json_data["posts"]))

                for post_info in index_page_response.json_data["posts"]:
                    if not robot.check_sub_key(("title", "post_id", "published_at", "images"), post_info):
                        log.error(account_name + " 相册信息解析失败：%s" % post_info)
                        continue

                    post_id = str(post_info["post_id"])

                    # 检查信息页id是否小于上次的记录
                    if int(post_id) <= int(self.account_info[1]):
                        is_over = True
                        break

                    # 将第一个信息页的id做为新的存档记录
                    if first_post_id == "0":
                        first_post_id = post_id

                    log.step(account_name + " 开始解析相册%s" % post_id)

                    # 过滤标题中不支持的字符
                    title = robot.filter_text(post_info["title"])
                    if title:
                        post_path = os.path.join(image_path, "%s %s" % (post_id, title))
                    else:
                        post_path = os.path.join(image_path, post_id)
                    if not tool.make_dir(post_path, 0):
                        # 目录出错，把title去掉后再试一次，如果还不行退出
                        log.error(account_name + " 创建相册目录 %s 失败，尝试不使用title" % post_path)
                        post_path = os.path.join(image_path, post_id)
                        if not tool.make_dir(post_path, 0):
                            log.error(account_name + " 创建相册目录 %s 失败" % post_path)
                            tool.process_exit()

                    image_count = 0
                    for image_info in post_info["images"]:
                        image_count += 1
                        if not robot.check_sub_key(("img_id",), image_info):
                            log.error(account_name + " 相册%s 第%s张图片解析失败" % (post_id, image_count))
                            continue
                        image_url = generate_large_image_url(account_id, image_info["img_id"])
                        log.step(account_name + " 相册%s 开始下载第%s张图片 %s" % (post_id, image_count, image_url))

                        file_path = os.path.join(post_path, "%s.jpg" % image_count)
                        save_file_return = net.save_net_file(image_url, file_path)
                        if save_file_return["status"] == 1:
                            log.step(account_name + " 相册%s 第%s张图片下载成功" % (post_id, image_count))
                        else:
                            log.error(account_name + " 相册%s 第%s张图片 %s 下载失败，原因：%s" % (post_info["post_id"], image_count, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
                    this_account_total_image_count += image_count

                    if not is_over:
                        # 达到配置文件中的下载页数，结束
                        if 0 < GET_PAGE_COUNT < post_count:
                            is_over = True
                        else:
                            # 相册发布时间
                            post_time = post_info["published_at"]
                            post_count += 1

            log.step(account_name + " 下载完毕，总共获得%s张图片" % this_account_total_image_count)

            # 新的存档记录
            if first_post_id != "0":
                self.account_info[1] = first_post_id

            # 保存最后的信息
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            self.thread_lock.acquire()
            TOTAL_IMAGE_COUNT += this_account_total_image_count
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
    TuChong().main()
