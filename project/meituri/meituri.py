# -*- coding:UTF-8  -*-
"""
美图日图片爬虫
https://www.meituri.com
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import os
import re
import traceback


# 获取指定一页的图集
def get_one_page_album(album_id):
    page_count = max_page_count = 1
    result = {
        "album_title": "",  # 图集标题
        "image_url_list": [],  # 全部图片地址
        "is_delete": False,  # 是不是已经被删除
    }
    while page_count <= max_page_count:
        if page_count == 1:
            album_pagination_url = "http://www.meituri.com/a/%s/" % album_id
        else:
            album_pagination_url = "http://www.meituri.com/a/%s/%s.html" % (album_id, page_count)
        album_pagination_response = net.http_request(album_pagination_url, method="GET")
        if page_count == 1 and album_pagination_response.status in [403, 404]:
            result["is_delete"] = True
            return result
        elif album_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
            raise crawler.CrawlerException("第%s页 " % page_count + crawler.request_failre(album_pagination_response.status))
        if page_count == 1:
            # 获取图集标题
            album_title = tool.find_sub_string(album_pagination_response.data, "<h1>", "</h1>")
            if not album_title:
                raise crawler.CrawlerException("标题截取失败\n%s" % album_pagination_response.data)
            result["album_title"] = album_title.strip()
        # 获取图集图片地址
        image_list_html = tool.find_sub_string(album_pagination_response.data, '<div class="content">', "</div>")
        if not image_list_html:
            raise crawler.CrawlerException("第%s页 页面截取图片列表失败\n%s" % (page_count, album_pagination_response.data))
        image_url_list = re.findall('<img src="([^"]*)"', image_list_html)
        if len(image_url_list) == 0:
            if image_list_html.strip() != "<center></center>":
                raise crawler.CrawlerException("第%s页 图片列表匹配图片地址失败\n%s" % (page_count, album_pagination_response.data))
        else:
            result["image_url_list"] += map(str, image_url_list)
        # 判断是不是最后一页
        page_count_find = re.findall('">(\d*)</a>', tool.find_sub_string(album_pagination_response.data, '<div id="pages">', "</div>"))
        if len(page_count_find) > 0:
            max_page_count = max(map(int, page_count_find))
        else:
            max_page_count = 1
        page_count += 1
    return result


# 对一些异常的图片地址做过滤
def get_image_url(image_url):
    return image_url.replace("/[page]", "/")


class MeiTuRi(crawler.Crawler):
    def __init__(self):
        sys_config = {
            crawler.SYS_DOWNLOAD_IMAGE: True,
            crawler.SYS_NOT_CHECK_SAVE_DATA: True,
        }
        crawler.Crawler.__init__(self, sys_config)

    def main(self):
        # 解析存档文件，获取上一次的album id
        album_id = 1
        if os.path.exists(self.save_data_path):
            file_save_info = tool.read_file(self.save_data_path)
            if not crawler.is_integer(file_save_info):
                log.error("存档内数据格式不正确")
                tool.process_exit()
            album_id = int(file_save_info)
        temp_path = ""

        try:
            while True:
                if not self.is_running():
                    tool.process_exit(0)
                log.step("开始解析图集%s" % album_id)

                # 获取相册
                try:
                    album_pagination_response = get_one_page_album(album_id)
                except crawler.CrawlerException, e:
                    log.error("图集%s解析失败，原因：%s" % (album_id, e.message))
                    raise

                if album_pagination_response["is_delete"]:
                    log.step("图集%s不存在，跳过" % album_id)
                    album_id += 1
                    continue

                log.trace("图集%s解析的全部图片：%s" % (album_id, album_pagination_response["image_url_list"]))

                image_index = 1
                # 过滤标题中不支持的字符
                album_title = path.filter_text(album_pagination_response["album_title"])
                if album_title:
                    album_path = os.path.join(self.image_download_path, "%05d %s" % (album_id, album_title))
                else:
                    album_path = os.path.join(self.image_download_path, "%05d" % album_id)
                temp_path = album_path
                for image_url in album_pagination_response["image_url_list"]:
                    if not self.is_running():
                        tool.process_exit(0)
                    image_url = get_image_url(image_url)
                    log.step("图集%s 《%s》 开始下载第%s张图片 %s" % (album_id, album_title, image_index, image_url))

                    file_type = image_url.split(".")[-1]
                    file_path = os.path.join(album_path, "%03d.%s" % (image_index, file_type))
                    save_file_return = net.save_net_file(image_url, file_path, header_list={"Referer": "http://www.meituri.com/"})
                    if save_file_return["status"] == 1:
                        log.step("图集%s 《%s》 第%s张图片下载成功" % (album_id, album_title, image_index))
                    else:
                        log.error("图集%s 《%s》 第%s张图片 %s 下载失败，原因：%s" % (album_id, album_title, image_index, image_url, crawler.download_failre(save_file_return["code"])))
                    image_index += 1
                # 图集内图片全部下载完毕
                temp_path = ""  # 临时目录设置清除
                self.total_image_count += image_index - 1  # 计数累加
                album_id += 1  # 设置存档记录
        except SystemExit, se:
            if se.code == 0:
                log.step("提前退出")
            else:
                log.error("异常退出")
            # 如果临时目录变量不为空，表示某个图集正在下载中，需要把下载了部分的内容给清理掉
            if temp_path:
                path.delete_dir_or_file(temp_path)
        except Exception, e:
            log.error("未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 重新保存存档文件
        tool.write_file(str(album_id), self.save_data_path, tool.WRITE_FILE_TYPE_REPLACE)
        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), self.total_image_count))


if __name__ == "__main__":
    MeiTuRi().main()
