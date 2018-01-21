# -*- coding:UTF-8  -*-
"""
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import os
import re
import time
import threading


def get_archive_page(archive_id):
    archive_url = "http://www.ivseek.com/archives/%s.html" % archive_id
    archive_response = net.http_request(archive_url, method="GET")
    result = {
        "account_id": "",  # 视频发布账号（youtube）
        "title": "",  # 标题
        "video_url": None,  # 视频地址（youtube）
    }
    if archive_response.status == 404:
        return result
    elif archive_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(archive_response.status))
    # 没有内嵌视频
    if archive_response.data.find("<iframe") == -1:
        return result
    # 获取标题
    title = tool.find_sub_string(archive_response.data, '<meta property="og:title" content="', '"')
    if not title:
        raise crawler.CrawlerException("标题截取失败")
    result["title"] = str(title).strip()
    # 获取视频地址
    video_url_find = re.findall('<iframe[\s|\S]*?src="([^"]*)"', archive_response.data)
    if len(video_url_find) == 0:
        raise crawler.CrawlerException("视频地址匹配失败")
    elif len(video_url_find) != 1:
        log.error("多个内嵌iframe" + str(video_url_find))
    video_url = str(video_url_find[0])
    # 'http://embed.share-videos.se/auto/embed/40537536?uid=6050'
    if video_url.find("//embed.share-videos.se/") >= 0:
        video_id = video_url.split("/")[-1]
        result["video_url"] = "http://share-videos.se/auto/video/%s" % video_id
    # https://www.youtube.com/embed/9GSEOmLD_zc?feature=oembed
    elif video_url.find("//www.youtube.com/") >= 0:
        video_id = video_url.split("/")[-1].split("?")[0]
        result["video_url"] = "https://www.youtube.com/watch?v=%s" % video_id
        # 获取视频发布账号
        header_list = {
            "cookie": "YSC=5qtzcCE2QUY; VISITOR_INFO1_LIVE=zldN2C7424k; PREF=f1=50000000&f5=30000",
            "x-client-data": "CJK2yQEIpLbJAQjEtskBCPqcygEIqZ3KAQioo8oB",
            "accept-language": "zh-CN,zh;q=0.9",
        }
        video_play_response = net.http_request(result["video_url"], method="GET", header_list=header_list)
        if video_play_response.status != net.HTTP_RETURN_CODE_SUCCEED:
            raise crawler.CrawlerException("视频播放页面%s %s" % (result["video_url"], crawler.request_failre(archive_response.status)))
        account_id = tool.find_sub_string(video_play_response.data, '"webNavigationEndpointData":{"url":"/channel/', '"')
        if not account_id:
            raise crawler.CrawlerException("视频发布账号截取失败")
        result["account_id"] = str(account_id)
    else:
        raise crawler.CrawlerException("未知视频来源" + video_url)
    return result


class IvSeek(crawler.Crawler):
    def __init__(self):
        sys_config = {
            crawler.SYS_NOT_CHECK_SAVE_DATA: True,
            crawler.SYS_NOT_DOWNLAOD: True,
            crawler.SYS_SET_PROXY: True,
        }
        crawler.Crawler.__init__(self, sys_config)

    def main(self):
        save_id = 1
        save_info_list = tool.read_file(self.save_data_path, tool.READ_FILE_TYPE_LINE)
        if len(save_info_list) > 0:
            save_id = int(save_info_list[-1].split("\t")[0]) + 1

        for archive_id in range(save_id, 3000):
            log.step("开始解析第%s页视频" % archive_id)

            # 获取一页图片
            try:
                archive_response = get_archive_page(archive_id)
            except crawler.CrawlerException, e:
                log.error("第%s页视频解析失败，原因：%s" % (archive_id, e.message))
                archive_id += 1
                continue

            if archive_response["video_url"] is None:
                continue

            tool.write_file("%s\t%s\t%s\t%s" % (archive_id, archive_response["title"], archive_response["video_url"], archive_response["account_id"]), self.save_data_path)

            # 提前结束
            if not self.is_running():
                break


if __name__ == "__main__":
    IvSeek().main()
