# -*- coding:UTF-8  -*-
"""
美图赚赚图片爬虫
http://meituzz.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import os
import traceback
from common import *

ERROR_PAGE_COUNT_CHECK = 50


# 获取指定页数的相册
def get_album_page(page_count):
    if page_count <= 25000:
        album_url = "http://meituzz.com/album/browse"
        query_data = {"albumID": page_count}
    else:
        album_url = "http://meituzz.com/ab/brVv22"
        query_data = {"y": "%sm0%s" % (hex(page_count)[2:], str(9 + page_count ** 2)[-4:])}
    album_response = net.http_request(album_url, method="GET", fields=query_data)
    result = {
        "image_url_list": None,  # 全部图片地址
        "is_delete": False,  # 是不是相册已被删除（或还没有内容）
        "is_over": False,  # 是不是已经结束
        "album_title": "",  # 相册标题
        "video_url": None,  # 视频地址
    }
    if album_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 获取相册标题
        result["is_over"] = album_response.data.find("<p>视频正在审核中<br><b>精彩需要耐心等待</b></p>") >= 0
        if result["is_over"]:
            return result
        # 获取相册标题
        result["album_title"] = tool.find_sub_string(album_response.data, "<title>", "</title>").replace("\n", "")
        # 检测相册是否已被删除
        result["is_delete"] = result["album_title"] == "作品已被删除"
        if result["is_delete"]:
            return result
        # 截取key
        key = tool.find_sub_string(album_response.data, '<input type="hidden" id="s" value="', '">')
        if not key:
            raise crawler.CrawlerException("页面截取媒体key失败\n%s" % album_response.data)
        # 调用API，获取相册资源
        media_url = "http://meituzz.com/ab/bd"
        post_data = {"y": page_count, "s": key}
        media_response = net.http_request(media_url, method="POST", fields=post_data, json_decode=True)
        if media_response.status == net.HTTP_RETURN_CODE_SUCCEED:
            if not crawler.check_sub_key(("i",), media_response.json_data) and not crawler.check_sub_key(("v",), media_response.json_data):
                raise crawler.CrawlerException("图片相册'i'和'v'字段都不存在\n%s" % media_response.json_data)
            # 检测是否是图片相册
            if crawler.check_sub_key(("i",), media_response.json_data):
                if not isinstance(media_response.json_data["i"], list):
                    raise crawler.CrawlerException("图片相册'i'字段格式不正确\n%s" % media_response.json_data)
                result["image_url_list"] = []
                for image_info in media_response.json_data["i"]:
                    if not crawler.check_sub_key(("url",), image_info):
                        raise crawler.CrawlerException("图片相册'url'字段不存在\n%s" % media_response.json_data)
                    result["image_url_list"].append(str(image_info["url"]))
            # 检测是否是视频相册
            if crawler.check_sub_key(("v",), media_response.json_data):
                result["video_url"] = str(media_response.json_data["v"])
        else:
            raise crawler.CrawlerException("媒体" + crawler.request_failre(media_response.status))
    elif album_response.status == 500:
        result["is_delete"] = True
    else:
        raise crawler.CrawlerException(crawler.request_failre(album_response.status))
    return result


class MeiTuZZ(crawler.Crawler):
    def __init__(self):
        # 设置APP目录
        tool.PROJECT_APP_PATH = os.path.abspath(os.path.dirname(__file__))

        # 初始化参数
        sys_config = {
            crawler.SYS_DOWNLOAD_IMAGE: True,
            crawler.SYS_DOWNLOAD_VIDEO: True,
            crawler.SYS_NOT_CHECK_SAVE_DATA: True,
        }
        crawler.Crawler.__init__(self, sys_config)

    def main(self):
        # 解析存档文件，获取上一次的album id
        save_album_id = album_id = 1
        if os.path.exists(self.save_data_path):
            file_save_info = tool.read_file(self.save_data_path)
            if not crawler.is_integer(file_save_info):
                log.error("存档内数据格式不正确")
                tool.process_exit()
            save_album_id = album_id = int(file_save_info)
        temp_path_list = []

        try:
            error_album_count = 0
            while True:
                if not self.is_running():
                    tool.process_exit(0)
                log.step("开始解析第%s页相册" % album_id)

                # 获取相册
                try:
                    album_response = get_album_page(album_id)
                except crawler.CrawlerException, e:
                    log.error("第%s页相册解析失败，原因：%s" % (album_id, e.message))
                    raise

                if album_response["is_over"]:
                    break

                if album_response["is_delete"]:
                    error_album_count += 1
                    if error_album_count >= ERROR_PAGE_COUNT_CHECK:
                        log.step("连续%s页相册没有图片，退出程序" % ERROR_PAGE_COUNT_CHECK)
                        break
                    else:
                        log.step("第%s页相册已被删除" % album_id)
                        album_id += 1
                        continue

                # 成功获取到相册，错误数重置
                error_album_count = 0

                if album_response["image_url_list"] is not None:
                    log.trace("第%s页相册解析的全部图片：%s" % (album_id, album_response["image_url_list"]))
                else:
                    log.trace("第%s页相册解析的视频：%s" % (album_id, album_response["video_url"]))

                # 图片下载
                image_index = 1
                if self.is_download_image and album_response["image_url_list"] is not None:
                    image_path = os.path.join(self.image_download_path, "%06d" % album_id)
                    for image_url in album_response["image_url_list"]:
                        if not self.is_running():
                            tool.process_exit(0)
                        log.step("开始下载第%s页第%s张图片 %s" % (album_id, image_index, image_url))

                        image_file_path = os.path.join(image_path, "%04d.jpg" % image_index)
                        save_file_return = net.save_net_file(image_url, image_file_path, True)
                        if save_file_return["status"] == 1:
                            # 设置临时目录
                            temp_path_list.append(image_file_path)
                            log.step("第%s页第%s张图片下载成功" % (album_id, image_index))
                            image_index += 1
                        else:
                            log.error("第%s页第%s张图片 %s 下载失败，原因：%s" % (album_id, image_index, image_url, crawler.download_failre(save_file_return["code"])))

                # 视频下载
                video_index = 1
                if self.is_download_image and album_response["video_url"] is not None:
                    if not self.is_running():
                        tool.process_exit(0)
                    log.step("开始下载第%s页视频 %s" % (album_id, album_response["video_url"]))

                    video_file_path = os.path.join(self.video_download_path, "%06d %s.mp4" % (int(album_id), path.filter_text(album_response["album_title"])))
                    save_file_return = net.save_net_file(album_response["video_url"], video_file_path)
                    if save_file_return["status"] == 1:
                        # 设置临时目录
                        temp_path_list.append(video_file_path)
                        log.step("第%s页视频下载成功" % album_id)
                        video_index += 1
                    else:
                        log.error("第%s页视频 %s 下载失败，原因：%s" % (album_id, album_response["video_url"], crawler.download_failre(save_file_return["code"])))

                # tweet内图片和视频全部下载完毕
                temp_path_list = []  # 临时目录设置清除
                self.total_image_count += image_index - 1  # 计数累加
                self.total_video_count += video_index - 1  # 计数累加
                save_album_id = album_id = album_id + 1  # 设置存档记录
        except SystemExit, se:
            if se.code == 0:
                log.step("提前退出")
            else:
                log.error("异常退出")
            # 如果临时目录变量不为空，表示某个相册正在下载中，需要把下载了部分的内容给清理掉
            if len(temp_path_list) > 0:
                for temp_path in temp_path_list:
                    path.delete_dir_or_file(temp_path)
        except Exception, e:
            log.error("未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 重新保存存档文件
        tool.write_file(str(save_album_id), self.save_data_path, tool.WRITE_FILE_TYPE_REPLACE)
        log.step("全部下载完毕，耗时%s秒，共计图片%s张，视频%s个" % (self.get_run_time(), self.total_image_count, self.total_video_count))


if __name__ == "__main__":
    MeiTuZZ().main()
