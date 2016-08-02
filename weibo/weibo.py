# -*- coding:UTF-8  -*-
"""
微博图片&视频爬虫
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, robot, tool
import hashlib
import json
import os
import random
import re
import threading
import time
import traceback
import urllib2

ACCOUNTS = []
INIT_SINCE_ID = "9999999999999999"
IMAGE_COUNT_PER_PAGE = 20  # 每次请求获取的图片数量
TOTAL_IMAGE_COUNT = 0
TOTAL_VIDEO_COUNT = 0
GET_IMAGE_COUNT = 0
GET_VIDEO_COUNT = 0
IMAGE_TEMP_PATH = ""
IMAGE_DOWNLOAD_PATH = ""
VIDEO_TEMP_PATH = ""
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_SORT = True
IS_DOWNLOAD_IMAGE = True
IS_DOWNLOAD_VIDEO = True

threadLock = threading.Lock()


def trace(msg):
    threadLock.acquire()
    log.trace(msg)
    threadLock.release()


def print_error_msg(msg):
    threadLock.acquire()
    log.error(msg)
    threadLock.release()


def print_step_msg(msg):
    threadLock.acquire()
    log.step(msg)
    threadLock.release()


# 图片二进制字节保存为本地文件
def save_image(image_byte, image_path):
    image_path = tool.change_path_encoding(image_path)
    image_file = open(image_path, "wb")
    image_file.write(image_byte)
    image_file.close()


# 将二进制数据生成MD5的hash值
def md5(file_byte):
    md5_obj = hashlib.md5()
    md5_obj.update(file_byte)
    return md5_obj.hexdigest()


# 访问微博域名网页，自动判断是否需要跳转
def visit_weibo(url):
    page_return_code, page_response = tool.http_request(url)[:2]
    if page_return_code == 1:
        # 有重定向
        redirect_url_find = re.findall('location.replace\(["|\']([^"|^\']*)["|\']\)', page_response)
        if len(redirect_url_find) == 1:
            return visit_weibo(redirect_url_find[0])
        # 没有cookies无法访问的处理
        if page_response.find("用户名或密码错误") != -1:
            print_error_msg("登陆状态异常，请在浏览器中重新登陆微博账号")
            tool.process_exit()
        # else:
        #     try:
        #         temp_page_response = page_response.decode("GBK")
        #         if temp_page_response.find("用户名或密码错误") != -1:
        #             print_error_msg("登陆状态异常，请在浏览器中重新登陆微博账号")
        #             tool.process_exit()
        #     except Exception,e:
        #         print e
        #         pass
        # 返回页面
        if page_response:
            return str(page_response)
    return False


# 获取一页的图片信息
def get_weibo_photo_page_data(account_id, page_count):
    photo_page_url = "http://photo.weibo.com/photos/get_all"
    photo_page_url += "?uid=%s&count=%s&page=%s&type=3" % (account_id, IMAGE_COUNT_PER_PAGE, page_count)
    photo_page_data = visit_weibo(photo_page_url)
    try:
        page = json.loads(photo_page_data)
    except ValueError:
        pass
    else:
        if robot.check_sub_key(("data", ), page):
            if robot.check_sub_key(("total", "photo_list"), page["data"]):
                return page["data"]
    return None


# 获取账号对应的page_id
def get_weibo_account_page_id(account_id):
    for i in range(0, 50):
        index_url = "http://weibo.com/u/%s?is_all=1" % account_id
        index_page = visit_weibo(index_url)
        if index_page:
            page_id = tool.find_sub_string(index_page, "$CONFIG['page_id']='", "'")
            if page_id:
                return page_id
        time.sleep(5)
    return None


# 获取一页的视频信息
def get_weibo_video_page_data(page_id, since_id):
    video_album_url = "http://weibo.com/p/aj/album/loading"
    video_album_url += "?type=video&since_id=%s&page_id=%s&page=1&ajax_call=1" % (since_id, page_id)
    for i in range(0, 50):
        video_page = visit_weibo(video_album_url)
        if video_page:
            try:
                video_page = json.loads(video_page)
            except ValueError:
                pass
            else:
                if robot.check_sub_key(("code", "data"), video_page):
                    if int(video_page["code"]) == 100000:
                        return video_page[u"data"].encode("utf-8")
        time.sleep(5)
    return None


# 从视频播放页面中提取源地址
def find_real_video_url(video_page_url, account_name):
    # http://miaopai.com/show/Gmd7rwiNrc84z5h6S9DhjQ__.htm
    if video_page_url.find("miaopai.com/show/") >= 0:  # 秒拍
        video_id = video_page_url.split("/")[-1].split(".")[0]
        return 1, ["http://wsqncdn.miaopai.com/stream/%s.mp4" % video_id]
    # http://video.weibo.com/show?fid=1034:e608e50d5fa95410748da61a7dfa2bff
    elif video_page_url.find("video.weibo.com/show?fid=") >= 0:  # 微博视频
        # 多次尝试，在多线程访问的时候有较大几率无法返回正确的信息
        for i in range(0, 50):
            source_video_page = visit_weibo(video_page_url)
            if source_video_page:
                ssig_file_url = tool.find_sub_string(source_video_page, 'flashvars=\\"file=', '\\"')
                if ssig_file_url:
                    ssig_file_page = visit_weibo(urllib2.unquote(ssig_file_url))
                    if ssig_file_page:
                        ssig_list = re.findall("\s([^#]\S*)", ssig_file_page)
                        if len(ssig_list) >= 1:
                            video_source_url = []
                            for ssig in ssig_list:
                                video_source_url.append("http://us.sinaimg.cn/" + ssig)
                            return 1, video_source_url
            time.sleep(5)
        return -1, []
    # http://www.meipai.com/media/98089758
    elif video_page_url.find("www.meipai.com/media") >= 0:  # 美拍
        source_video_page_return_code, source_video_page = tool.http_request(video_page_url)[:2]
        if source_video_page_return_code == 1:
            video_url = tool.find_sub_string(source_video_page, '<meta content="og:video:url" property="', '">')
            if video_url:
                return 1, [video_url]
            return -1, []
        else:
            return -2, []
    # http://v.xiaokaxiu.com/v/0YyG7I4092d~GayCAhwdJQ__.html
    elif video_page_url.find("v.xiaokaxiu.com/v/") >= 0:  # 小咖秀
        video_id = video_page_url.split("/")[-1].split(".")[0]
        return 1, ["http://bsyqncdn.miaopai.com/stream/%s.mp4" % video_id]
    # http://www.weishi.com/t/2000546051794045
    elif video_page_url.find("www.weishi.com/t/") >= 0:  # 微视
        source_video_page_return_code, source_video_page = tool.http_request(video_page_url)[:2]
        if source_video_page_return_code == 1:
            video_id_find = re.findall('<div class="vBox js_player"[\s]*id="([^"]*)"', source_video_page)
            if len(video_id_find) == 1:
                video_page_id = video_page_url.split("/")[-1]
                video_info_url = "http://wsi.weishi.com/weishi/video/downloadVideo.php?vid=%s&device=1&id=%s" % (video_id_find[0], video_page_id)
                video_info_page_return_code, video_info_page = tool.http_request(video_info_url)[:2]
                if video_info_page_return_code == 1:
                    try:
                        video_info_page = json.loads(video_info_page)
                    except ValueError:
                        pass
                    else:
                        if robot.check_sub_key(("data", ), video_info_page):
                            if robot.check_sub_key(("url", ), video_info_page["data"]):
                                return 1, [random.choice(video_info_page["data"]["url"])]
            return -1, []
        else:
            return -2, []
    else:  # 其他视频，暂时不支持，收集看看有没有
        return -3, []


# 访问图片源地址，判断是不是图片已经被删除或暂时无法访问后，返回图片字节
def get_image_byte(image_url):
    for i in range(0, 10):
        image_return_code, image_data = tool.http_request(image_url)[:2]
        if image_return_code == 1:
            # 处理获取的文件为weibo默认获取失败的图片
            md5_digest = md5(image_data)
            if md5_digest in ["14f2559305a6c96608c474f4ca47e6b0"]:
                return -2, None  # 被系统自动删除的图片
            # 不是暂时无法访问，否则重试
            if md5_digest not in ["d29352f3e0f276baaf97740d170467d7", "7bd88df2b5be33e1a79ac91e7d0376b5"]:
                return 1, image_data
        time.sleep(5)
    return -1, None


class Weibo(robot.Robot):
    def __init__(self, extra_config=None):
        global GET_IMAGE_COUNT
        global GET_VIDEO_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global VIDEO_TEMP_PATH
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT
        global IS_DOWNLOAD_IMAGE
        global IS_DOWNLOAD_VIDEO

        robot.Robot.__init__(self, extra_config)

        # 设置全局变量，供子线程调用
        GET_IMAGE_COUNT = self.get_image_count
        GET_VIDEO_COUNT = self.get_video_count
        IMAGE_TEMP_PATH = self.image_temp_path
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        VIDEO_TEMP_PATH = self.video_temp_path
        VIDEO_DOWNLOAD_PATH = self.video_download_path
        IS_SORT = self.is_sort
        IS_DOWNLOAD_IMAGE = self.is_download_image
        IS_DOWNLOAD_VIDEO = self.is_download_video
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

        tool.print_msg("配置文件读取完成")

    def main(self):
        global ACCOUNTS

        if not IS_DOWNLOAD_IMAGE and not IS_DOWNLOAD_VIDEO:
            print_error_msg("下载图片和视频都没有开启，请检查配置！")
            tool.process_exit()

        start_time = time.time()

        # 创建图片保存目录
        if IS_DOWNLOAD_IMAGE:
            print_step_msg("创建图片根目录：" + IMAGE_DOWNLOAD_PATH)
            if not tool.make_dir(IMAGE_DOWNLOAD_PATH, 0):
                print_error_msg("创建图片根目录：" + IMAGE_DOWNLOAD_PATH + " 失败")
                tool.process_exit()

        # 创建视频保存目录
        if IS_DOWNLOAD_VIDEO:
            print_step_msg("创建视频根目录：" + VIDEO_DOWNLOAD_PATH)
            if not tool.make_dir(VIDEO_DOWNLOAD_PATH, 0):
                print_error_msg("创建视频根目录：" + VIDEO_DOWNLOAD_PATH + " 失败")
                tool.process_exit()

        # 设置代理
        if self.is_proxy == 1:
            tool.set_proxy(self.proxy_ip, self.proxy_port, "http")

        # 设置系统cookies
        if not tool.set_cookie(self.cookie_path, self.browser_version, ("weibo.com", ".sina.com.cn")):
            print_error_msg("导入浏览器cookies失败")
            tool.process_exit()

        # 寻找存档，如果没有结束进程
        account_list = {}
        if os.path.exists(self.save_data_path):
            # account_id  image_count  last_image_time  video_count  last_video_url  (account_name)
            account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0", "0", ""])
            ACCOUNTS = account_list.keys()
        else:
            print_error_msg("存档文件：" + self.save_data_path + "不存在")
            tool.process_exit()

        # 创建临时存档文件
        new_save_data_file = open(NEW_SAVE_DATA_PATH, "w")
        new_save_data_file.close()

        # 先访问下页面，产生cookies
        visit_weibo("http://www.weibo.com/")
        time.sleep(2)

        # 启用线程监控是否需要暂停其他下载线程
        process_control_thread = tool.ProcessControl()
        process_control_thread.setDaemon(True)
        process_control_thread.start()

        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for account_id in sorted(account_list.keys()):
            # 检查正在运行的线程数
            while threading.activeCount() >= self.thread_count + main_thread_count:
                if tool.is_process_end() == 0:
                    time.sleep(10)
                else:
                    break

            # 提前结束
            if tool.is_process_end() > 0:
                break

            # 开始下载
            thread = Download(account_list[account_id])
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
        tool.remove_dir(VIDEO_TEMP_PATH)

        # 重新排序保存存档文件
        account_list = robot.read_save_data(NEW_SAVE_DATA_PATH, 0, [])
        temp_list = [account_list[key] for key in sorted(account_list.keys())]
        tool.write_file(tool.list_to_string(temp_list), self.save_data_path, 2)
        os.remove(NEW_SAVE_DATA_PATH)

        duration_time = int(time.time() - start_time)
        print_step_msg("全部下载完毕，耗时" + str(duration_time) + "秒，共计图片" + str(TOTAL_IMAGE_COUNT) + "张，视频" + str(TOTAL_VIDEO_COUNT) + "个")


class Download(threading.Thread):
    def __init__(self, account_info):
        threading.Thread.__init__(self)
        self.account_info = account_info

    def run(self):
        global TOTAL_IMAGE_COUNT
        global TOTAL_VIDEO_COUNT

        account_id = self.account_info[0]
        if len(self.account_info) >= 6 and self.account_info[5]:
            account_name = self.account_info[5]
        else:
            account_name = self.account_info[0]

        try:
            print_step_msg(account_name + " 开始")

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if IS_SORT:
                image_path = os.path.join(IMAGE_TEMP_PATH, account_name)
                video_path = os.path.join(VIDEO_TEMP_PATH, account_name)
            else:
                image_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
                video_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)

            # 视频
            video_count = 1
            page_id = None
            first_video_url = ""
            is_over = False
            need_make_video_dir = True
            since_id = INIT_SINCE_ID
            while IS_DOWNLOAD_VIDEO and (not is_over):
                # 获取page_id
                if page_id is None:
                    page_id = get_weibo_account_page_id(account_id)
                    if page_id is None:
                        print_error_msg(account_name + " 微博主页没有获取到page_id")
                        break

                # 获取指定时间点后的一页视频信息
                video_page_data = get_weibo_video_page_data(page_id, since_id)
                if video_page_data is None:
                    print_error_msg(account_name + " 视频列表解析异常")
                    first_video_url = ""  # 存档恢复
                    break

                # 匹配获取全部的视频页面
                video_page_url_list = re.findall('<a target="_blank" href="([^"]*)"><div ', video_page_data)
                trace(account_name + "since_id：" + since_id + "中的全部视频：" + str(video_page_url_list))
                for video_page_url in video_page_url_list:
                    # 将第一个视频的地址做为新的存档记录
                    if first_video_url == "":
                        first_video_url = video_page_url
                    # 检查是否是上一次的最后视频
                    if self.account_info[4] == video_page_url:
                        is_over = True
                        break
                    # 获取这个视频的视频源地址（下载地址）
                    return_code, video_source_url_list = find_real_video_url(video_page_url, account_name)
                    if return_code != 1:
                        if return_code == -1:
                            print_error_msg(account_name + " 第" + str(video_count) + "个视频：" + video_page_url + "没有获取到源地址")
                        elif return_code == -2:
                            print_error_msg(account_name + " 第" + str(video_count) + "个视频：" + video_page_url + "无法访问")
                        elif return_code == -3:
                            print_error_msg(account_name + " 第" + str(video_count) + "个视频：" + video_page_url + "，暂不支持的视频源")
                        continue
                    # 下载
                    for video_source_url in video_source_url_list:
                        print_step_msg(account_name + " 开始下载第" + str(video_count) + "个视频：" + video_page_url)

                        video_file_path = os.path.join(video_path, str("%04d" % video_count) + ".mp4")
                        # 第一个视频，创建目录
                        if need_make_video_dir:
                            if not tool.make_dir(video_path, 0):
                                print_error_msg(account_name + " 创建图片下载目录： " + video_path + " 失败")
                                tool.process_exit()
                            need_make_video_dir = False
                        if tool.save_net_file(video_source_url, video_file_path):
                            print_step_msg(account_name + " 第" + str(video_count) + "个视频下载成功")
                            video_count += 1
                        else:
                            print_error_msg(account_name + " 第" + str(video_count) + "个视频 " + video_page_url + " 下载失败")

                    # 达到配置文件中的下载数量，结束
                    if 0 < GET_VIDEO_COUNT < video_count:
                        is_over = True
                        break

                if not is_over:
                    # 获取下一页的since_id
                    since_id = tool.find_sub_string(video_page_data, 'type=video&owner_uid=&since_id=', '">')
                    if not since_id:
                        break

            # 有历史记录，并且此次没有获得正常结束的标记，说明历史最后的视频已经被删除了
            if self.account_info[4] != "" and video_count > 1 and not is_over :
                print_error_msg(account_name + " 没有找到上次下载的最后一个视频地址")

            # 图片
            image_count = 1
            page_count = 1
            first_image_time = "0"
            unique_list = []
            is_over = False
            need_make_image_dir = True
            while IS_DOWNLOAD_IMAGE and (not is_over):
                # 获取指定一页图片的信息
                photo_page_data = get_weibo_photo_page_data(account_id, page_count)
                if photo_page_data is None:
                    print_error_msg(account_name + " 图片列表解析错误")
                    first_image_time = "0"  # 存档恢复
                    break

                trace(account_name + "第：" + str(page_count) + "页的全部图片信息：" + str(photo_page_data))
                for image_info in photo_page_data["photo_list"]:
                    if not robot.check_sub_key(("pic_host", "pic_name", "timestamp"), image_info):
                        print_error_msg(account_name + " 第" + str(image_count) + "张图片信息解析错误 " + image_info)
                        continue

                    # 新增图片导致的重复判断
                    if image_info["pic_name"] in unique_list:
                        continue
                    else:
                        unique_list.append(image_info["pic_name"])
                    # 将第一张图片的上传时间做为新的存档记录
                    if first_image_time == "0":
                        first_image_time = str(image_info["timestamp"])
                    # 检查是否图片时间小于上次的记录
                    if int(image_info["timestamp"]) <= int(self.account_info[2]):
                        is_over = True
                        break

                    # 下载
                    image_url = str(image_info["pic_host"]) + "/large/" + str(image_info["pic_name"])
                    print_step_msg(account_name + " 开始下载第" + str(image_count) + "张图片：" + image_url)
                    # 获取图片的二进制数据，并且判断这个图片是否是可用的
                    image_status, image_byte = get_image_byte(image_url)
                    if image_status != 1:
                        if image_status == -1:
                            print_error_msg(account_name + " 第" + str(image_count) + "张图片 " + image_url + " 下载失败")
                        elif image_status == -2:
                            print_error_msg(account_name + " 第" + str(image_count) + "张图片 " + image_url + " 资源已被删除")
                        continue

                    # 第一张图片，创建目录
                    if need_make_image_dir:
                        if not tool.make_dir(image_path, 0):
                            print_error_msg(account_name + " 创建图片下载目录： " + image_path + " 失败")
                            tool.process_exit()
                        need_make_image_dir = False

                    file_type = image_url.split(".")[-1]
                    if file_type.find("/") != -1:
                        file_type = "jpg"
                    image_file_path = os.path.join(image_path, str("%04d" % image_count) + "." + file_type)
                    save_image(image_byte, image_file_path)
                    print_step_msg(account_name + " 第" + str(image_count) + "张图片下载成功")
                    image_count += 1

                    # 达到配置文件中的下载数量，结束
                    if 0 < GET_IMAGE_COUNT < image_count:
                        is_over = True
                        break

                if not is_over:
                    # 根据总的图片数量和每页显示的图片数量，计算是否还有下一页
                    if (photo_page_data["total"] / IMAGE_COUNT_PER_PAGE) > (page_count - 1):
                        page_count += 1
                    else:
                        # 全部图片下载完毕
                        is_over = True

            print_step_msg(account_name + " 下载完毕，总共获得" + str(image_count - 1) + "张图片和" + str(video_count - 1) + "个视频")

            # 排序
            if IS_SORT:
                if image_count > 1:
                    destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
                    if robot.sort_file(image_path, destination_path, int(self.account_info[1]), 4):
                        print_step_msg(account_name + " 图片从下载目录移动到保存目录成功")
                    else:
                        print_error_msg(account_name + " 创建图片保存目录： " + destination_path + " 失败")
                        tool.process_exit()
                if video_count > 1:
                    destination_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)
                    if robot.sort_file(video_path, destination_path, int(self.account_info[3]), 4):
                        print_step_msg(account_name + " 视频从下载目录移动到保存目录成功")
                    else:
                        print_error_msg(account_name + " 创建视频保存目录： " + destination_path + " 失败")
                        tool.process_exit()

            # 新的存档记录
            if first_image_time != "0":
                self.account_info[1] = str(int(self.account_info[1]) + image_count - 1)
                self.account_info[2] = first_image_time
            if first_video_url != "":
                self.account_info[3] = str(int(self.account_info[3]) + video_count - 1)
                self.account_info[4] = first_video_url

            # 保存最后的信息
            threadLock.acquire()
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            TOTAL_IMAGE_COUNT += image_count - 1
            TOTAL_VIDEO_COUNT += video_count - 1
            ACCOUNTS.remove(account_id)
            threadLock.release()

            print_step_msg(account_name + " 完成")
        except SystemExit, se:
            if se.code == 0:
                print_step_msg(account_name + " 提前退出")
            else:
                print_error_msg(account_name + " 异常退出")
        except Exception, e:
            print_step_msg(account_name + " 未知异常")
            print_error_msg(str(e) + "\n" + str(traceback.format_exc()))


if __name__ == "__main__":
    Weibo().main()
