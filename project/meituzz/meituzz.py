# -*- coding:UTF-8  -*-
"""
美图赚赚图片爬虫
http://meituzz.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import os

ERROR_PAGE_COUNT_CHECK = 50


# 获取指定页数的相册
def get_album_page(page_count):
    if page_count <= 25000:
        album_url = "http://meituzz.com/album/browse?albumID=%s" % page_count
    else:
        album_url = "http://zz.mt27z.cn/ab/brVv22?y=%sm0%s" % (hex(page_count)[2:], str(9 + page_count ** 2)[-4:])
    album_response = net.http_request(album_url)
    extra_info = {
        "is_delete": False,  # 相册是不是已被删除（或还没有内容）
        "image_url_list": None,  # 页面解析出的所有图片地址列表
        "video_url": None,  # 页面解析出的所有视频地址
        "title": "",  # 页面解析出的相册标题
        "is_error": False,  # 是不是没有任何图片或视频
    }
    if album_response.status == 200:
        # 获取相册标题
        extra_info["title"] = tool.find_sub_string(album_response.data, "<title>", "</title>").replace("\n", "")
        # 检测相册是否已被删除
        extra_info["is_delete"] = extra_info["title"] == "作品已被删除"
        if not extra_info["is_delete"]:
            key = tool.find_sub_string(album_response.data, '<input type="hidden" id="s" value="', '">')
            is_error = True
            if key:
                media_url = "http://zz.mt27z.cn/ab/bd"
                post_data = {"y": page_count, "s": key}
                media_response = net.http_request(media_url, method="POST", post_data=post_data, json_decode=True)
                if media_response.status == net.HTTP_RETURN_CODE_SUCCEED:
                    # 检测是否是图片相册
                    if robot.check_sub_key(("i",), media_response.json_data) and isinstance(media_response.json_data["i"], list):
                        is_error = False
                        if len(media_response.json_data["i"]) > 0:
                            image_url_list = []
                            for image_info in media_response.json_data["i"]:
                                if robot.check_sub_key(("url",), image_info):
                                    image_url_list.append(str(image_info["url"]))
                                else:
                                    image_url_list = []
                                    break
                            extra_info["image_url_list"] = image_url_list
                    # 检测是否是视频相册
                    if robot.check_sub_key(("v",), media_response.json_data):
                        is_error = False
                        extra_info["video_url"] = str(media_response.json_data["v"])
            extra_info["is_error"] = is_error
    album_response.extra_info = extra_info
    return album_response


class MeiTuZZ(robot.Robot):
    def __init__(self):
        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_DOWNLOAD_VIDEO: True,
            robot.SYS_NOT_CHECK_SAVE_DATA: True,
        }
        robot.Robot.__init__(self, sys_config)

        tool.print_msg("配置文件读取完成")

    def main(self):
        # 解析存档文件，获取上一次的album id
        album_id = 1
        if os.path.exists(self.save_data_path):
            save_file = open(self.save_data_path, "r")
            save_info = save_file.read()
            save_file.close()
            album_id = int(save_info.strip())

        total_image_count = 0
        total_video_count = 0
        error_count = 0
        is_over = False
        while not is_over:
            log.step("开始解析第%s页相册" % album_id)

            # 获取相册
            try:
                album_response = get_album_page(album_id)
            except SystemExit:
                log.step("提前退出")
                break

            if album_response.status == 500:
                log.step("第%s页相册内部错误，跳过" % album_id)
                album_id += 1
                continue
            elif album_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                log.error("第%s页相册访问失败，原因：%s" % (album_id, robot.get_http_request_failed_reason(album_response.status)))
                break

            if album_response.extra_info["is_delete"]:
                error_count += 1
                if error_count >= ERROR_PAGE_COUNT_CHECK:
                    log.step("连续%s页相册没有图片，退出程序" % ERROR_PAGE_COUNT_CHECK)
                    album_id -= error_count - 1
                    break
                else:
                    log.step("第%s页相册已被删除" % album_id)
                    album_id += 1
                    continue

            if album_response.extra_info["is_error"]:
                log.step("第%s页相册解析失败" % album_id)
                break

            # 错误数量重置
            error_count = 0

            if album_response.extra_info["image_url_list"] is not None:
                log.trace("第%s页相册解析的所有图片：%s" % (album_id, album_response.extra_info["image_url_list"]))
            else:
                log.trace("第%s页相册解析的视频：%s" % (album_id, album_response.extra_info["video_url"]))

            # 图片下载
            if self.is_download_image and album_response.extra_info["image_url_list"] is not None:
                if len(album_response.extra_info["image_url_list"]) == 0:
                    log.error("第%s页相册图片解析失败" % album_id)
                    break

                log.trace("第%s页解析的全部图片：%s" % (album_id, album_response.extra_info["image_url_list"]))

                image_path = os.path.join(self.image_download_path, "%04d" % album_id)
                if not tool.make_dir(image_path, 0):
                    log.error("创建图片下载目录 %s 失败" % image_path)
                    break

                image_count = 1
                for image_url in album_response.extra_info["image_url_list"]:
                    log.step("开始下载第%s页第%s张图片 %s" % (album_id, image_count, image_url))

                    image_file_path = os.path.join(image_path, "%04d.jpg" % image_count)
                    try:
                        save_file_return = net.save_net_file(image_url, image_file_path, True)
                        if save_file_return["status"] == 1:
                            log.step("第%s页第%s张图片下载成功" % (album_id, image_count))
                            image_count += 1
                        else:
                            log.error("第%s页第%s张图片 %s 下载失败，原因：%s" % (album_id, image_count, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
                    except SystemExit:
                        log.step("提前退出")
                        tool.remove_dir(image_path)
                        is_over = True
                        break

                total_image_count += image_count - 1

            # 视频下载
            if self.is_download_image and album_response.extra_info["video_url"] is not None:
                video_url = album_response.extra_info["video_url"]
                log.step("开始下载第%s页视频 %s" % (album_id, video_url))

                title = robot.filter_text(album_response.extra_info["title"])
                video_file_path = os.path.join(self.video_download_path, "%s %s.mp4" % (album_id, title))
                try:
                    save_file_return = net.save_net_file(video_url, video_file_path)
                    if save_file_return["status"] == 1:
                        log.step("第%s页视频下载成功" % album_id)
                        total_video_count += 1
                    else:
                        log.error("第%s页视频 %s 下载失败，原因：%s" % (album_id, video_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
                except SystemExit:
                    log.step("提前退出")
                    is_over = True

            if not is_over:
                album_id += 1

        # 重新保存存档文件
        save_data_dir = os.path.dirname(self.save_data_path)
        if not os.path.exists(save_data_dir):
            tool.make_dir(save_data_dir, 0)
        save_file = open(self.save_data_path, "w")
        save_file.write(str(album_id))
        save_file.close()

        log.step("全部下载完毕，耗时%s秒，共计图片%s张，视频%s个" % (self.get_run_time(), total_image_count, total_video_count))


if __name__ == "__main__":
    MeiTuZZ().main()