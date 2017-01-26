# -*- coding:UTF-8  -*-
"""
美图赚赚图片爬虫
http://meituzz.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, net, robot, tool
import json
import os
import re

ERROR_PAGE_COUNT_CHECK = 10


# 获取指定页数的相册
def get_album_page(page_count):
    album_url = "http://meituzz.com/album/browse?albumID=%s" % page_count
    album_page_response = net.http_request(album_url)
    extra_info = {
        "is_delete": False,  # 相册是不是已被删除（或还没有内容）
        "image_info": {},  # 图片相册信息
        "video_info": {},  # 视频相册信息
        "is_exit": False,  # 视频相册信息
    }
    if album_page_response.status == 200:
        # 检测相册是否已被删除
        extra_info["is_delete"] = album_page_response.data.find("<title>相册已被删除</title>") >= 0
        # 检测是否是图片相册
        if album_page_response.data.find('<input type="hidden" id="imageList"') >= 0:
            image_info = {
                "is_error": False,  # 获取的图片数量和图片地址数量是否一致
                "image_url_list": [],  # 页面解析出的所有图片地址列表
            }
            # 获取图片数量
            image_count_find = tool.find_sub_string(album_page_response.data, '<input type="hidden" id="totalPageNum" value=', " ")
            if image_count_find.isdigit() and int(image_count_find) > 0:
                image_count = int(image_count_find)
                # 获取图片地址列表
                image_url_list_find = tool.find_sub_string(album_page_response.data, '<input type="hidden" id="imageList" value=', " ")
                try:
                    image_url_list = json.loads(image_url_list_find)
                except ValueError:
                    image_info["is_error"] = True
                else:
                    if len(image_url_list) == 0:
                        image_info["is_error"] = True
                    elif len(image_url_list) != image_count:
                        album_reward_find = re.findall('<input type="hidden" id="rewardAmount" value="(\d*)">', album_page_response.data)
                        # 收费相册
                        if len(album_reward_find) == 1 and album_reward_find[0].isdigit() and int(album_reward_find) > 0:
                            # 图片地址数量大于获取的数量，或者获取的数量比图片地址数量多一张以上
                            if image_count < len(image_url_list) or image_count > len(image_url_list) + 1:
                                image_info["is_error"] = True
                        else:
                            # 非收费相册，两个数量不一致
                            image_info["is_error"] = True
                    else:
                        image_info["image_url_list"] = image_url_list
            else:
                image_info["is_error"] = True
            extra_info["image_info"] = image_info
        # 检测是否是视频相册
        if album_page_response.data.find('<input type="hidden" id="VideoUrl"') >= 0:
            video_info = {
                "video_url": None,  # 获取的视频地址
                "video_title": "",  # 获取的视频标题
            }
            # 获取视频下载地址
            video_url = tool.find_sub_string(album_page_response.data, '<input type="hidden" id="VideoUrl" value="', '">')
            if video_url:
                if video_url[0] == "/":
                    video_info["video_url"] = "http://t.xiutuzz.com%s" % video_url
                else:
                    video_info["video_url"] = video_url
            # 获取视频标题
            video_info["video_title"] = robot.filter_text(tool.find_sub_string(album_page_response.data, "<title>", "</title>"))
            extra_info["video_info"] = video_info
    album_page_response.extra_info = extra_info
    return album_page_response


class MeiTuZZ(robot.Robot):
    def __init__(self):
        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_DOWNLOAD_VIDEO: True,
            robot.SYS_NOT_CHECK_SAVE_DATA: True,
        }
        robot.Robot.__init__(self, sys_config, use_urllib3=True)

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
                album_page_response = get_album_page(album_id)
            except SystemExit:
                log.step("提前退出")
                break

            if album_page_response.status == 500:
                log.step("第%s页相册内部错误，跳过" % album_id)
                album_id += 1
                continue
            elif album_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                log.error("第%s页图片访问失败，原因：%s" % (album_id, robot.get_http_request_failed_reason(album_page_response.status)))
                break

            if album_page_response.extra_info["is_delete"]:
                error_count += 1
                if error_count >= ERROR_PAGE_COUNT_CHECK:
                    log.step("连续%s页相册没有图片，退出程序" % ERROR_PAGE_COUNT_CHECK)
                    album_id -= error_count - 1
                    break
                else:
                    log.step("第%s页相册已被删除" % album_id)
                    album_id += 1
                    continue
            # 错误数量重置
            error_count = 0

            # 图片下载
            if self.is_download_image and album_page_response.extra_info["image_info"]:
                if album_page_response.extra_info["image_info"]["is_error"]:
                    log.error("第%s页图片解析失败" % album_id)
                    break

                log.trace("第%s页获取的全部图片：%s" % (album_id, album_page_response.extra_info["image_info"]["image_url_list"]))

                image_path = os.path.join(self.image_download_path, "%04d" % album_id)
                if not tool.make_dir(image_path, 0):
                    log.error("创建图片下载目录 %s 失败" % image_path)
                    break

                image_count = 1
                for image_url in album_page_response.extra_info["image_info"]["image_url_list"]:
                    # 去除模糊效果
                    image_url = str(image_url).split("@")[0]
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
            if self.is_download_image and album_page_response.extra_info["video_info"]:
                if album_page_response.extra_info["video_info"]["video_url"] is None:
                    log.error("第%s页视频解析失败" % album_id)
                    break

                video_url = album_page_response.extra_info["video_info"]["video_url"]
                log.step("开始下载第%s页视频 %s" % (album_id, video_url))

                video_title = album_page_response.extra_info["video_info"]["video_title"]
                file_type = video_url.split(".")[-1]
                video_file_path = os.path.join(self.video_download_path, "%s %s.%s" % (album_id, video_title, file_type))
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
