# -*- coding:UTF-8  -*-
'''
Created on 2014-2-8

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

from common import log, robot, tool
from common import BeautifulSoup
import os
import time


class Fkoji(robot.Robot):

    ALL_SIGN = '_____'

    def __init__(self):
        super(Fkoji, self).__init__()

        tool.print_msg("配置文件读取完成")

    def main(self):
        start_time = time.time()

        # 图片保存目录
        log.step("创建图片根目录：" + self.image_download_path)
        if not tool.make_dir(self.image_download_path, 0):
            log.error("创建图片根目录：" + self.image_download_path + " 失败，程序结束！")
            tool.process_exit()

        # 图片下载临时目录
        if self.is_sort == 1:
            log.step("创建图片下载目录：" + self.image_temp_path)
            if not tool.make_dir(self.image_temp_path, 0):
                log.error("创建图片下载目录：" + self.image_temp_path + " 失败，程序结束！")
                tool.process_exit()

        # 设置代理
        if self.is_proxy == 1 or self.is_proxy == 2:
            tool.set_proxy(self.proxy_ip, self.proxy_port, "http")

        # 寻找fkoji.save
        account_list = {}
        if os.path.exists(self.save_data_path):
            account_list = robot.read_save_data(self.save_data_path, 0, ["", "", ""])

        # 这个key的内容为总数据
        if self.ALL_SIGN in account_list:
            image_start_index = int(account_list[self.ALL_SIGN][1])
            last_image_url = account_list[self.ALL_SIGN][2]
            account_list.pop(self.ALL_SIGN)
        else:
            last_image_url = ""
            image_start_index = 0

        page_index = 1
        image_count = 1
        new_last_image_url = ""
        image_url_list = []
        is_over = False

        if self.is_sort == 1:
            image_path = self.image_temp_path
        else:
            image_path = self.image_download_path

        # 下载
        while True:
            index_url = "http://jigadori.fkoji.com/?p=%s" % str(page_index)
            log.trace("网页地址：" + index_url)

            [index_page_return_code, index_page_response] = tool.http_request(index_url)[:2]
            if index_page_return_code != 1:
                log.error("无法访问首页地址" + index_url)
                tool.process_exit()

            index_page = BeautifulSoup.BeautifulSoup(index_page_response)
            photo_list = index_page.body.findAll("div", "photo")
            # 已经下载到最后一页
            if not photo_list:
                break
            for photo_info in photo_list:
                if isinstance(photo_info, BeautifulSoup.NavigableString):
                    continue
                tags = photo_info.findAll("span")
                # 找account_id
                for tag in tags:
                    sub_tag = tag.next.next
                    if isinstance(sub_tag, BeautifulSoup.NavigableString):
                        if sub_tag.find("@") == 0:
                            account_id = sub_tag[1:].encode("GBK")
                # 找图片
                tags = photo_info.findAll("img")
                for tag in tags:
                    tag_attr = dict(tag.attrs)
                    if tag_attr.has_key("src") and tag_attr.has_key("alt"):
                        image_url = str(tag_attr["src"]).replace(" ", "").encode("GBK")
                        if new_last_image_url == "":
                            new_last_image_url = image_url
                        # 检查是否已下载到前一次的图片
                        if last_image_url == image_url:
                            is_over = True
                            break
                        log.trace("id: " + account_id + "，地址: " + image_url)
                        if image_url in image_url_list:
                            continue
                        # 文件类型
                        file_type = image_url.split(".")[-1]
                        if file_type.find("/") != -1:
                            file_type = "jpg"
                        file_path = image_path + "\\" + str("%05d" % image_count) + "_" + str(account_id) + "." + file_type
                        log.step("开始下载第" + str(image_count) + "张图片：" + image_url)
                        if tool.save_image(image_url, file_path):
                            log.step("第" + str(image_count) + "张图片下载成功")
                            image_count += 1
                        else:
                            log.error("第" + str(image_count) + "张图片 " + image_url + ", id: " + account_id + " 下载失败")
                if is_over:
                    break
            if is_over:
                break
            page_index += 1

        log.step("下载完毕")

        # 排序复制到保存目录
        if self.is_sort == 1:
            is_check_ok = False
            while not is_check_ok:
                # 等待手动检测所有图片结束
                input_str = raw_input(tool.get_time() + " 已经下载完毕，是否下一步操作？ (Y)es or (N)o: ")
                try:
                    input_str = input_str.lower()
                    if input_str in ["y", "yes"]:
                        is_check_ok = True
                    elif input_str in ["n", "no"]:
                        tool.process_exit()
                except:
                    pass
            if not tool.make_dir(self.image_download_path + "\\all", 0):
                log.error("创建目录：" + self.image_download_path + "\\all" + " 失败，程序结束！")
                tool.process_exit()

            file_list = tool.get_dir_files_name(self.image_temp_path, "desc")
            for file_name in file_list:
                image_path = self.image_temp_path + "\\" + file_name
                file_name_list = file_name.split(".")
                file_type = file_name_list[-1]
                account_id = "_".join(".".join(file_name_list[:-1]).split("_")[1:])

                # 所有
                image_start_index += 1
                tool.copy_files(image_path, self.image_download_path + "\\all\\" + str("%05d" % image_start_index) + "_" + account_id + "." + file_type)

                # 单个
                each_account_path = self.image_download_path + "\\single\\" + account_id
                if not os.path.exists(each_account_path):
                    if not tool.make_dir(each_account_path, 0):
                        log.error("创建目录：" + each_account_path + " 失败，程序结束！")
                        tool.process_exit()
                if account_list.has_key(account_id):
                    account_list[account_id][1] = int(account_list[account_id][1]) + 1
                else:
                    account_list[account_id] = [account_id, 1]
                tool.copy_files(image_path, each_account_path + "\\" + str("%05d" % account_list[account_id][1]) + "." + file_type)

            log.step("图片从下载目录移动到保存目录成功")

            # 删除临时文件夹
            tool.remove_dir(self.image_temp_path)
            
        # 保存新的存档文件
        temp_list = [account_list[key] for key in sorted(account_list.keys())]
        # 把总数据插入列表头
        temp_list.insert(0, [self.ALL_SIGN, str(image_start_index), new_last_image_url])
        tool.write_file(tool.list_to_string(temp_list), self.save_data_path, 2)

        duration_time = int(time.time() - start_time)
        log.step("全部下载完毕，耗时" + str(duration_time) + "秒，共计图片" + str(image_count - 1) + "张")


if __name__ == "__main__":
    tool.restore_process_status()
    Fkoji().main()
