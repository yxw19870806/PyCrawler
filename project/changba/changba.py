# -*- coding:UTF-8  -*-
"""
唱吧歌曲爬虫
http://changba.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import base64
import os
import re
import threading
import time
import traceback
from common import *


# 获取账号首页页面
def get_account_index_page(account_id):
    account_index_url = "http://changba.com/u/%s" % account_id
    account_index_response = net.http_request(account_index_url, method="GET", is_auto_redirect=False)
    result = {
        "user_id": None,  # user id
    }
    if account_index_response.status == 302 and account_index_response.getheader("Location") == "http://changba.com":
        raise crawler.CrawlerException("账号不存在")
    elif account_index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(account_index_response.status))
    # 获取user id
    user_id = tool.find_sub_string(account_index_response.data, "var userid = '", "'")
    if not crawler.is_integer(user_id):
        raise crawler.CrawlerException("页面截取userid失败\n%s" % account_index_response.data)
    result["user_id"] = str(user_id)
    return result


# 获取指定页数的全部歌曲信息
# user_id -> 4306405
def get_one_page_audio(user_id, page_count):
    # http://changba.com/member/personcenter/loadmore.php?userid=4306405&pageNum=1
    audit_pagination_url = "http://changba.com/member/personcenter/loadmore.php"
    query_data = {
        "userid": user_id,
        "pageNum": page_count - 1,
    }
    audit_pagination_response = net.http_request(audit_pagination_url, method="GET", fields=query_data, json_decode=True)
    result = {
        "audio_info_list": [],  # 全部歌曲信息
    }
    if audit_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(audit_pagination_response.status))
    for audio_info in audit_pagination_response.json_data:
        result_audio_info = {
            "audio_id": None,  # 歌曲id
            "audio_key": None,  # 歌曲唯一key
            "audio_title": "",  # 歌曲标题
            "audio_type": None,  # 歌曲类型，2 MV，1/3 歌曲
        }
        # 获取歌曲id
        if not crawler.check_sub_key(("workid",), audio_info):
            raise crawler.CrawlerException("歌曲信息'workid'字段不存在\n%s" % audio_info)
        if not crawler.is_integer(audio_info["workid"]):
            raise crawler.CrawlerException("歌曲信息'workid'字段类型不正确\n%s" % audio_info)
        result_audio_info["audio_id"] = str(audio_info["workid"])
        # 获取歌曲标题
        if not crawler.check_sub_key(("songname",), audio_info):
            raise crawler.CrawlerException("歌曲信息'songname'字段不存在\n%s" % audio_info)
        result_audio_info["audio_title"] = str(audio_info["songname"].encode("UTF-8"))
        # 获取歌曲key
        if not crawler.check_sub_key(("enworkid",), audio_info):
            raise crawler.CrawlerException("歌曲信息'enworkid'字段不存在\n%s" % audio_info)
        result_audio_info["audio_key"] = str(audio_info["enworkid"])
        # 获取歌曲类型
        if not crawler.check_sub_key(("type",), audio_info):
            raise crawler.CrawlerException("歌曲信息'type'字段不存在\n%s" % audio_info)
        if not crawler.is_integer(audio_info["type"]):
            raise crawler.CrawlerException("歌曲信息'type'字段类型不正确\n%s" % audio_info)
        if int(audio_info["type"]) not in (1, 2, 3):
            raise crawler.CrawlerException("歌曲信息'type'字段取值不正确\n%s" % audio_info)
        result_audio_info["audio_type"] = int(audio_info["type"])
        result["audio_info_list"].append(result_audio_info)
    return result


# 获取指定id的歌曲播放页
# audio_en_word_id => w-ptydrV23KVyIPbWPoKsA
def get_audio_play_page(audio_en_word_id, audio_type):
    audio_play_url = "http://changba.com/s/%s" % audio_en_word_id
    result = {
        "audio_url": None,  # 歌曲地址
        "is_delete": False,  # 是不是已经被删除
    }
    audio_play_response = net.http_request(audio_play_url, method="GET")
    if audio_play_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(audio_play_response.status))
    if audio_play_response.data.find("该作品可能含有不恰当内容将不能显示。") > -1:
        result["is_delete"] = True
    else:
        # 获取歌曲地址
        if audio_type == 1 or audio_type == 3:
            audio_source_url = tool.find_sub_string(audio_play_response.data, 'var a="', '"')
            if not audio_source_url:
                raise crawler.CrawlerException("页面截取歌曲原始地址失败\n%s" % audio_play_response.data)
            # 从JS处解析的规则
            special_find = re.findall("userwork/([abc])(\d+)/(\w+)/(\w+)\.mp3", audio_source_url)
            if len(special_find) == 0:
                result["audio_url"] = str(audio_source_url)
            elif len(special_find) == 1:
                e = int(special_find[0][1], 8)
                f = int(special_find[0][2], 16) / e / e
                g = int(special_find[0][3], 16) / e / e
                if "a" == special_find[0][0] and g % 1000 == f:
                    result["audio_url"] = "http://a%smp3.changba.com/userdata/userwork/%s/%g.mp3" % (e, f, g)
                else:
                    result["audio_url"] = "http://aliuwmp3.changba.com/userdata/userwork/%s.mp3" % g
            else:
                raise crawler.CrawlerException("歌曲原始地址解密歌曲地址失败\n%s" % audio_source_url)
        # MV
        else:
            video_source_string = tool.find_sub_string(audio_play_response.data, "<script>jwplayer.utils.qn = '", "';</script>")
            if not video_source_string:
                # 是不是使用bokecc cdn的视频
                bokecc_param = tool.find_sub_string(audio_play_response.data, '<script src="//p.bokecc.com/player?', '"')
                if not bokecc_param:
                    raise crawler.CrawlerException("页面截取歌曲加密地址失败\n%s" % audio_play_response.data)
                vid = tool.find_sub_string(bokecc_param, "vid=", "&")
                if not vid:
                    raise crawler.CrawlerException("bokecc参数截取vid失败\n%s" % bokecc_param)
                bokecc_xml_url = "https://p.bokecc.com/servlet/playinfo"
                query_data = {
                    "vid": vid,
                    "m": 1,
                    "fv": "WIN",
                    "rnd": str(int(time.time()))[-4:],
                }
                bokecc_xml_response = net.http_request(bokecc_xml_url, method="GET", fields=query_data)
                if bokecc_xml_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                    raise crawler.CrawlerException("bokecc xml文件 %s 访问失败" % bokecc_xml_url)
                audio_url_find = re.findall('playurl="([^"]*)"', bokecc_xml_response.data)
                if len(audio_url_find) == 0:
                    raise crawler.CrawlerException("bokecc xml文件 %s 截取歌曲地址失败\n%s" % (bokecc_xml_url, bokecc_xml_response.data))
                video_url = audio_url_find[-1].replace("&amp;", "&")
            else:
                try:
                    video_url = base64.b64decode(video_source_string)
                except TypeError:
                    raise crawler.CrawlerException("歌曲加密地址解密失败\n%s" % video_source_string)
            result["audio_url"] = video_url
    return result


class ChangBa(crawler.Crawler):
    def __init__(self):
        sys_config = {
            crawler.SYS_DOWNLOAD_VIDEO: True,
        }
        crawler.Crawler.__init__(self, sys_config)

        # 解析存档文件
        # account_id  last_audio_id
        self.account_list = crawler.read_save_data(self.save_data_path, 0, ["", "0"])

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

        log.step("全部下载完毕，耗时%s秒，共计歌曲%s首" % (self.get_run_time(), self.total_video_count))


class Download(crawler.DownloadThread):
    AUDIO_COUNT_PER_PAGE = 20  # 每页歌曲数量上限

    def __init__(self, account_info, main_thread):
        crawler.DownloadThread.__init__(self, account_info, main_thread)
        self.account_id = self.account_info[0]
        if len(self.account_info) >= 3 and self.account_info[2]:
            self.account_name = self.account_info[2]
        else:
            self.account_name = self.account_info[0]
        log.step(self.account_name + " 开始")

    # 获取所有可下载歌曲
    def get_crawl_list(self, user_id):
        page_count = 1
        unique_list = []
        audio_info_list = []
        is_over = False
        # 获取全部还未下载过需要解析的歌曲
        while not is_over:
            self.main_thread_check()  # 检测主线程运行状态
            log.step(self.account_name + " 开始解析第%s页歌曲" % page_count)

            # 获取一页歌曲
            try:
                audit_pagination_response = get_one_page_audio(user_id, page_count)
            except crawler.CrawlerException, e:
                log.error(self.account_name + " 第%s页歌曲解析失败，原因：%s" % (page_count, e.message))
                raise

            # 如果为空，表示已经取完了
            if len(audit_pagination_response["audio_info_list"]) == 0:
                break

            log.trace(self.account_name + " 第%s页解析的全部歌曲：%s" % (page_count, audit_pagination_response["audio_info_list"]))

            # 寻找这一页符合条件的歌曲
            for audio_info in audit_pagination_response["audio_info_list"]:
                # 检查是否达到存档记录
                if int(audio_info["audio_id"]) > int(self.account_info[1]):
                    # 新增歌曲导致的重复判断
                    if audio_info["audio_id"] in unique_list:
                        continue
                    else:
                        audio_info_list.append(audio_info)
                        unique_list.append(audio_info["audio_id"])
                else:
                    is_over = True
                    break

            if not is_over:
                # 获取的歌曲数量少于1页的上限，表示已经到结束了
                # 如果歌曲数量正好是页数上限的倍数，则由下一页获取是否为空判断
                if len(audit_pagination_response["audio_info_list"]) < self.AUDIO_COUNT_PER_PAGE:
                    is_over = True
                else:
                    page_count += 1

        return audio_info_list

    # 解析单首歌曲
    def crawl_audio(self, audio_info):
        self.main_thread_check()  # 检测主线程运行状态
        # 获取歌曲播放页
        try:
            audio_play_response = get_audio_play_page(audio_info["audio_key"], audio_info["audio_type"])
        except crawler.CrawlerException, e:
            log.error(self.account_name + " 歌曲%s《%s》解析失败，原因：%s" % (audio_info["audio_key"], audio_info["audio_title"], e.message))
            raise

        if audio_play_response["is_delete"]:
            log.error(self.account_name + " 歌曲%s《%s》异常，跳过" % (audio_info["audio_key"], audio_info["audio_title"]))
            return

        self.main_thread_check()  # 检测主线程运行状态
        log.step(self.account_name + " 开始下载歌曲%s《%s》 %s" % (audio_info["audio_key"], audio_info["audio_title"], audio_play_response["audio_url"]))

        file_path = os.path.join(self.main_thread.video_download_path, self.account_name, "%010d - %s.mp3" % (int(audio_info["audio_id"]), path.filter_text(audio_info["audio_title"])))
        save_file_return = net.save_net_file(audio_play_response["audio_url"], file_path)
        if save_file_return["status"] == 1:
            log.step(self.account_name + " 歌曲%s《%s》下载成功" % (audio_info["audio_key"], audio_info["audio_title"]))
        else:
            log.error(self.account_name + " 歌曲%s《%s》 %s 下载失败，原因：%s" % (audio_info["audio_key"], audio_info["audio_title"], audio_play_response["audio_url"], crawler.download_failre(save_file_return["code"])))
            return

        # 歌曲下载完毕
        if save_file_return["status"] == 1:
            self.total_video_count += 1  # 计数累加
        self.account_info[1] = audio_info["audio_id"]  # 设置存档

    def run(self):
        try:
            # 查找账号user id
            try:
                account_index_response = get_account_index_page(self.account_id)
            except crawler.CrawlerException, e:
                log.error(self.account_name + " 主页解析失败，原因：%s" % e.message)
                raise

            # 获取所有可下载歌曲
            audio_info_list = self.get_crawl_list(account_index_response["user_id"])
            log.step(self.account_name + " 需要下载的全部歌曲解析完毕，共%s首" % len(audio_info_list))

            # 从最早的歌曲开始下载
            while len(audio_info_list) > 0:
                audio_info = audio_info_list.pop()
                log.step(self.account_name + " 开始解析歌曲%s《%s》" % (audio_info["audio_key"], audio_info["audio_title"]))
                self.crawl_audio(audio_info)
                self.main_thread_check()  # 检测主线程运行状态
        except SystemExit, se:
            if se.code == 0:
                log.step(self.account_name + " 提前退出")
            else:
                log.error(self.account_name + " 异常退出")
        except Exception, e:
            log.error(self.account_name + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 保存最后的信息
        with self.thread_lock:
            tool.write_file("\t".join(self.account_info), self.main_thread.temp_save_data_path)
            self.main_thread.total_video_count += self.total_video_count
            self.main_thread.account_list.pop(self.account_id)
        log.step(self.account_name + " 下载完毕，总共获得%s首歌曲" % self.total_video_count)
        self.notify_main_thread()


if __name__ == "__main__":
    ChangBa().main()
