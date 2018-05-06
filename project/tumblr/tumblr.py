# -*- coding:UTF-8  -*-
"""
tumblr图片和视频爬虫
http://www.tumblr.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import os
import re
import threading
import time
import traceback
import urllib
import urlparse

EACH_PAGE_COUNT = 100
IS_LOGIN = True
COOKIE_INFO = {}
USER_AGENT = None
IS_STEP_ERROR_403_AND_404 = False


# 检测登录状态
def check_login():
    if not COOKIE_INFO:
        return False
    index_url = "https://www.tumblr.com/"
    index_response = net.http_request(index_url, method="GET", cookies_list=COOKIE_INFO, is_auto_redirect=False)
    if index_response.status == 302 and index_response.getheader("Location") == "https://www.tumblr.com/dashboard":
        safe_mode_url = "https://www.tumblr.com/safe-mode?url=https://www.tumblr.com/"
        safe_mode_response = net.http_request(safe_mode_url, method="GET", header_list={"User-Agent": USER_AGENT}, cookies_list=COOKIE_INFO, is_auto_redirect=False)
        if safe_mode_response.status == 404:
            COOKIE_INFO.update(net.get_cookies_from_response_header(safe_mode_response.headers))
        return True
    return False


# 获取首页，判断是否支持https以及是否启用safe-mode和"Show this blog on the web"
def get_index_setting(account_id):
    index_url = "https://%s.tumblr.com/" % account_id
    index_response = net.http_request(index_url, method="GET", is_auto_redirect=False)
    is_https = True
    is_safe_mode = False
    is_private = False
    if index_response.status == 302:
        redirect_url = index_response.getheader("Location")
        if redirect_url.find("http://%s.tumblr.com/" % account_id) == 0:
            is_https = False
            index_url = "http://%s.tumblr.com/" % account_id
            index_response = net.http_request(index_url, method="GET", is_auto_redirect=False)
            if index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
                return is_https, is_safe_mode, is_private
            elif index_response.status != 302:
                raise crawler.CrawlerException(crawler.request_failre(index_response.status))
            redirect_url = index_response.getheader("Location")
        if redirect_url.find("www.tumblr.com/safe-mode?url=") > 0:
            is_safe_mode = True
            if tool.find_sub_string(redirect_url, "?https://www.tumblr.com/safe-mode?url=").find("http://") == 0:
                is_https = False
        # "Show this blog on the web" disabled
        elif redirect_url.find("//www.tumblr.com/login_required/%s" % account_id) > 0:
            is_private = True
    elif index_response.status == 404:
        raise crawler.CrawlerException("账号不存在")
    elif index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(index_response.status))
    return is_https, is_safe_mode, is_private


# 获取一页的日志地址列表
def get_one_page_post(account_id, page_count, is_https, is_safe_mode):
    if is_https:
        protocol_type = "https"
    else:
        protocol_type = "http"
    if page_count == 1:
        post_pagination_url = "%s://%s.tumblr.com/" % (protocol_type, account_id)
    else:
        post_pagination_url = "%s://%s.tumblr.com/page/%s" % (protocol_type, account_id, page_count)
    if is_safe_mode:
        header_list = {"User-Agent": USER_AGENT}
        cookies_list = COOKIE_INFO
    else:
        header_list = None
        cookies_list = None
    post_pagination_response = net.http_request(post_pagination_url, method="GET", header_list=header_list, cookies_list=cookies_list)
    result = {
        "is_over": False,  # 是不是最后一页日志
        "post_info_list": [],  # 全部日志信息
    }
    if post_pagination_response.status == 404:
        time.sleep(5)
        log.step(account_id + "第%s页日志异常，重试" % page_count)
        return get_one_page_post(account_id, page_count, is_https, is_safe_mode)
    elif post_pagination_response.status in [503, 504, net.HTTP_RETURN_CODE_RETRY] and page_count > 1:
        # 服务器错误，跳过这页
        log.error(account_id + "第%s页日志无法访问，跳过" % page_count)
        return result
    elif post_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(post_pagination_response.status))
    page_html = tool.find_sub_string(post_pagination_response.data, '<script type="application/ld+json">', "</script>").strip()
    if page_html:
        page_data = tool.json_decode(page_html)
        if page_data is None:
            raise crawler.CrawlerException("日志信息加载失败\n%s" % page_html)
        if not crawler.check_sub_key(("itemListElement",), page_data):
            raise crawler.CrawlerException("日志信息'itemListElement'字段不存在\n%s" % page_data)
        if len(page_data["itemListElement"]) == 0:
            raise crawler.CrawlerException("日志信息'itemListElement'字段长度不正确\n%s" % page_data)
        # 单条日志
        for post_info in page_data["itemListElement"]:
            result_post_info = {
                "post_url": None,  # 日志地址
            }
            # 获取日志地址
            if not crawler.check_sub_key(("url",), post_info):
                raise crawler.CrawlerException("日志信息'url'字段不存在\n%s" % page_data)
            post_url_split = urlparse.urlsplit(post_info["url"].encode("UTF-8"))
            result_post_info["post_url"] = str(post_url_split[0] + "://" + post_url_split[1] + urllib.quote(post_url_split[2]))
            result["post_info_list"].append(result_post_info)
    else:
        result["is_over"] = True
    return result


# 获取一页的私人日志地址列表
def get_one_page_private_blog(account_id, page_count):
    post_pagination_url = "https://www.tumblr.com/svc/indash_blog"
    query_data = {
        "limit": EACH_PAGE_COUNT,
        "offset": (page_count - 1) * EACH_PAGE_COUNT,
        "post_id": "",
        "should_bypass_safemode": "false",
        "should_bypass_tagfiltering": "false",
        "tumblelog_name_or_id": account_id,
    }
    header_list = {
        "Host": "www.tumblr.com",
        "Referer": "https://www.tumblr.com/dashboard/blog/%s/" % account_id,
        "User-Agent": USER_AGENT,
        "X-Requested-With": "XMLHttpRequest",
    }
    post_pagination_response = net.http_request(post_pagination_url, method="GET", fields=query_data, header_list=header_list, cookies_list=COOKIE_INFO, json_decode=True)
    result = {
        "is_over": [],  # 是不是最后一页日志
        "post_info_list": [],  # 全部日志信息
    }
    if post_pagination_response.status == 404:
        time.sleep(5)
        return get_one_page_private_blog(account_id, page_count)
    elif post_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(post_pagination_response.status))
    if not crawler.check_sub_key(("meta",), post_pagination_response.json_data):
        raise crawler.CrawlerException("返回信息'meta'字段不存在\n%s" % post_pagination_response.json_data)
    if not crawler.check_sub_key(("status",), post_pagination_response.json_data["meta"]):
        raise crawler.CrawlerException("返回信息'status'字段不存在\n%s" % post_pagination_response.json_data)
    if not crawler.is_integer(post_pagination_response.json_data["meta"]["status"]):
        raise crawler.CrawlerException("返回信息'status'字段类型不正确\n%s" % post_pagination_response.json_data)
    if int(post_pagination_response.json_data["meta"]["status"]) != 200:
        raise crawler.CrawlerException("返回信息'status'字段取值不正确\n%s" % post_pagination_response.json_data)
    if not crawler.check_sub_key(("response",), post_pagination_response.json_data):
        raise crawler.CrawlerException("返回信息'response'字段不存在\n%s" % post_pagination_response.json_data)
    if not crawler.check_sub_key(("posts",), post_pagination_response.json_data["response"]):
        raise crawler.CrawlerException("返回信息'posts'字段不存在\n%s" % post_pagination_response.json_data)
    for post_info in post_pagination_response.json_data["response"]["posts"]:
        result_post_info = {
            "has_video": False,  # 是不是包含视频
            "image_url_list": [],  # 全部图片地址
            "post_url": None,  # 日志地址
            "video_url": None,  # 视频地址
        }
        if not crawler.check_sub_key(("post_url",), post_info):
            raise crawler.CrawlerException("日志信息'post_url'字段不存在\n%s" % post_info)
        post_url_split = urlparse.urlsplit(post_info["post_url"].encode("UTF-8"))
        result_post_info["post_url"] = post_url_split[0] + "://" + post_url_split[1] + urllib.quote(post_url_split[2])
        if not crawler.check_sub_key(("type",), post_info):
            raise crawler.CrawlerException("日志信息'type'字段不存在\n%s" % post_info)
        # 视频
        if post_info["type"] == "video":
            if not crawler.check_sub_key(("player",), post_info):
                raise crawler.CrawlerException("日志信息'player'字段不存在\n%s" % post_info)
            result_post_info["is_video"] = True
            # 获取视频地址
            max_width = 0
            video_url = None
            for video_info in post_info["player"]:
                if not crawler.check_sub_key(("width", "embed_code"), video_info):
                    raise crawler.CrawlerException("视频信息'width'或'embed_code'字段不存在\n%s" % video_info)
                if not crawler.is_integer(video_info["width"]):
                    raise crawler.CrawlerException("视频信息'width'字段类型不正确\n%s" % video_info)
                if video_info["embed_code"] is False:
                    continue
                if int(video_info["width"]) > max_width:
                    temp_video_url = tool.find_sub_string(video_info["embed_code"].encode("UTF-8"), '<source src="', '"')
                    if temp_video_url:
                        video_url = temp_video_url
                        max_width = video_info["width"]
            if video_url is not None:
                result_post_info["video_url"] = video_url
        # 图片
        elif crawler.check_sub_key(("photos",), post_info):
            for photo_info in post_info["photos"]:
                if not crawler.check_sub_key(("original_size",), photo_info):
                    raise crawler.CrawlerException("图片信息'original_size'字段不存在\n%s" % photo_info)
                if not crawler.check_sub_key(("url",), photo_info["original_size"]):
                    raise crawler.CrawlerException("图片信息'url'字段不存在\n%s" % photo_info)
                result_post_info["image_url_list"].append(str(photo_info["original_size"]["url"]))
        result["post_info_list"].append(result_post_info)
    if len(post_pagination_response.json_data["response"]["posts"]) < EACH_PAGE_COUNT:
        result["is_over"] = True
    return result


# 获取日志页面
def get_post_page(post_url, is_safe_mode):
    if is_safe_mode:
        header_list = {"User-Agent": USER_AGENT}
        cookies_list = COOKIE_INFO
    else:
        header_list = None
        cookies_list = None
    post_response = net.http_request(post_url, method="GET", header_list=header_list, cookies_list=cookies_list)
    result = {
        "has_video": False,  # 是不是包含视频
        "image_url_list": [],  # 全部图片地址
    }
    if post_response.status == 429:
        time.sleep(30)
        return get_post_page(post_url, is_safe_mode)
    elif post_response.status in [503, 504, net.HTTP_RETURN_CODE_RETRY]:
        # 服务器错误，跳过这页
        account_id = tool.find_sub_string(post_url, "://", ".tumblr.com")
        log.error(account_id + " 日志 %s 无法访问，跳过" % post_url)
        return result
    elif post_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(post_response.status))
    post_page_head = tool.find_sub_string(post_response.data, "<head", "</head>", 3)
    if not post_page_head:
        raise crawler.CrawlerException("页面截取正文失败\n%s" % post_response.data)
    # 获取og_type（页面类型的是视频还是图片或其他）
    og_type = tool.find_sub_string(post_page_head, '<meta property="og:type" content="', '" />')
    # 视频
    if og_type == "tumblr-feed:video":
        result["has_video"] = True
        # 获取图片地址
        image_url = tool.find_sub_string(post_page_head, '<meta property="og:image" content="', '" />')
        if image_url and image_url.find("assets.tumblr.com/images/og/fb_landscape_share.png") == -1:
            result["image_url_list"].append(image_url)
    elif not og_type:
        script_data_string = tool.find_sub_string(post_page_head, '<script type="application/ld+json">', "</script>").strip()
        if not script_data_string:
            raise crawler.CrawlerException("正文截取og_type失败\n%s" % post_page_head)
        script_data = tool.json_decode(script_data_string)
        if script_data is None:
            raise crawler.CrawlerException("页面脚本数据解析失败\n%s" % script_data)
        if crawler.check_sub_key(("image",), script_data):
            if isinstance(script_data["image"], dict):
                if not crawler.check_sub_key(("@list",), script_data["image"]):
                    raise crawler.CrawlerException("页面脚本数据'@list'字段不存在\n%s" % script_data)
                for image_url in script_data["image"]["@list"]:
                    result["image_url_list"].append(str(image_url))
            elif isinstance(script_data["image"], str) or isinstance(script_data["image"], unicode):
                result["image_url_list"].append(str(script_data["image"]))
            else:
                raise crawler.CrawlerException("页面脚本数据'image'字段类型错误\n%s" % script_data)
    else:
        # 获取全部图片地址
        image_url_list = re.findall('"(http[s]?://\d*[.]?media.tumblr.com/[^"]*)"', post_page_head)
        new_image_url_list = {}
        for image_url in image_url_list:
            # 头像，跳过
            if image_url.find("/avatar_") != -1 or image_url[-9:] == "_75sq.gif" or image_url[-9:] == "_75sq.jpg" or image_url[-9:] == "_75sq.png":
                continue
            elif len(re.findall("/birthday\d_", image_url)) == 1:
                continue
            image_id, resolution = analysis_image(image_url)
            # 判断是否有分辨率更小的相同图片
            if image_id in new_image_url_list:
                image_id, old_resolution = analysis_image(new_image_url_list[image_id])
                if old_resolution == -1:
                    log.error("unknown image url 1: %s, image url 2: %s" % (image_url, new_image_url_list[image_id]))
                if resolution < old_resolution:
                    continue
            new_image_url_list[image_id] = image_url
        result["image_url_list"] = new_image_url_list.values()
    return result


def analysis_image(image_url):
    temp_list = image_url.split("/")[-1].split(".")[0].split("_")
    resolution = 0
    if temp_list[0] == "tumblr":
        if temp_list[1] == "inline" and not crawler.is_integer(temp_list[2]):
            image_id = temp_list[2]
        else:
            image_id = temp_list[1]
        # http://78.media.tumblr.com/tumblr_livevtbzL31qzk5tao1_cover.jpg
        # http://78.media.tumblr.com/tumblr_ljkiptVlj61qg3k48o1_1302659992_cover.jpg
        if temp_list[-1] in ["cover", "og", "frame1"]:
            pass
        # https://78.media.tumblr.com/tumblr_lixa2piSdw1qc4p5zo1_500.jpg
        # https://78.media.tumblr.com/tumblr_lhrk7kBVz31qbijcho1_r1_500.gif
        # https://78.media.tumblr.com/4612757fb6b608d2d14939833ed2e244/tumblr_ouao969iP51rqmr8lo1_540.jpg
        elif crawler.is_integer(temp_list[-1]):
            resolution = int(temp_list[-1])
        # https://78.media.tumblr.com/19b0b807d374ed9e4ed22caf74cb1ec0/tumblr_mxukamH4GV1s4or9ao1_500h.jpg
        elif temp_list[-1][-1] == "h" and crawler.is_integer(temp_list[-1][:-1]):
            resolution = int(temp_list[-1][:-1])
        # https://78.media.tumblr.com/5c0b9f4e8ac839a628863bb5d7255938/tumblr_inline_p6ve89vOZA1uhchy5_250sq.jpg
        elif temp_list[-1][-2:] == "sq" and crawler.is_integer(temp_list[-1][:-2]):
            image_url = image_url.replace("_250sq", "1280")
            resolution = 1280
        # http://78.media.tumblr.com/tumblr_m9rwkpsRwt1rr15s5.jpg
        # http://78.media.tumblr.com/afd60c3d469055cea4544fe848eeb266/tumblr_inline_n9gff0sXMl1rzbdqg.gif
        # https://78.media.tumblr.com/tumblr_o7ec46zp5M1vpohsl_frame1.jpg
        # https://78.media.tumblr.com/tumblr_odtdlgTAbg1sg1lga_r1_frame1.jpg
        elif (
            len(temp_list) == 2 or
            (len(temp_list) == 3 and temp_list[1] == "inline") or
            (len(temp_list) == 3 and temp_list[2] == "frame1") or
            (len(temp_list) == 4 and temp_list[2] == "r1" and temp_list[3] == "frame1")
        ):
            pass
        else:
            log.error("unknown 1 image url: %s" % image_url)
    # http://78.media.tumblr.com/TVeEqrZktkygbzi2tUbbKMGXo1_1280.jpg
    elif not crawler.is_integer(temp_list[0]) and crawler.is_integer(temp_list[-1]):
        image_id = temp_list[0]
        resolution = int(temp_list[-1])
    #  http://78.media.tumblr.com/_1364612391_cover.jpg
    elif len(temp_list) == 3 and temp_list[0] == "" and crawler.is_integer(temp_list[1]) and temp_list[2] == "cover":
        image_id = temp_list[1]
    # http://78.media.tumblr.com/3562275_500.jpg
    elif len(temp_list) == 2 and crawler.is_integer(temp_list[0]) and crawler.is_integer(temp_list[-1]):
        image_id = temp_list[0]
        resolution = int(temp_list[1])
    # http://78.media.tumblr.com/15427139_r1_500.jpg
    elif len(temp_list) == 3 and crawler.is_integer(temp_list[0]) and crawler.is_integer(temp_list[-1]) and len(temp_list[1]) == 2 and temp_list[1][0] == "r" :
        image_id = temp_list[0]
        resolution = int(temp_list[2])
    else:
        image_id = image_url.split("/")[-1]
        log.error("unknown 2 image url: %s" % image_url)
    if len(image_id) < 15 and not (crawler.is_integer(image_id) and int(image_id) < 2000000000):
        log.error("unknown 3 image url: %s" % image_url)
    return image_id, resolution


# 获取视频播放页面
def get_video_play_page(account_id, post_id, is_https):
    if is_https:
        protocol_type = "https"
    else:
        protocol_type = "http"
    video_play_url = "%s://www.tumblr.com/video/%s/%s/0" % (protocol_type, account_id, post_id)
    video_play_response = net.http_request(video_play_url, method="GET", is_auto_redirect=False)
    result = {
        "video_url": None,  # 视频地址
    }
    if video_play_response.status == 301:
        video_play_url = video_play_response.getheader("Location")
        if video_play_url is not None:
            video_play_response = net.http_request(video_play_url, method="GET")
    if video_play_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(video_play_response.status))
    video_url_find = re.findall('<source src="(http[s]?://' + account_id + '.tumblr.com/video_file/[^"]*)" type="[^"]*"', video_play_response.data)
    if len(video_url_find) == 1:
        if crawler.is_integer(video_url_find[0].split("/")[-1]):
            result["video_url"] = "/".join(video_url_find[0].split("/")[:-1])
        result["video_url"] = video_url_find[0]
    elif len(video_url_find) == 0:
        # 第三方视频
        pass
    else:
        raise crawler.CrawlerException("页面截取视频地址失败\n%s" % video_play_response.data)
    return result


# 日志地址解析日志id
def get_post_id(post_url):
    post_id = tool.find_sub_string(post_url, "/post/").split("/")[0]
    if crawler.is_integer(post_id):
        return post_id
    return None


class Tumblr(crawler.Crawler):
    def __init__(self):
        global COOKIE_INFO
        global USER_AGENT
        global IS_STEP_ERROR_403_AND_404

        sys_config = {
            crawler.SYS_DOWNLOAD_IMAGE: True,
            crawler.SYS_DOWNLOAD_VIDEO: True,
            crawler.SYS_GET_COOKIE: {".tumblr.com": (), "www.tumblr.com": ()},
            crawler.SYS_SET_PROXY: True,
            crawler.SYS_APP_CONFIG: (
                ("USER_AGENT", "", crawler.CONFIG_ANALYSIS_MODE_RAW),
                ("IS_STEP_ERROR_403_AND_404", False, crawler.CONFIG_ANALYSIS_MODE_BOOLEAN)
            ),
        }
        crawler.Crawler.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        COOKIE_INFO = self.cookie_value
        USER_AGENT = self.app_config["USER_AGENT"]
        IS_STEP_ERROR_403_AND_404 = self.app_config["IS_STEP_ERROR_403_AND_404"]

        # 解析存档文件
        # account_id  last_post_id
        self.account_list = crawler.read_save_data(self.save_data_path, 0, ["", "0"])

        # 检测登录状态
        if not check_login():
            while True:
                input_str = output.console_input(crawler.get_time() + " 没有检测到账号登录状态，可能无法解析开启safe mode的账号，继续程序(C)ontinue？或者退出程序(E)xit？:")
                input_str = input_str.lower()
                if input_str in ["e", "exit"]:
                    tool.process_exit()
                elif input_str in ["c", "continue"]:
                    global IS_LOGIN
                    IS_LOGIN = False
                    break

    def main(self):
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
        crawler.rewrite_save_file(self.temp_save_data_path, self.save_data_path)

        log.step("全部下载完毕，耗时%s秒，共计图片%s张，视频%s个" % (self.get_run_time(), self.total_image_count, self.total_video_count))


class Download(crawler.DownloadThread):
    EACH_LOOP_MAX_PAGE_COUNT = 200  # 单词缓存多少页的日志
    is_https = True
    is_safe_mode = False
    is_private = False

    def __init__(self, account_info, main_thread):
        crawler.DownloadThread.__init__(self, account_info, main_thread)
        self.account_id = self.account_info[0]
        log.step(self.account_id + " 开始")

    # 获取所有可下载日志
    def get_crawl_list(self, page_count, unique_list):
        post_info_list = []
        is_over = False
        # 获取全部还未下载过需要解析的日志
        while not is_over:
            self.main_thread_check()  # 检测主线程运行状态
            log.step(self.account_id + " 开始解析第%s页日志" % page_count)

            # 获取一页的日志地址
            try:
                if self.is_private:
                    post_pagination_response = get_one_page_private_blog(self.account_id, page_count)
                else:
                    post_pagination_response = get_one_page_post(self.account_id, page_count, self.is_https, self.is_safe_mode)
            except crawler.CrawlerException, e:
                log.error(self.account_id + " 第%s页日志解析失败，原因：%s" % (page_count, e.message))
                raise

            if not self.is_private and post_pagination_response["is_over"]:
                break

            log.trace(self.account_id + " 第%s页解析的全部日志：%s" % (page_count, post_pagination_response["post_info_list"]))

            # 寻找这一页符合条件的日志
            for post_info in post_pagination_response["post_info_list"]:
                # 获取日志id
                post_id = get_post_id(post_info["post_url"])
                if post_id is None:
                    log.error(self.account_id + " 日志地址%s解析日志id失败" % post_info["post_url"])
                    tool.process_exit()

                # 检查是否达到存档记录
                if int(post_id) > int(self.account_info[1]):
                    # 新增信息页导致的重复判断
                    if post_id in unique_list:
                        continue
                    else:
                        post_info_list.append(post_info)
                        unique_list.append(post_id)
                else:
                    is_over = True
                    break

            if not is_over:
                if post_pagination_response["is_over"]:
                    is_over = True
                else:
                    page_count += 1
        return post_info_list

    # 解析单个日志
    def crawl_post(self, post_info):
        post_id = get_post_id(post_info["post_url"])
        post_url = post_info["post_url"][:post_info["post_url"].find(post_id) + len(post_id)]

        if self.is_private:
            has_video = post_info["has_video"]
            image_url_list = post_info["image_url_list"]
        else:
            # 获取日志
            try:
                post_response = get_post_page(post_info["post_url"], self.is_safe_mode)
            except crawler.CrawlerException, e:
                log.error(self.account_id + " 日志 %s 解析失败，原因：%s" % (post_url, e.message))
                raise
            has_video = post_response["has_video"]
            image_url_list = post_response["image_url_list"]

        # 视频下载
        video_index = 1
        while self.main_thread.is_download_video and has_video:
            if self.is_private:
                video_url = post_info["video_url"]
            else:
                self.main_thread_check()  # 检测主线程运行状态
                try:
                    video_play_response = get_video_play_page(self.account_id, post_id, self.is_https)
                except crawler.CrawlerException, e:
                    log.error(self.account_id + " 日志 %s 视频解析失败，原因：%s" % (post_url, e.message))
                    raise
                video_url = video_play_response["video_url"]

            # 第三方视频，跳过
            if video_url is None:
                log.error(self.account_id + " 日志 %s 存在第三方视频，跳过" % post_url)
                break

            self.main_thread_check()  # 检测主线程运行状态
            log.step(self.account_id + " 日志 %s 开始下载视频 %s" % (post_id, video_url))

            video_file_path = os.path.join(self.main_thread.video_download_path, self.account_id, "%012d.mp4" % int(post_id))
            save_file_return = net.save_net_file(video_url, video_file_path)
            if save_file_return["status"] == 1:
                # 设置临时目录
                self.temp_path_list.append(video_file_path)
                log.step(self.account_id + " 日志 %s 视频下载成功" % post_id)
            else:
                if save_file_return["code"] == 403 and video_url.find("_r1_720") != -1:
                    video_url = video_url.replace("_r1_720", "_r1")
                    save_file_return = net.save_net_file(video_url, video_file_path)
                    if save_file_return["status"] == 1:
                        # 设置临时目录
                        self.temp_path_list.append(video_file_path)
                        log.step(self.account_id + " 日志 %s 视频下载成功" % post_id)
                        break
                error_message = self.account_id + " 日志 %s 视频 %s 下载失败，原因：%s" % (post_url, video_url, crawler.download_failre(save_file_return["code"]))
                # 403、404错误作为step log输出
                if IS_STEP_ERROR_403_AND_404 and save_file_return["code"] in [403, 404]:
                    log.step(error_message)
                else:
                    log.error(error_message)
            break

        # 图片下载
        image_index = 1
        if self.main_thread.is_download_image and len(image_url_list) > 0:
            log.trace(self.account_id + " 日志 %s 解析的的全部图片：%s" % (post_id, image_url_list))

            for image_url in image_url_list:
                self.main_thread_check()  # 检测主线程运行状态
                log.step(self.account_id + " 日志 %s 开始下载第%s张图片 %s" % (post_id, image_index, image_url))

                file_type = image_url.split("?")[0].split(".")[-1]
                image_file_path = os.path.join(self.main_thread.image_download_path, self.account_id, "%012d_%02d.%s" % (int(post_id), image_index, file_type))
                save_file_return = net.save_net_file(image_url, image_file_path)
                if save_file_return["status"] == 1:
                    # 设置临时目录
                    self.temp_path_list.append(image_file_path)
                    log.step(self.account_id + " 日志 %s 第%s张图片下载成功" % (post_id, image_index))
                    image_index += 1
                else:
                    error_message = self.account_id + " 日志 %s 第%s张图片 %s 下载失败，原因：%s" % (post_url, image_index, image_url, crawler.download_failre(save_file_return["code"]))
                    # 403、404错误作为step log输出
                    if IS_STEP_ERROR_403_AND_404 and save_file_return["code"] in [403, 404]:
                        log.step(error_message)
                    else:
                        image_index += 1
                        log.error(error_message)

        # 日志内图片和视频全部下载完毕
        self.temp_path_list = []  # 临时目录设置清除
        self.total_image_count += image_index - 1  # 计数累加
        self.total_video_count += video_index - 1  # 计数累加
        self.account_info[1] = post_id

    def run(self):
        try:
            try:
                self.is_https, self.is_safe_mode, self.is_private = get_index_setting(self.account_id)
            except crawler.CrawlerException, e:
                log.error(self.account_id + " 账号设置解析失败，原因：%s" % e.message)
                raise

            # 未登录&开启safe mode直接退出
            if not IS_LOGIN and self.is_safe_mode:
                log.error(self.account_id + " 账号开启了safe mode并且未检测到登录状态")
                tool.process_exit()

            start_page_count = 1
            while self.EACH_LOOP_MAX_PAGE_COUNT > 0:
                self.main_thread_check()  # 检测主线程运行状态
                start_page_count += self.EACH_LOOP_MAX_PAGE_COUNT
                try:
                    if self.is_private:
                        post_pagination_response = get_one_page_private_blog(self.account_id, start_page_count)
                    else:
                        post_pagination_response = get_one_page_post(self.account_id, start_page_count, self.is_https, self.is_safe_mode)
                except crawler.CrawlerException, e:
                    log.error(self.account_id + " 第%s页日志解析失败，原因：%s" % (start_page_count, e.message))
                    raise

                # 这页没有任何内容，返回上一个检查节点
                if post_pagination_response["is_over"]:
                    start_page_count -= self.EACH_LOOP_MAX_PAGE_COUNT
                    break

                post_id = get_post_id(post_pagination_response["post_info_list"][-1]["post_url"])
                # 这页已经匹配到存档点，返回上一个节点
                if int(post_id) < int(self.account_info[1]):
                    start_page_count -= self.EACH_LOOP_MAX_PAGE_COUNT
                    break

                log.step(self.account_id + " 前%s页没有符合条件的日志，跳过%s页后继续查询" % (start_page_count, self.EACH_LOOP_MAX_PAGE_COUNT))

            unique_list = []
            while True:
                # 获取所有可下载日志
                post_info_list = self.get_crawl_list(start_page_count, unique_list)
                log.step(self.account_id + " 需要下载的全部日志解析完毕，共%s个" % len(post_info_list))

                # 从最早的日志开始下载
                while len(post_info_list) > 0:
                    post_info = post_info_list.pop()
                    log.step(self.account_id + " 开始解析日志 %s" % post_info["post_url"])
                    self.crawl_post(post_info)
                    self.main_thread_check()  # 检测主线程运行状态

                if start_page_count == 1:
                    break
                else:
                    start_page_count -= self.EACH_LOOP_MAX_PAGE_COUNT
        except SystemExit, se:
            if se.code == 0:
                log.step(self.account_id + " 提前退出")
            else:
                log.error(self.account_id + " 异常退出")
            # 如果临时目录变量不为空，表示某个日志正在下载中，需要把下载了部分的内容给清理掉
            self.clean_temp_path()
        except Exception, e:
            log.error(self.account_id + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 保存最后的信息
        with self.thread_lock:
            tool.write_file("\t".join(self.account_info), self.main_thread.temp_save_data_path)
            self.main_thread.total_image_count += self.total_image_count
            self.main_thread.total_video_count += self.total_video_count
            self.main_thread.account_list.pop(self.account_id)
        log.step(self.account_id + " 下载完毕，总共获得%s张图片和%s个视频" % (self.total_image_count, self.total_video_count))
        self.notify_main_thread()


if __name__ == "__main__":
    Tumblr().main()
