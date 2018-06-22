# -*- coding:UTF-8  -*-
"""
CNU图片爬虫
http://www.cnu.cc/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import os
import traceback
from common import *


# 获取作品页面
def get_album_page(album_id):
    album_url = "http://www.cnu.cc/works/%s" % album_id
    album_response = net.http_request(album_url, method="GET")
    result = {
        "album_title": "",  # 作品标题
        "image_url_list": [],  # 全部图片地址
        "is_delete": False,  # 是不是作品已被删除
    }
    if album_response.status == 404:
        result["is_delete"] = True
    elif album_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(album_response.status))
    # 获取作品标题
    album_title = tool.find_sub_string(album_response.data, '<h2 class="work-title">', "</h2>")
    if not album_title:
        raise crawler.CrawlerException("页面截取作品标题失败\n%s" % album_response.data)
    result["album_title"] = album_title
    # 获取图片地址
    image_info_html = tool.find_sub_string(album_response.data, '<div id="imgs_json" style="display:none">', "</div>")
    if not image_info_html:
        raise crawler.CrawlerException("页面截取图片列表失败\n%s" % album_response.data)
    image_info_data = tool.json_decode(image_info_html)
    if image_info_data is None:
        raise crawler.CrawlerException("图片列表加载失败\n%s" % image_info_html)
    image_url_list = []
    for image_info in image_info_data:
        if not crawler.check_sub_key(("img",), image_info):
            raise crawler.CrawlerException("图片信息'img'字段不存在\n%s" % image_info)
        image_url_list.append("http://img.cnu.cc/uploads/images/920/" + str(image_info["img"]))
    result["image_url_list"] = image_url_list
    return result


class CNU(crawler.Crawler):
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
            # http://www.cnu.cc/about/ 全部作品
            # todo 获取最新的作品id
            while True:
                if not self.is_running():
                    tool.process_exit(0)
                log.step("开始解析第%s页作品" % album_id)

                # 获取相册
                try:
                    album_response = get_album_page(album_id)
                except crawler.CrawlerException, e:
                    log.error("第%s页作品解析失败，原因：%s" % (album_id, e.message))
                    raise

                if album_response["is_delete"]:
                    log.step("第%s页作品已被删除，跳过" % album_id)
                    album_id += 1
                    continue

                log.trace("第%s页作品解析的全部图片：%s" % (album_id, album_response["image_url_list"]))

                image_index = 1
                # 过滤标题中不支持的字符
                album_title = path.filter_text(album_response["album_title"])
                if album_title:
                    album_path = os.path.join(self.image_download_path, "%05d %s" % (album_id, album_title))
                else:
                    album_path = os.path.join(self.image_download_path, str(album_id))
                temp_path = album_path
                for image_url in album_response["image_url_list"]:
                    if not self.is_running():
                        tool.process_exit(0)
                    log.step("作品%s 《%s》 开始下载第%s张图片 %s" % (album_id, album_title, image_index, image_url))

                    file_type = image_url.split(".")[-1]
                    file_path = os.path.join(album_path, "%03d.%s" % (image_index, file_type))
                    save_file_return = net.save_net_file(image_url, file_path)
                    if save_file_return["status"] == 1:
                        log.step("作品%s 《%s》 第%s张图片下载成功" % (album_id, album_title, image_index))
                        image_index += 1
                    else:
                        log.error("作品%s 《%s》 第%s张图片 %s 下载失败，原因：%s" % (album_id, album_title, image_index, image_url, crawler.download_failre(save_file_return["code"])))
                # 作品内图片全部下载完毕
                temp_path = ""  # 临时目录设置清除
                self.total_image_count += image_index - 1  # 计数累加
                album_id += 1  # 设置存档记录
        except SystemExit, se:
            if se.code == 0:
                log.step("提前退出")
            else:
                log.error("异常退出")
            # 如果临时目录变量不为空，表示某个作品正在下载中，需要把下载了部分的内容给清理掉
            if temp_path:
                path.delete_dir_or_file(temp_path)
        except Exception, e:
            log.error("未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 重新保存存档文件
        tool.write_file(str(album_id), self.save_data_path, tool.WRITE_FILE_TYPE_REPLACE)
        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), self.total_image_count))


if __name__ == "__main__":
    CNU().main()
