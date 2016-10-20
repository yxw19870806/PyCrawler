# -*- coding:UTF-8  -*-
"""
fkoji图片爬虫
http://jigadori.fkoji.com
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, robot, tool
from common import BeautifulSoup
import os
import time

ALL_SIGN = "_____"


# 从图片页面中解析获取推特发布时间的时间戳
def get_tweet_created_time(photo_info):
    tweet_created_time_find = photo_info.findAll("div", "tweet-created-at")
    if len(tweet_created_time_find) == 1:
        tweet_created_time_string = tweet_created_time_find[0].text
        return int(time.mktime(time.strptime(tweet_created_time_string, "%Y-%m-%d %H:%M:%S")))
    return None


# 从图片页面中解析获取推特发布账号
def get_tweet_account_id(photo_info):
    span_tags = photo_info.findAll("span")
    for tag in span_tags:
        sub_tag = tag.next.next
        if isinstance(sub_tag, BeautifulSoup.NavigableString):
            if sub_tag.find("@") == 0:
                return sub_tag[1:].encode("GBK")
    return None


class Fkoji(robot.Robot):
    def __init__(self):
        sys_config = [
            robot.SYS_DOWNLOAD_IMAGE,
            robot.SYS_SET_PROXY,
            robot.SYS_NOT_CHECK_SAVE_DATA,
        ]
        robot.Robot.__init__(self, sys_config)

    def main(self):
        # 解析存档文件
        # 寻找fkoji.save
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "", ""])

        # 这个key的内容为总数据
        if ALL_SIGN in account_list:
            image_start_index = int(account_list[ALL_SIGN][1])
            account_list.pop(ALL_SIGN)
            save_data_image_time = 0
        else:
            image_start_index = 0
            save_data_image_time = 0

        if self.is_sort:
            image_path = self.image_temp_path
        else:
            image_path = self.image_download_path

        # 下载
        page_index = 1
        image_count = 1
        first_image_url = ""
        first_image_time = 0
        unique_list = []
        is_over = False
        while not is_over:
            index_url = "http://jigadori.fkoji.com/?p=%s" % page_index
            index_page_return_code, index_page_response = tool.http_request(index_url)[:2]
            if index_page_return_code != 1:
                log.error("无法访问首页地址 %s" % index_url)
                tool.process_exit()

            index_page = BeautifulSoup.BeautifulSoup(index_page_response)
            photo_list = index_page.body.findAll("div", "photo")
            # 已经下载到最后一页
            if not photo_list:
                break
            for photo_info in photo_list:
                if isinstance(photo_info, BeautifulSoup.NavigableString):
                    continue

                # 从图片页面中解析获取推特发布时间的时间戳
                tweet_created_time = get_tweet_created_time(photo_info)
                if tweet_created_time is None:
                    log.error("第%s张图片，解析tweet-created-at失败" % image_count)
                    continue

                # 下载完毕
                if tweet_created_time <= save_data_image_time:
                    break

                # 将第一张图片的上传时间做为新的存档记录
                if first_image_time == 0:
                    first_image_time = tweet_created_time

                # 从图片页面中解析获取推特发布账号
                account_id = get_tweet_account_id(photo_info)
                if account_id is None:
                    log.error("第%s张图片，解析tweet账号失败" % image_count)
                    continue

                # 找图片
                img_tags = photo_info.findAll("img")
                for tag in img_tags:
                    tag_attr = dict(tag.attrs)
                    if robot.check_sub_key(("src", "alt"), tag_attr):
                        image_url = str(tag_attr["src"]).replace(" ", "").encode("GBK")
                        # 新增图片导致的重复判断
                        if image_url in unique_list:
                            continue
                        else:
                            unique_list.append(image_url)
                        # 将第一张图片的地址做为新的存档记录
                        if first_image_url == "":
                            first_image_url = image_url

                        log.step("开始下载第%s张图片 %s" % (image_count, image_url))

                        file_type = image_url.split(".")[-1]
                        if file_type.find("/") != -1:
                            file_type = "jpg"
                        file_path = os.path.join(image_path, "%05d_%s.%s" % (image_count, account_id, file_type))
                        if tool.save_net_file(image_url, file_path):
                            log.step("第%s张图片下载成功" % image_count)
                            image_count += 1
                        else:
                            log.error("第%s张图片 %s，account_id：%s，下载失败" % (image_count, image_url, account_id))
                if is_over:
                    break

            if not is_over:
                page_index += 1

        log.step("下载完毕")

        # 排序复制到保存目录
        if self.is_sort:
            is_check_ok = False
            while not is_check_ok:
                # 等待手动检测所有图片结束
                input_str = raw_input(tool.get_time() + " 已经下载完毕，是否下一步操作？ (Y)es or (N)o: ")
                input_str = input_str.lower()
                if input_str in ["y", "yes"]:
                    is_check_ok = True
                elif input_str in ["n", "no"]:
                    tool.process_exit()

            all_path = os.path.join(self.image_download_path, "all")
            if not tool.make_dir(all_path, 0):
                log.error("创建目录 %s 失败" % all_path)
                tool.process_exit()

            file_list = tool.get_dir_files_name(self.image_temp_path, "desc")
            for file_name in file_list:
                image_path = os.path.join(self.image_temp_path, file_name)
                file_name_list = file_name.split(".")
                file_type = file_name_list[-1]
                account_id = "_".join(".".join(file_name_list[:-1]).split("_")[1:])

                # 所有
                image_start_index += 1
                destination_file_name = "%05d_%s.%s" % (image_start_index, account_id, file_type)
                destination_path = os.path.join(all_path, destination_file_name)
                tool.copy_files(image_path, destination_path)

                # 单个
                each_account_path = os.path.join(self.image_download_path, "single", account_id)
                if not os.path.exists(each_account_path):
                    if not tool.make_dir(each_account_path, 0):
                        log.error("创建目录 %s 失败" % each_account_path)
                        tool.process_exit()
                if account_id in account_list:
                    account_list[account_id][1] = int(account_list[account_id][1]) + 1
                else:
                    account_list[account_id] = [account_id, 1]
                destination_file_name = "%05d.%s" % (account_list[account_id][1], file_type)
                destination_path = os.path.join(each_account_path, destination_file_name)
                tool.copy_files(image_path, destination_path)

            log.step("图片从下载目录移动到保存目录成功")

            # 删除临时文件夹
            tool.remove_dir(self.image_temp_path)

        # 保存新的存档文件
        temp_list = [account_list[key] for key in sorted(account_list.keys())]
        # 把总数据插入列表头
        temp_list.insert(0, [ALL_SIGN, str(image_start_index), str(first_image_time)])
        tool.write_file(tool.list_to_string(temp_list), self.save_data_path, 2)

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), image_count - 1))


if __name__ == "__main__":
    Fkoji().main()
