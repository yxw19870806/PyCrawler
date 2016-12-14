# -*- coding:UTF-8  -*-
"""
美图赚赚图片爬虫
http://meituzz.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, robot, tool
import json
import os
import re


ERROR_PAGE_COUNT_CHECK = 10


# 根据页面内容获取图片下载地址列表
def get_image_url_list(album_page):
    image_url_list_find = tool.find_sub_string(album_page, '<input type="hidden" id="imageList" value=', " />")
    try:
        image_url_list_find = json.loads(image_url_list_find)
    except ValueError:
        return None
    image_url_list = []
    for temp_image_list in image_url_list_find:
        image_url_list += temp_image_list
    return image_url_list


# 根据页面内容获取视频下载地址
def get_video_url(album_page):
    video_url = tool.find_sub_string(album_page, '<input type="hidden" id="VideoUrl" value="', '">')
    return "http://t.xiutuzz.com%s" % video_url


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
            album_url = "http://meituzz.com/album/browse?albumID=%s" % album_id
            try:
                album_page_return_code, album_page = tool.http_request(album_url)[:2]
            except SystemExit:
                log.step("提前退出")
                break

            if album_page_return_code == -500:
                log.error("第%s页相册内部错误" % album_id)
                album_id += 1
                continue
            elif album_page_return_code != 1:
                log.error("第%s页图片获取失败" % album_id)
                break

            if album_page.find("<title>相册已被删除</title>") >= 0:
                error_count += 1
                if error_count >= ERROR_PAGE_COUNT_CHECK:
                    log.error("连续%s页相册没有图片，退出程序" % ERROR_PAGE_COUNT_CHECK)
                    album_id -= error_count - 1
                    break
                else:
                    log.error("第%s页相册已被删除" % album_id)
                    album_id += 1
                    continue
            # 错误数量重置
            error_count = 0

            # 图片下载
            if self.is_download_image and album_page.find('<input type="hidden" id="imageList"') >= 0:
                total_photo_count = tool.find_sub_string(album_page, '<input type="hidden" id="totalPageNum" value=', " />")
                if not total_photo_count:
                    log.error("第%s页图片数量解析失败" % album_id)
                    break
                total_photo_count = int(total_photo_count)

                # 获取页面全部图片地址列表
                image_url_list = get_image_url_list(album_page)
                if image_url_list is None:
                    log.error("第%s页图片地址列表解析失败" % album_id)
                    break

                if len(image_url_list) == 0:
                    log.error("第%s页没有获取到图片" % album_id)
                    break

                is_fee = False
                if len(image_url_list) != total_photo_count:
                    album_reward_find = re.findall('<input type="hidden" id="rewardAmount" value="(\d*)">', album_page)
                    if len(album_reward_find) == 1:
                        album_reward = int(album_reward_find[0])
                        if album_reward > 0 and total_photo_count - len(image_url_list) <= 1:
                            is_fee = True
                    if not is_fee:
                        log.error("第%s页解析获取的图片数量不符" % album_id)
                        # break

                image_path = os.path.join(self.image_download_path, "%04d" % album_id)
                if not tool.make_dir(image_path, 0):
                    log.error("创建图片下载目录 %s 失败" % image_path)
                    break

                image_count = 1
                for image_url in image_url_list:
                    # 去除模糊效果
                    image_url = str(image_url).split("@")[0]
                    log.step("开始下载第%s页第%s张图片 %s" % (album_id, image_count, image_url))

                    image_file_path = os.path.join(image_path, "%04d.jpg" % image_count)
                    try:
                        if tool.save_net_file(image_url, image_file_path, True):
                            log.step("第%s页第%s张图片下载成功" % (album_id, image_count))
                            image_count += 1
                        else:
                            log.error("第%s页第%s张图片 %s 下载失败" % (album_id, image_count, image_url))
                    except SystemExit:
                        log.step("提前退出")
                        tool.remove_dir(image_path)
                        is_over = True
                        break

                total_image_count += image_count - 1

            # 视频下载
            if self.is_download_image and album_page.find('<input type="hidden" id="VideoUrl"') >= 0:
                # 获取视频下载地址
                video_url = get_video_url(album_page)
                log.step("开始下载第%s页视频 %s" % (album_id, video_url))

                video_title = robot.filter_text(tool.find_sub_string(album_page, "<title>", "</title>"))
                file_type = video_url.split(".")[-1]
                video_file_path = os.path.join(self.video_download_path, "%s %s.%s" % (album_id, video_title, file_type))
                try:
                    if tool.save_net_file(video_url, video_file_path, True):
                        log.step("第%s页视频下载成功" % album_id)
                        total_video_count += 1
                    else:
                        log.error("第%s页视频 %s 下载失败" % (album_id, video_url))
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
