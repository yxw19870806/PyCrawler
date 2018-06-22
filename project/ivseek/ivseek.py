# -*- coding:UTF-8  -*-
"""
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import re
import traceback
from common import *


# 获取首页
def get_index_page():
    index_url = "http://www.ivseek.com/"
    index_response = net.http_request(index_url, method="GET")
    result = {
        "max_archive_id": None,  # 最新图集id
    }
    if index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(index_response.status))
    archive_id_find = re.findall('<a class="no-deco" href="http://www.ivseek.com/archives/(\d*).html">', index_response.data)
    if len(archive_id_find) == 0:
        raise crawler.CrawlerException("页面匹配视频id失败\n%s" % index_response.data)
    result["max_archive_id"] = max(map(int, archive_id_find))
    return result


def get_archive_page(archive_id):
    archive_url = "http://www.ivseek.com/archives/%s.html" % archive_id
    archive_response = net.http_request(archive_url, method="GET")
    result = {
        "title": "",  # 标题
        "video_info_list": [],  # 全部视频信息
    }
    if archive_response.status == 404:
        return result
    elif archive_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(archive_response.status))
    # 获取视频地址
    video_url_find1 = re.findall('<iframe[\s|\S]*?src="([^"]*)"', archive_response.data)
    video_url_find2 = re.findall('<script type="\w*/javascript" src="(http[s]?://\w*.nicovideo.jp/[^"]*)"></script>', archive_response.data)
    video_url_find = video_url_find1 + video_url_find2
    if len(video_url_find) == 0:
        return result
    for video_url in video_url_find:
        result_video_info = {
            "account_id": "",  # 视频发布账号（youtube）
            "video_url": None,  # 视频信息
        }
        # 'http://embed.share-videos.se/auto/embed/40537536?uid=6050'
        if video_url.find("//embed.share-videos.se/") >= 0:
            video_id = video_url.split("/")[-1]
            result_video_info["video_url"] = "http://share-videos.se/auto/video/%s" % video_id
        # https://www.youtube.com/embed/9GSEOmLD_zc?feature=oembed
        elif video_url.find("//www.youtube.com/") >= 0:
            video_id = video_url.split("/")[-1].split("?")[0]
            result_video_info["video_url"] = "https://www.youtube.com/watch?v=%s" % video_id
            # 获取视频发布账号
            video_play_response = net.http_request(result_video_info["video_url"], method="GET", header_list={"accept-language": "en-US"})
            if video_play_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                raise crawler.CrawlerException("视频播放页%s，%s" % (result["video_url"], crawler.request_failre(archive_response.status)))
            # 账号已被删除，跳过
            if video_play_response.data.find('"reason":"This video is no longer available because the YouTube account associated with this video has been terminated."') >= 0:
                continue
            account_id = tool.find_sub_string(video_play_response.data, '"webNavigationEndpointData":{"url":"/channel/', '"')
            if not account_id:
                account_id = tool.find_sub_string(video_play_response.data, '{"webCommandMetadata":{"url":"/channel/', '"')
            if not account_id:
                account_id = tool.find_sub_string(video_play_response.data, '<meta itemprop="channelId" content="', '">')
            if account_id:
                result_video_info["account_id"] = str(account_id)
            else:
                log.error("视频 %s 发布账号截取失败\n%s" % (result_video_info["video_url"], video_play_response.data))
        elif video_url.find(".nicovideo.jp/") >= 0:
            # https://embed.nicovideo.jp/watch/sm23008734/script?w=640&#038;h=360
            if video_url.find("embed.nicovideo.jp/watch") >= 0:
                video_id = video_url.split("/")[-2]
            # http://ext.nicovideo.jp/thumb_watch/sm21088018?w=490&#038;h=307
            elif video_url.find("ext.nicovideo.jp/thumb_watch/") >= 0:
                video_id = video_url.split("/")[-1].split("?")[0]
            else:
                raise crawler.CrawlerException("未知视频来源" + video_url)
            result_video_info["video_url"] = "http://www.nicovideo.jp/watch/%s" % video_id
            # 获取视频发布账号
            video_play_response = net.http_request(result_video_info["video_url"], method="GET", header_list={"accept-language": "en-US"})
            if video_play_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                raise crawler.CrawlerException("视频播放页%s，%s" % (result["video_url"], crawler.request_failre(video_play_response.status)))
            account_id = tool.find_sub_string(video_play_response.data, '<a href="/user/', '"')
            if crawler.is_integer(account_id):
                result_video_info["account_id"] = str(account_id)
        # http://www.dailymotion.com/embed/video/x5oi0x
        elif video_url.find("//www.dailymotion.com/") >= 0:
            video_id = video_url.split("/")[-1][0]
            result_video_info["video_url"] = "http://www.dailymotion.com/video/%s" % video_id
            # 获取视频发布账号
            video_play_response = net.http_request(result_video_info["video_url"], method="GET")
            if video_play_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                raise crawler.CrawlerException("视频播放页%s，%s" % (result_video_info["video_url"], crawler.request_failre(video_play_response.status)))
            account_id = tool.find_sub_string(video_play_response.data, '"screenname":"', '"')
            if account_id:
                result_video_info["account_id"] = str(account_id)
        # 无效的视频地址
        elif video_url.find("//rcm-fe.amazon-adsystem.com") >= 0:
            continue
        else:
            result_video_info["video_url"] = video_url
            log.error("未知视频来源" + video_url)
        result["video_info_list"].append(result_video_info)
    # 获取标题
    title = tool.find_sub_string(archive_response.data, '<meta property="og:title" content="', '"')
    if not title:
        raise crawler.CrawlerException("标题截取失败")
    result["title"] = str(title).strip()
    return result


class IvSeek(crawler.Crawler):
    def __init__(self):
        sys_config = {
            crawler.SYS_NOT_CHECK_SAVE_DATA: True,
            crawler.SYS_NOT_DOWNLOAD: True,
            crawler.SYS_SET_PROXY: True,
        }
        crawler.Crawler.__init__(self, sys_config)

    def main(self):
        save_id = 1
        save_info_list = tool.read_file(self.save_data_path, tool.READ_FILE_TYPE_LINE)
        if len(save_info_list) > 0:
            save_id = int(save_info_list[-1].split("\t")[0]) + 1

        try:
            # 获取首页
            try:
                index_response = get_index_page()
            except crawler.CrawlerException, e:
                log.error("首页解析失败，原因：%s" % e.message)
                raise

            log.step("最新视频id：%s" % index_response["max_archive_id"])

            for archive_id in range(save_id, index_response["max_archive_id"]):
                if not self.is_running():
                    tool.process_exit(0)
                log.step("开始解析第%s个视频" % archive_id)

                # 获取一页图片
                try:
                    archive_response = get_archive_page(archive_id)
                except crawler.CrawlerException, e:
                    log.error("第%s个视频解析失败，原因：%s" % (archive_id, e.message))
                    archive_id += 1
                    continue

                if len(archive_response["video_info_list"]) == 0:
                    continue

                for video_info in archive_response["video_info_list"]:
                    log.step("视频%s 《%s》: %s" % (archive_id, archive_response["title"], video_info["video_url"]))
                    tool.write_file("%s\t%s\t%s\t%s" % (archive_id, archive_response["title"], video_info["video_url"], video_info["account_id"]), self.save_data_path)

                # 提前结束
                if not self.is_running():
                    break
        except SystemExit, se:
            if se.code == 0:
                log.step("提前退出")
            else:
                log.error("异常退出")
        except Exception, e:
            log.error("未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))


if __name__ == "__main__":
    IvSeek().main()
