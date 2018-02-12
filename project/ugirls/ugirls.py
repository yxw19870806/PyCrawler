# -*- coding:UTF-8  -*-
"""
尤果图集预览图片爬虫
http://www.ugirls.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
from pyquery import PyQuery as PQ
import os
import traceback


# 从图集首页获取最新的图集id
def get_index_page():
    index_url = "http://www.ugirls.com/Content/"
    index_response = net.http_request(index_url, method="GET")
    result = {
        "max_album_id": None,  # 最新图集id
    }
    if index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(index_response.status))
    first_album_url = PQ(index_response.data).find("div.magazine_list_wrap .magazine_item").eq(0).find(".magazine_item_wrap").attr("href")
    if not first_album_url:
        raise crawler.CrawlerException("页面截取最新图集地址失败\n%s" % index_response.data)
    album_id = tool.find_sub_string(first_album_url, "/Product-", ".html")
    if not crawler.is_integer(album_id):
        raise crawler.CrawlerException("图集地址截取图集id失败\n%s" % index_response.data)
    result["max_album_id"] = int(album_id)
    return result


# 获取指定页数的图集
def get_album_page(album_id):
    album_url = "http://www.ugirls.com/Content/List/Magazine-%s.html" % album_id
    album_response = net.http_request(album_url, method="GET")
    result = {
        "image_url_list": [],  # 全部图片地址
        "is_delete": False,  # 是不是已经被删除
        "model_name": "",  # 模特名字
    }
    if album_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(album_response.status))
    if album_response.data.find("该页面不存在,或者已经被删除!") >= 0:
        result["is_delete"] = True
        return result
    # 获取模特名字
    model_name = PQ(album_response.data).find("div.ren_head div.ren_head_c a").attr("title")
    if not model_name:
        raise crawler.CrawlerException("模特信息截取模特名字失败\n%s" % album_response.data)
    result["model_name"] = model_name.encode("UTF-8").strip()
    # 获取所有图片地址
    image_list_selector = PQ(album_response.data).find("ul#myGallery li img")
    if image_list_selector.size() == 0:
        raise crawler.CrawlerException("页面匹配图片地址失败\n%s" % album_response.data)
    for image_index in range(0, image_list_selector.size()):
        image_url = image_list_selector.eq(image_index).attr("src")
        if image_url.find("_magazine_web_m.") == -1:
            raise crawler.CrawlerException("图片地址不符合规则\n%s" % image_url)
        result["image_url_list"].append(image_url.replace("_magazine_web_m.", "_magazine_web_l."))
    return result


class UGirls(crawler.Crawler):
    def __init__(self):
        sys_config = {
            crawler.SYS_DOWNLOAD_IMAGE: True,
            crawler.SYS_NOT_CHECK_SAVE_DATA: True,
        }
        crawler.Crawler.__init__(self, sys_config)

    def main(self):
        # 解析存档文件，获取上一次的图集id
        album_id = 1
        if os.path.exists(self.save_data_path):
            file_save_info = tool.read_file(self.save_data_path)
            if not crawler.is_integer(file_save_info):
                log.error("存档内数据格式不正确")
                tool.process_exit()
            album_id = int(file_save_info)
        temp_path = ""

        try:
            # 获取图集首页
            try:
                index_response = get_index_page()
            except crawler.CrawlerException, e:
                log.error("图集首页解析失败，原因：%s" % e.message)
                raise

            log.step("最新图集id：%s" % index_response["max_album_id"])

            while album_id <= index_response["max_album_id"]:
                if not self.is_running():
                    tool.process_exit(0)
                log.step("开始解析第%s页图集" % album_id)

                # 获取相册
                try:
                    album_response = get_album_page(album_id)
                except crawler.CrawlerException, e:
                    log.error("第%s页图集解析失败，原因：%s" % (album_id, e.message))
                    raise

                if album_response["is_delete"]:
                    log.step("第%s页图集已被删除，跳过" % album_id)
                    album_id += 1
                    continue

                log.trace("第%s页图集解析的全部图片：%s" % (album_id, album_response["image_url_list"]))

                image_index = 1
                temp_path = album_path = os.path.join(self.image_download_path, "%04d %s" % (album_id, album_response["model_name"]))
                for image_url in album_response["image_url_list"]:
                    if not self.is_running():
                        tool.process_exit(0)
                    log.step("开始下载第%s页图集的第%s张图片 %s" % (album_id, image_index, image_url))

                    file_type = image_url.split(".")[-1]
                    file_path = os.path.join(album_path, "%03d.%s" % (image_index, file_type))
                    save_file_return = net.save_net_file(image_url, file_path)
                    if save_file_return["status"] == 1:
                        log.step("第%s页图集的第%s张图片下载成功" % (album_id, image_index))
                        image_index += 1
                    else:
                         log.error("第%s页图集的第%s张图片 %s 下载失败，原因：%s" % (album_id, image_index, image_url, crawler.download_failre(save_file_return["code"])))
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
    UGirls().main()
